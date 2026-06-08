"""Парсинг листинга проектов FL.ru: 2–3 страницы ленты за цикл."""

from __future__ import annotations

import logging
import os
import re
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from config import Config
from exchange_browser_fetch import fetch_listing_html_browser, listing_browser_enabled
from exchange_proxy import exchange_fetch_begin, exchange_fetch_end, exchange_get, proxy_log_hint
from html_fetch import HtmlFetchError
from ingest_published_at import parse_fl_published_at
from lead_category import category_from_fl_listing_url
from listing import SOURCE_FL, ListingProject
from listing_fresh import trim_listing_at_known
from radar_cycle_log import log_pipeline_line, stash_listing_metrics

logger = logging.getLogger(__name__)

# Сколько страниц ленты запрашивать за один цикл (см. docs/SOURCES.md).
def _fl_listing_max_pages() -> int:
    raw = os.environ.get("FL_LISTING_MAX_PAGES", "1").strip()
    try:
        n = int(raw)
    except ValueError:
        n = 1
    return max(1, min(5, n))

_PAGE_PATH_RE = re.compile(r"/page-\d+/?")


class FlListingError(RuntimeError):
    """Не удалось разобрать ленту (пустой ответ, смена вёрстки, блокировка бота)."""


def _fl_listing_page_url(base_url: str, page: int) -> str:
    """Страница 1 — URL из конфига; далее `/projects/.../page-N/` + те же query."""
    if page <= 1:
        return base_url
    parsed = urlparse(base_url)
    path = _PAGE_PATH_RE.sub("", parsed.path or "/")
    path = path.rstrip("/") + f"/page-{page}/"
    return urlunparse(
        (parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment)
    )


def _parse_items(html: str, page_url: str) -> list[ListingProject]:
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".b-page__lenta_item")
    out: list[ListingProject] = []
    seen: set[int] = set()

    for node in items:
        link = node.select_one(".b-post__title a[href*='/projects/']")
        if not link or not link.get("href"):
            continue
        href = str(link["href"]).strip()
        m = re.search(r"/projects/(\d+)/", href)
        if not m:
            continue
        pid = int(m.group(1))
        if pid in seen:
            continue
        seen.add(pid)

        title = link.get_text(strip=True)
        price_el = node.select_one(".b-post__price")
        budget_text = price_el.get_text(strip=True) if price_el else ""

        full_url = urljoin(page_url, href)

        published_at = ""
        for sp in node.select("span.text-gray-opacity-4"):
            t = sp.get_text(strip=True)
            if t:
                published_at = parse_fl_published_at(t)
                break
        if not published_at:
            time_el = node.select_one("time[datetime]")
            if time_el and time_el.get("datetime"):
                published_at = parse_fl_published_at(str(time_el["datetime"]))

        body_el = node.select_one(".b-post__body .b-post__txt") or node.select_one(
            ".b-post__body"
        )
        listing_snippet = body_el.get_text(strip=True) if body_el else ""

        out.append(
            ListingProject(
                project_id=pid,
                title=title,
                budget_text=budget_text,
                url=full_url,
                published_at=published_at,
                listing_snippet=listing_snippet,
                source=SOURCE_FL,
            )
        )

    return out


def _guess_blocked_or_changed(html: str) -> str | None:
    low = html.lower()
    if "cloudflare" in low and "challenge" in low:
        return "challenge (Cloudflare и т.п.)"
    if "проверьте, что вы не робот" in low:
        return "антибот («не робот»)"
    return None


def parse_listing_html(html: str, page_url: str) -> list[ListingProject]:
    """Разбор сохранённого HTML листинга (удобно для отладки и тестов)."""
    if not html or not html.strip():
        raise FlListingError("Пустой HTML листинга.")
    projects = _parse_items(html, page_url)
    if not projects:
        hint = _guess_blocked_or_changed(html)
        extra = f" Дополнительно: похоже на {hint}." if hint else ""
        raise FlListingError(
            "На странице нет карточек `.b-page__lenta_item` — сменилась вёрстка или лента недоступна."
            f"{extra} См. docs/SOURCES.md / docs/STATUS.md (Playwright)."
        )
    return projects


