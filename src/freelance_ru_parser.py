"""Парсинг листинга Freelance.ru: HTML `/project/search`."""

from __future__ import annotations

import logging
import os
import re
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from config import Config
from exchange_proxy import exchange_fetch_begin, exchange_fetch_end, exchange_get, proxy_log_hint
from listing import SOURCE_FREELANCE_RU, ListingProject
from radar_cycle_log import log_pipeline_line

logger = logging.getLogger(__name__)

_DEFAULT_LISTING_URL = "https://freelance.ru/project/search"
_PROJECT_ID_RE = re.compile(r"-(\d+)\.html(?:\?|$)")
_TASK_VIEW_RE = re.compile(r"/task/view/(\d+)(?:\?|$|/)")
_PAGE_PATH_RE = re.compile(r"/page-\d+/?")


class FreelanceRuListingError(RuntimeError):
    """Не удалось разобрать ленту Freelance.ru."""


def _listing_url() -> str:
    return (os.getenv("FREELANCE_RU_LISTING_URL", "") or _DEFAULT_LISTING_URL).strip()


def _listing_max_pages() -> int:
    raw = os.getenv("FREELANCE_RU_LISTING_MAX_PAGES", "1").strip()
    try:
        n = int(raw)
    except ValueError:
        n = 1
    return max(1, min(3, n))


def _listing_page_url(base_url: str, page: int) -> str:
    if page <= 1:
        return base_url
    parsed = urlparse(base_url)
    path = _PAGE_PATH_RE.sub("", parsed.path or "/")
    path = path.rstrip("/") + f"/page-{page}/"
    return urlunparse(
        (parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment)
    )


def _project_id_from_href(href: str) -> int | None:
    m = _PROJECT_ID_RE.search(href or "")
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    m = _TASK_VIEW_RE.search(href or "")
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def _parse_task_cards(nodes, page_url: str) -> list[ListingProject]:
    """Новая вёрстка freelance.ru (2026): `article.task-card`, URL `/task/view/{id}`."""
    out: list[ListingProject] = []
    seen: set[int] = set()
    for node in nodes:
        title_a = node.select_one(".task-card__title-link[href], h2 a[href], a[href*='/task/view/']")
        if not title_a or not title_a.get("href"):
            continue
        href = str(title_a["href"]).strip()
        pid = _project_id_from_href(href)
        if pid is None or pid in seen:
            continue
        seen.add(pid)

        title = title_a.get_text(strip=True)
        if not title:
            continue

        desc_el = node.select_one(".task-card__desc")
        listing_snippet = desc_el.get_text(" ", strip=True) if desc_el else ""

        budget_el = node.select_one(".task-card__budget")
        budget_text = budget_el.get_text(" ", strip=True) if budget_el else ""

        published_at = ""
        for foot in node.select(".task-card__foot-item"):
            part = foot.get_text(strip=True)
            low = part.casefold()
            if any(
                x in low
                for x in ("назад", "мин", "час", "день", "нед", "мес", "сегодня", "вчера")
            ):
                published_at = part
                break

        full_url = urljoin(page_url, href)
        out.append(
            ListingProject(
                project_id=pid,
                title=title,
                budget_text=budget_text,
                url=full_url,
                published_at=published_at,
                listing_snippet=listing_snippet or title,
                source=SOURCE_FREELANCE_RU,
            )
        )
    return out


