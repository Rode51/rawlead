"""Парсинг листинга YouDo: SSR Next.js `/tasks-all-opened-all`."""

from __future__ import annotations

import logging
import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from config import Config
from exchange_browser_fetch import (
    fetch_listing_html_browser_slots,
    listing_browser_enabled,
)
from exchange_proxy import (
    exchange_fetch_begin,
    exchange_fetch_end,
    exchange_get,
    proxy_log_hint,
)
from html_fetch import HtmlFetchError, fetch_html_playwright
from listing import SOURCE_YOUDO, ListingProject
from radar_cycle_log import log_pipeline_line

logger = logging.getLogger(__name__)

_DEFAULT_LISTING_URL = "https://youdo.com/tasks-all-opened-all"
_TASK_ID_RE = re.compile(r"/t(\d+)")
_ANTIBOT_MARKERS = ("noscript", "exhkqyad", "just a moment", "checking your browser")


class YoudoListingError(RuntimeError):
    """Не удалось разобрать ленту YouDo."""


def _listing_url() -> str:
    return (os.getenv("YOUDO_LISTING_URL", "") or _DEFAULT_LISTING_URL).strip()


def _looks_like_antibot(html: str) -> bool:
    if not html or not html.strip():
        return True
    low = html.casefold()
    # Живая лента SSR — не антибот (на нормальной странице тоже есть <noscript>)
    if _TASK_ID_RE.search(html) or (
        'data-id' in low and 'href="/t' in low.replace("'", '"')
    ):
        return False
    if any(m in low for m in ("exhkqyad", "just a moment", "checking your browser")):
        return True
    if "403 forbidden" in low[:2500] and len(html.strip()) < 5000:
        return True
    if len(html.strip()) < 4000 and not _TASK_ID_RE.search(html):
        return True
    return False


def _task_id_from_link(link, href: str) -> int | None:
    data_id = getattr(link, "get", lambda _k, _d=None: None)("data-id")
    if data_id:
        try:
            return int(str(data_id).strip())
        except ValueError:
            pass
    m = _TASK_ID_RE.search(href or "")
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def _canonical_task_url(page_url: str, task_id: int) -> str:
    parsed = urlparse(page_url)
    host = parsed.netloc or "youdo.com"
    scheme = parsed.scheme or "https"
    return f"{scheme}://{host}/t{task_id}"


def _save_listing_html_debug(html: str, *, tag: str = "youdo") -> str:
    root = Path(__file__).resolve().parent.parent / "data" / "debug_listings"
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{tag}_{int(time.time())}.html"
    path.write_text(html[:500_000], encoding="utf-8", errors="replace")
    return str(path)


def parse_listing_html(html: str, page_url: str) -> list[ListingProject]:
    """Разбор сохранённого HTML листинга (отладка / тесты)."""
    if not html or not html.strip():
        raise YoudoListingError("Пустой HTML листинга YouDo.")
    if _looks_like_antibot(html):
        raise YoudoListingError(
            "Ответ похож на антибот — нужен YOUDO_PROXY_URLS или Playwright."
        )

    soup = BeautifulSoup(html, "html.parser")
    title_links = soup.select('a[data-id][href*="/t"]')
    if not title_links:
        title_links = [
            a
            for a in soup.find_all("a", href=True)
            if _TASK_ID_RE.search(str(a["href"]))
        ]

    out: list[ListingProject] = []
    seen: set[int] = set()

    for link in title_links:
        href = str(link.get("href") or "").strip()
        pid = _task_id_from_link(link, href)
        if pid is None or pid in seen:
            continue
        seen.add(pid)

        item = link.find_parent("li") or link.find_parent("div")
        title = link.get_text(" ", strip=True)
        if not title and item:
            title_el = item.select_one('[class*="TasksList_title"]')
            title = title_el.get_text(" ", strip=True) if title_el else ""
        if not title:
            continue

        listing_snippet = ""
        budget_text = ""
        published_at = ""
        if item:
            content_el = item.select_one('[class*="TasksList_contentBlock"]')
            if content_el:
                listing_snippet = content_el.get_text(" ", strip=True)
            price_el = item.select_one('[class*="TasksList_price"]')
            if price_el:
                budget_text = price_el.get_text(" ", strip=True)
            date_el = item.select_one('[class*="TasksList_date"]')
            if date_el:
                published_at = date_el.get_text(" ", strip=True)

        out.append(
            ListingProject(
                project_id=pid,
                title=title,
                budget_text=budget_text,
                url=_canonical_task_url(page_url, pid),
                published_at=published_at,
                listing_snippet=listing_snippet or title,
                source=SOURCE_YOUDO,
            )
        )

    if not out:
        saved = _save_listing_html_debug(html)
        raise YoudoListingError(
            "На странице нет карточек заданий (`a[data-id]` / `/t{id}`) — сменилась вёрстка."
            f" HTML saved: {saved}"
        )
    return out