def _fetch_listing_html_requests(
    url: str,
    cfg: Config,
    *,
    timeout_sec: float,
    page: int,
) -> str | None:
    headers = {"User-Agent": cfg.http_user_agent}
    hint = proxy_log_hint("fl")
    try:
        resp = exchange_get("fl", url, headers=headers, timeout_sec=timeout_sec)
    except requests.RequestException as exc:
        msg = f"Сетевой сбой при запросе ленты (стр. {page}, {hint}): {exc}"
        if page <= 1:
            raise FlListingError(msg) from exc
        logger.warning("fl_listing: %s — partial listing (%s)", msg, hint)
        return None

    if resp.status_code != 200:
        msg = f"HTTP {resp.status_code} для ленты ({url}, {hint})"
        if page <= 1:
            raise FlListingError(msg)
        logger.warning("fl_listing: %s — stop pagination", msg)
        return None

    encoding = resp.encoding or "utf-8"
    return resp.content.decode(encoding, errors="replace")


def _fetch_listing_html(
    url: str,
    cfg: Config,
    *,
    timeout_sec: float,
    page: int,
) -> str | None:
    hint = proxy_log_hint("fl")
    if listing_browser_enabled():
        try:
            return fetch_listing_html_browser(
                "fl",
                url,
                user_agent=cfg.http_user_agent,
                timeout_sec=timeout_sec,
            )
        except HtmlFetchError as exc:
            logger.warning(
                "fl_listing: Playwright failed (%s) — httpx fallback (%s)",
                exc,
                hint,
            )
    return _fetch_listing_html_requests(
        url, cfg, timeout_sec=timeout_sec, page=page
    )


def fetch_listing_projects(
    cfg: Config,
    *,
    timeout_sec: float = 30.0,
    storage: object | None = None,
) -> list[ListingProject]:
    """GET до `FL_LISTING_MAX_PAGES` страниц `cfg.fl_projects_url`, дедуп id внутри цикла.

    Без прокси: домашний IP, не TG_PROXY_URL и не системные HTTP_PROXY из ОС.
    O134/O139: `storage` → fresh-only (filter unseen; pinned known do not stop scan).
    """
    merged: list[ListingProject] = []
    seen: set[int] = set()

    max_pages = _fl_listing_max_pages()
    exchange_fetch_begin("fl")
    log_pipeline_line(cfg.radar_log_path, f"fetch:fl proxy={proxy_log_hint('fl')}")
    try:
        projects = _fetch_listing_pages(
            cfg, timeout_sec, max_pages, merged, seen, storage=storage
        )
        parsed_cards = len(projects)
        trimmed = trim_listing_at_known(projects, storage, SOURCE_FL)  # type: ignore[arg-type]
        fresh = len(trimmed)
        log_pipeline_line(
            cfg.radar_log_path,
            f"listing:fl parsed={parsed_cards} fresh={fresh}",
        )
        stash_listing_metrics("fl", parsed_cards, fresh)
        return trimmed
    finally:
        exchange_fetch_end("fl")


def _fetch_listing_pages(
    cfg: Config,
    timeout_sec: float,
    max_pages: int,
    merged: list[ListingProject],
    seen: set[int],
    *,
    storage: object | None = None,
) -> list[ListingProject]:
    for page in range(1, max_pages + 1):
        page_url = _fl_listing_page_url(cfg.fl_projects_url, page)
        html = _fetch_listing_html(page_url, cfg, timeout_sec=timeout_sec, page=page)
        if html is None:
            break
        batch = _parse_items(html, page_url)

        if not batch:
            if page == 1:
                hint = _guess_blocked_or_changed(html)
                extra = f" Дополнительно: похоже на {hint}." if hint else ""
                raise FlListingError(
                    "На странице нет карточек `.b-page__lenta_item` — сменилась вёрстка или лента недоступна."
                    f"{extra} См. docs/SOURCES.md / docs/STATUS.md (Playwright)."
                )
            break

        for project in batch:
            if project.project_id in seen:
                continue
            seen.add(project.project_id)
            merged.append(project)

    feed_cat = category_from_fl_listing_url(cfg.fl_projects_url) or ""
    if not feed_cat:
        return merged
    return [
        ListingProject(
            project_id=p.project_id,
            title=p.title,
            budget_text=p.budget_text,
            url=p.url,
            published_at=p.published_at,
            listing_snippet=p.listing_snippet,
            source=p.source,
            listing_category=p.listing_category or feed_cat,
            chat_invite_url=p.chat_invite_url,
            chat_title=p.chat_title,
        )
        for p in merged
    ]