def _parse_project_cards(nodes, page_url: str) -> list[ListingProject]:
    """Старая вёрстка: `.project`, URL `/projects/...-{id}.html`."""
    out: list[ListingProject] = []
    seen: set[int] = set()
    for node in nodes:
        title_a = node.select_one("h2.title a[href]")
        if not title_a or not title_a.get("href"):
            continue
        href = str(title_a["href"]).strip()
        pid = _project_id_from_href(href)
        if pid is None or pid in seen:
            continue
        seen.add(pid)

        title = title_a.get_text(strip=True)
        if not title:
            continue

        desc_a = node.select_one("a.description")
        listing_snippet = desc_a.get_text(" ", strip=True) if desc_a else ""

        cost_el = node.select_one(".cost")
        budget_text = cost_el.get_text(strip=True) if cost_el else ""
        if not budget_text:
            side = node.select_one(".col-md-3")
            if side:
                budget_text = side.get_text(" ", strip=True)

        full_url = urljoin(page_url, href)

        published_at = ""
        side_text = node.select_one(".col-md-3")
        if side_text:
            parts = [p.strip() for p in side_text.get_text("|", strip=True).split("|") if p.strip()]
            for part in parts:
                low = part.casefold()
                if "договор" in low or "₽" in part or "руб" in low:
                    continue
                if any(x in low for x in ("назад", "мин", "час", "день", "нед", "мес", "сегодня", "вчера")):
                    published_at = part
                    break

        out.append(
            ListingProject(
                project_id=pid,
                title=title,
                budget_text=budget_text,
                url=full_url,
                published_at=published_at,
                listing_snippet=listing_snippet or title,
                source=SOURCE_FREELANCE_RU,
            )
        )
    return out


def parse_listing_html(html: str, page_url: str) -> list[ListingProject]:
    """Разбор сохранённого HTML листинга (отладка / тесты)."""
    if not html or not html.strip():
        raise FreelanceRuListingError("Пустой HTML листинга Freelance.ru.")
    soup = BeautifulSoup(html, "html.parser")
    nodes = soup.select(".project")
    if nodes:
        out = _parse_project_cards(nodes, page_url)
    else:
        task_nodes = soup.select("article.task-card, .task-card")
        if not task_nodes:
            raise FreelanceRuListingError(
                "На странице нет карточек `.project` / `.task-card` — сменилась вёрстка."
            )
        out = _parse_task_cards(task_nodes, page_url)

    if not out:
        raise FreelanceRuListingError("Карточки без id — сменилась вёрстка.")
    return out


def _fetch_listing_html(
    url: str,
    cfg: Config,
    *,
    timeout_sec: float,
    page: int,
) -> str | None:
    headers = {
        "User-Agent": cfg.http_user_agent,
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }
    hint = proxy_log_hint("freelance_ru")
    try:
        resp = exchange_get("freelance_ru", url, headers=headers, timeout_sec=timeout_sec)
    except requests.RequestException as exc:
        msg = f"Сетевой сбой при запросе ленты (стр. {page}, {hint}): {exc}"
        if page <= 1:
            raise FreelanceRuListingError(msg) from exc
        logger.warning("freelance_ru_listing: %s — partial listing", msg)
        return None

    if resp.status_code != 200:
        msg = f"HTTP {resp.status_code} для ленты ({url}, {hint})"
        if page <= 1:
            raise FreelanceRuListingError(msg)
        logger.warning("freelance_ru_listing: %s — stop pagination", msg)
        return None

    encoding = resp.encoding or "utf-8"
    return resp.content.decode(encoding, errors="replace")


def _parse_freelance_ru_detail_html(html: str, *, fallback_snippet: str = "") -> str:
    soup = BeautifulSoup(html, "html.parser")
    for sel in (
        ".task-view__description",
        ".task-view__text",
        ".task-card__desc",
        ".project-description",
        ".b-layout__txt",
        "article.task-view",
    ):
        node = soup.select_one(sel)
        if node:
            text = node.get_text(" ", strip=True)
            if len(text) > len((fallback_snippet or "").strip()):
                return text
    blocks: list[str] = []
    for node in soup.select(".b-layout__txt, .task-view p, article p"):
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
    url = (project_url or "").strip()
    if not url:
        return "", False
    headers = {
        "User-Agent": cfg.http_user_agent,
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }
    try:
        resp = exchange_get("freelance_ru", url, headers=headers, timeout_sec=timeout_sec)
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
    html, ok = fetch_project_page_html(project_url, cfg, timeout_sec=timeout_sec)
    if not ok:
        return fallback_snippet, "", False
    text = _parse_freelance_ru_detail_html(html, fallback_snippet=fallback_snippet)
    detail_ok = bool(text and text != (fallback_snippet or "").strip())
    return text, html, detail_ok


