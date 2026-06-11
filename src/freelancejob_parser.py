"""Парсинг листинга FreelanceJob.ru: HTML `/projects/` (карточки `/vacancy/{id}/`)."""

from __future__ import annotations

import logging
import os
import re
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from config import Config
from exchange_proxy import exchange_fetch_begin, exchange_fetch_end, exchange_get, proxy_log_hint
from listing import SOURCE_FREELANCEJOB, ListingProject
from radar_cycle_log import log_pipeline_line

logger = logging.getLogger(__name__)

_DEFAULT_LISTING_URL = "https://www.freelancejob.ru/projects/"
_VACANCY_ID_RE = re.compile(r"^/vacancy/(\d+)/?$")
_PAGE_PATH_RE = re.compile(r"/page-\d+/?")


class FreelancejobListingError(RuntimeError):
    """Не удалось разобрать ленту FreelanceJob.ru."""


def _listing_url() -> str:
    return (os.getenv("FREELANCEJOB_LISTING_URL", "") or _DEFAULT_LISTING_URL).strip()


def _listing_max_pages() -> int:
    raw = os.getenv("FREELANCEJOB_LISTING_MAX_PAGES", "1").strip()
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


def _vacancy_id_from_href(href: str) -> int | None:
    m = _VACANCY_ID_RE.match((href or "").strip())
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def parse_listing_html(html: str, page_url: str) -> list[ListingProject]:
    """Разбор сохранённого HTML листинга (отладка / тесты)."""
    if not html or not html.strip():
        raise FreelancejobListingError("Пустой HTML листинга FreelanceJob.ru.")
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.x17")
    if not cards:
        raise FreelancejobListingError(
            "На странице нет карточек `div.x17` — сменилась вёрстка или лента недоступна."
        )

    out: list[ListingProject] = []
    seen: set[int] = set()
    for card in cards:
        title_a = card.select_one("a.big[href]")
        if not title_a or not title_a.get("href"):
            continue
        href = str(title_a["href"]).strip()
        pid = _vacancy_id_from_href(href)
        if pid is None or pid in seen:
            continue
        seen.add(pid)

        title = title_a.get_text(strip=True)
        if not title:
            continue

        desc_divs = [
            d
            for d in card.find_all("div", recursive=False)
            if d != title_a.parent and not d.get("class")
        ]
        listing_snippet = ""
        if desc_divs:
            listing_snippet = desc_divs[0].get_text(" ", strip=True)

        budget_el = card.select_one("div.x18")
        budget_text = budget_el.get_text(" ", strip=True) if budget_el else ""

        published_at = ""
        date_el = card.select_one("div.x20")
        if date_el:
            raw = date_el.get_text(" ", strip=True)
            if "Проект добавлен:" in raw:
                published_at = raw.split("Проект добавлен:", 1)[-1].strip().split("—")[0].strip()
            else:
                published_at = raw[:80]

        full_url = urljoin(page_url, href)
        out.append(
            ListingProject(
                project_id=pid,
                title=title,
                budget_text=budget_text,
                url=full_url,
                published_at=published_at,
                listing_snippet=listing_snippet or title,
                source=SOURCE_FREELANCEJOB,
            )
        )

    if not out:
        raise FreelancejobListingError("Карточки `div.x17` без id — сменилась вёрстка.")
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
    hint = proxy_log_hint("freelancejob")
    try:
        resp = exchange_get("freelancejob", url, headers=headers, timeout_sec=timeout_sec)
    except requests.RequestException as exc:
        msg = f"Сетевой сбой при запросе ленты (стр. {page}, {hint}): {exc}"
        if page <= 1:
            raise FreelancejobListingError(msg) from exc
        logger.warning("freelancejob_listing: %s — partial listing", msg)
        return None

    if resp.status_code != 200:
        msg = f"HTTP {resp.status_code} для ленты ({url}, {hint})"
        if page <= 1:
            raise FreelancejobListingError(msg)
        logger.warning("freelancejob_listing: %s — stop pagination", msg)
        return None

    encoding = resp.encoding or "utf-8"
    return resp.content.decode(encoding, errors="replace")