def _parse_fl_detail_html(html: str, *, fallback_snippet: str = "") -> str:
    soup = BeautifulSoup(html, "html.parser")
    desc_el = soup.select_one(".fl-project-content__description-text")
    if desc_el:
        text = desc_el.get_text(" ", strip=True)
        if text:
            return text
    blocks: list[str] = []
    for sel in (".fl-project-content .b-layout__txt", ".b-layout__txt"):
        for node in soup.select(sel):
            t = node.get_text(" ", strip=True)
            if len(t) > 40:
                blocks.append(t)
    if blocks:
        return max(blocks, key=len)
    return fallback_snippet


def fetch_project_page_html(
    project_url: str,
    cfg: Config,
    *,
    timeout_sec: float = 30.0,
) -> tuple[str, bool]:
    """GET страницы проекта FL → HTML. (html, ok)."""
    url = (project_url or "").strip()
    if not url:
        return "", False
    headers = {"User-Agent": cfg.http_user_agent}
    try:
        resp = exchange_get("fl", url, headers=headers, timeout_sec=timeout_sec)
    except requests.RequestException:
        return "", False
    if resp.status_code != 200:
        return "", False
    encoding = resp.encoding or "utf-8"
    return resp.content.decode(encoding, errors="replace"), True


def fetch_project_detail(
    project_url: str,
    cfg: Config,
    *,
    fallback_snippet: str = "",
    timeout_sec: float = 30.0,
) -> tuple[str, str, bool]:
    """
    GET страницы проекта FL → (description, html, detail_ok).
    При ошибке — fallback_snippet, "", detail_ok=False.
    """
    html, ok = fetch_project_page_html(project_url, cfg, timeout_sec=timeout_sec)
    if not ok:
        return fallback_snippet, "", False
    text = _parse_fl_detail_html(html, fallback_snippet=fallback_snippet)
    detail_ok = bool(text and text != (fallback_snippet or "").strip())
    return text, html, detail_ok


def fetch_project_description(
    project_url: str,
    cfg: Config,
    *,
    fallback_snippet: str = "",
    timeout_sec: float = 30.0,
) -> tuple[str, bool]:
    """
    GET страницы проекта FL → полный текст ТЗ.
    Возвращает (description, detail_ok). При ошибке — fallback_snippet, detail_ok=False.
    """
    text, _, ok = fetch_project_detail(
        project_url,
        cfg,
        fallback_snippet=fallback_snippet,
        timeout_sec=timeout_sec,
    )
    return text, ok


_FL_GONE_MARKERS = (
    "проект закрыт",
    "заказ закрыт",
    "исполнитель уже выбран",
    "исполнитель найден",
    "страница не найдена",
    "проект не найден",
    "в архиве",
    "закрыт для откликов",
    "отклики не принимаются",
    "прием откликов закрыт",
    "приём откликов закрыт",
)

_FL_PROJECT_ID_RE = re.compile(r"/projects/(\d+)", re.I)


def _fl_redirected_away(original: str, final: str) -> bool:
    orig = (original or "").strip()
    fin = final.strip() if isinstance(final, str) else ""
    if not orig or not fin or orig.casefold() == fin.casefold():
        return False
    m = _FL_PROJECT_ID_RE.search(orig)
    if not m:
        return False
    pid = m.group(1)
    return f"/projects/{pid}" not in fin.casefold()


def check_project_page_gone(
    project_url: str,
    cfg: Config,
    *,
    timeout_sec: float = 20.0,
) -> bool | None:
    """O65: True — заказ снят/404; False — жив; None — не удалось проверить."""
    url = (project_url or "").strip()
    if not url:
        return None
    headers = {"User-Agent": cfg.http_user_agent}
    try:
        resp = exchange_get("fl", url, headers=headers, timeout_sec=timeout_sec)
    except requests.RequestException:
        return None

    if resp.status_code == 404:
        return True
    if resp.status_code != 200:
        return None

    raw_final = getattr(resp, "url", None)
    final_url = raw_final.strip() if isinstance(raw_final, str) and raw_final.strip() else url
    if _fl_redirected_away(url, final_url):
        return True

    encoding = resp.encoding or "utf-8"
    html = resp.content.decode(encoding, errors="replace").casefold()
    if any(m in html for m in _FL_GONE_MARKERS):
        return True
    if ".fl-project-content__description-text" in html or "fl-project-content" in html:
        return False
    return None