_FREELANCE_RU_GONE_MARKERS = (
    "проект закрыт",
    "задание закрыто",
    "заказ закрыт",
    "исполнитель выбран",
    "исполнитель уже выбран",
    "исполнитель найден",
    "страница не найдена",
    "проект не найден",
    "закрыт для откликов",
    "отклики не принимаются",
    "прием откликов закрыт",
    "приём откликов закрыт",
)

_FREELANCE_RU_ID_RE = re.compile(r"(?:/task/view/(\d+)|-(\d+)\.html)", re.I)


def _freelance_ru_project_id(url: str) -> str | None:
    m = _FREELANCE_RU_ID_RE.search(url or "")
    if not m:
        return None
    return m.group(1) or m.group(2)


def _freelance_ru_redirected_away(original: str, final: str) -> bool:
    orig = (original or "").strip()
    fin = final.strip() if isinstance(final, str) else ""
    if not orig or not fin or orig.casefold() == fin.casefold():
        return False
    pid = _freelance_ru_project_id(orig)
    if not pid:
        return False
    low = fin.casefold()
    return f"/task/view/{pid}" not in low and f"-{pid}.html" not in low


def check_project_page_gone(
    project_url: str,
    cfg: Config,
    *,
    timeout_sec: float = 20.0,
) -> bool | None:
    """O180: True — заказ снят/404; False — жив; None — не удалось проверить."""
    url = (project_url or "").strip()
    if not url:
        return None
    headers = {
        "User-Agent": cfg.http_user_agent,
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }
    try:
        resp = exchange_get("freelance_ru", url, headers=headers, timeout_sec=timeout_sec)
    except requests.RequestException:
        return None

    if resp.status_code == 404:
        return True
    if resp.status_code != 200:
        return None

    raw_final = getattr(resp, "url", None)
    final_url = raw_final.strip() if isinstance(raw_final, str) and raw_final.strip() else url
    if _freelance_ru_redirected_away(url, final_url):
        return True

    encoding = resp.encoding or "utf-8"
    html = resp.content.decode(encoding, errors="replace").casefold()
    if any(m in html for m in _FREELANCE_RU_GONE_MARKERS):
        return True
    if (
        "task-view__description" in html
        or "article.task-view" in html
        or "task-view__text" in html
        or "task-card__desc" in html
    ):
        return False
    return None


def fetch_listing_projects(
    cfg: Config, *, timeout_sec: float = 30.0
) -> list[ListingProject]:
    """GET листинга Freelance.ru (до FREELANCE_RU_LISTING_MAX_PAGES страниц)."""
    base_url = _listing_url()
    merged: list[ListingProject] = []
    seen: set[int] = set()
    max_pages = _listing_max_pages()

    exchange_fetch_begin("freelance_ru")
    log_pipeline_line(
        cfg.radar_log_path, f"fetch:freelance_ru proxy={proxy_log_hint('freelance_ru')}"
    )
    try:
        for page in range(1, max_pages + 1):
            page_url = _listing_page_url(base_url, page)
            html = _fetch_listing_html(page_url, cfg, timeout_sec=timeout_sec, page=page)
            if html is None:
                break
            batch = parse_listing_html(html, page_url)
            if not batch and page == 1:
                raise FreelanceRuListingError(
                    "Пустой разбор первой страницы Freelance.ru."
                )
            if not batch:
                break
            for project in batch:
                if project.project_id in seen:
                    continue
                seen.add(project.project_id)
                merged.append(project)
        return merged
    finally:
        exchange_fetch_end("freelance_ru")