def _fetch_listing_html_browser(
    url: str,
    cfg: Config,
    *,
    timeout_sec: float,
) -> str:
    """Browser-only (O63): все живые слоты, без httpx fallback."""
    try:
        html = fetch_listing_html_browser_slots(
            "youdo",
            url,
            user_agent=cfg.http_user_agent,
            timeout_sec=timeout_sec,
        )
    except HtmlFetchError as exc:
        msg = f"browser_fail={exc}"
        log_pipeline_line(cfg.radar_log_path, f"youdo_listing: {msg}")
        logger.warning("youdo_listing: %s — no httpx fallback", msg)
        raise YoudoListingError(f"browser failed ({exc})") from exc

    if _looks_like_antibot(html):
        saved = _save_listing_html_debug(html, tag="youdo_antibot")
        msg = f"browser_fail=antibot HTML saved={saved}"
        log_pipeline_line(cfg.radar_log_path, f"youdo_listing: {msg}")
        raise YoudoListingError(
            "Ответ похож на антибот после browser — смените YOUDO_PROXY_URLS / слот."
            f" HTML saved: {saved}"
        )
    return html


def _fetch_listing_html(
    url: str,
    cfg: Config,
    *,
    timeout_sec: float,
) -> str:
    """EXCHANGE_LISTING_BROWSER=1 → только Playwright; иначе httpx → legacy Playwright."""
    if listing_browser_enabled():
        return _fetch_listing_html_browser(url, cfg, timeout_sec=timeout_sec)

    hint = proxy_log_hint("youdo")
    html = _fetch_html_requests(url, cfg, timeout_sec=timeout_sec)
    if _looks_like_antibot(html):
        logger.info("youdo_listing: antibot HTML — legacy Playwright fallback (%s)", hint)
        html = _fetch_html_playwright(url, cfg, timeout_sec=timeout_sec)
    return html


def _fetch_html_requests(
    url: str,
    cfg: Config,
    *,
    timeout_sec: float,
) -> str:
    headers = {
        "User-Agent": cfg.http_user_agent,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Referer": "https://youdo.com/",
    }
    resp = exchange_get("youdo", url, headers=headers, timeout_sec=timeout_sec)
    if resp.status_code != 200:
        raise YoudoListingError(f"HTTP {resp.status_code} для ленты ({url})")
    encoding = resp.encoding or "utf-8"
    return resp.content.decode(encoding, errors="replace")


def _fetch_html_playwright(url: str, cfg: Config, *, timeout_sec: float) -> str:
    from exchange_proxy import exchange_primary_proxy_url

    proxy_url = exchange_primary_proxy_url("youdo")
    try:
        return fetch_html_playwright(
            url,
            user_agent=cfg.http_user_agent,
            timeout_sec=timeout_sec,
            proxy_url=proxy_url,
            wait_until="networkidle",
        )
    except HtmlFetchError as exc:
        raise YoudoListingError(str(exc)) from exc


def fetch_listing_projects(cfg: Config, *, timeout_sec: float = 45.0) -> list[ListingProject]:
    """GET листинга YouDo; при антиботе — Playwright + прокси."""
    url = _listing_url()
    exchange_fetch_begin("youdo")
    log_pipeline_line(cfg.radar_log_path, f"fetch:youdo proxy={proxy_log_hint('youdo')}")
    try:
        html = _fetch_listing_html(url, cfg, timeout_sec=timeout_sec)
        return parse_listing_html(html, url)
    finally:
        exchange_fetch_end("youdo")