def _parse_freelancejob_detail_html(html: str, *, fallback_snippet: str = "") -> str:
    soup = BeautifulSoup(html, "html.parser")
    for sel in ("div.x17", ".vacancy-description", ".project-description", "article"):
        nodes = soup.select(sel) if sel != "div.x17" else [soup.select_one(sel)]
        for node in nodes:
            if not node:
                continue
            text = node.get_text(" ", strip=True)
            if len(text) > len((fallback_snippet or "").strip()):
                return text
    blocks: list[str] = []
    for node in soup.select("div.x17 div, .vacancy p"):
        t = node.get_text(" ", strip=True)
        if len(t) > 60:
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
        resp = exchange_get("freelancejob", url, headers=headers, timeout_sec=timeout_sec)
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
    text = _parse_freelancejob_detail_html(html, fallback_snippet=fallback_snippet)
    detail_ok = bool(text and text != (fallback_snippet or "").strip())
    return text, html, detail_ok


_FREELANCEJOB_GONE_MARKERS = (
    "проект закрыт",
    "заказ закрыт",
    "вакансия закрыта",
    "исполнитель выбран",
    "исполнитель уже выбран",
    "исполнитель найден",
    "страница не найдена",
    "проект не найден",
    "закрыт для откликов",
    "отклики не принимаются",
)

_FREELANCEJOB_ID_RE = re.compile(r"/vacancy/(\d+)", re.I)


def _freelancejob_redirected_away(original: str, final: str) -> bool:
    orig = (original or "").strip()
    fin = final.strip() if isinstance(final, str) else ""
    if not orig or not fin or orig.casefold() == fin.casefold():
        return False
    m = _FREELANCEJOB_ID_RE.search(orig)
    if not m:
        return False
    vid = m.group(1)
    return f"/vacancy/{vid}" not in fin.casefold()


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
        resp = exchange_get("freelancejob", url, headers=headers, timeout_sec=timeout_sec)
    except requests.RequestException:
        return None

    if resp.status_code == 404:
        return True
    if resp.status_code != 200:
        return None

    raw_final = getattr(resp, "url", None)
    final_url = raw_final.strip() if isinstance(raw_final, str) and raw_final.strip() else url
    if _freelancejob_redirected_away(url, final_url):
        return True

    encoding = resp.encoding or "utf-8"
    html = resp.content.decode(encoding, errors="replace").casefold()
    if any(m in html for m in _FREELANCEJOB_GONE_MARKERS):
        return True
    if "vacancy-description" in html or 'class="x17"' in html or "div.x17" in html:
        return False
    if "/vacancy/" in html and "big" in html:
        return False
    return None


def fetch_listing_projects(
    cfg: Config, *, timeout_sec: float = 30.0
) -> list[ListingProject]:
    """GET листинга FreelanceJob (до FREELANCEJOB_LISTING_MAX_PAGES страниц)."""
    base_url = _listing_url()
    merged: list[ListingProject] = []
    seen: set[int] = set()
    max_pages = _listing_max_pages()

    exchange_fetch_begin("freelancejob")
    log_pipeline_line(
        cfg.radar_log_path, f"fetch:freelancejob proxy={proxy_log_hint('freelancejob')}"
    )
    try:
        for page in range(1, max_pages + 1):
            page_url = _listing_page_url(base_url, page)
            html = _fetch_listing_html(page_url, cfg, timeout_sec=timeout_sec, page=page)
            if html is None:
                break
            batch = parse_listing_html(html, page_url)
            if not batch and page == 1:
                raise FreelancejobListingError(
                    "Пустой разбор первой страницы FreelanceJob.ru."
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
        exchange_fetch_end("freelancejob")
