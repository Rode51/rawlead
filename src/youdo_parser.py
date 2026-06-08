"""Парсинг листинга YouDo: SSR Next.js `/tasks-all-opened-all`."""

from __future__ import annotations

import json
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
    fetch_youdo_detail_html,
    listing_browser_enabled,
    youdo_browser_only,
)
from exchange_proxy import (
    exchange_fetch_begin,
    exchange_fetch_end,
    exchange_get,
    exchange_primary_proxy_url,
    proxy_log_hint,
)
from html_fetch import HtmlFetchError, fetch_html_playwright
from listing import SOURCE_YOUDO, ListingProject
from radar_cycle_log import log_pipeline_line

logger = logging.getLogger(__name__)

YOUDO_COOLDOWN_KEY = "youdo_cooldown_until"
YOUDO_FETCH_CYCLE_KEY = "youdo_fetch_cycle_n"

_DEFAULT_LISTING_URL = "https://youdo.com/tasks-all-opened-all"
_TASK_ID_RE = re.compile(r"/t(\d+)")
_ANTIBOT_MARKERS = ("noscript", "exhkqyad", "just a moment", "checking your browser")


class YoudoListingError(RuntimeError):
    """Не удалось разобрать ленту YouDo."""


def _youdo_cooldown_min() -> int:
    return max(1, int(os.getenv("YOUDO_COOLDOWN_MIN", "30")))


def _youdo_fetch_every_n() -> int:
    return max(1, int(os.getenv("YOUDO_FETCH_EVERY_N_CYCLES", "4")))


def _youdo_detail_fetch_enabled() -> bool:
    return os.getenv("YOUDO_DETAIL_FETCH", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _should_fetch_youdo_listing(storage) -> bool:
    every = _youdo_fetch_every_n()
    if every <= 1:
        return True
    raw = storage.get_setting(YOUDO_FETCH_CYCLE_KEY, "0") or "0"
    try:
        n = int(raw) + 1
    except ValueError:
        n = 1
    storage.set_setting(YOUDO_FETCH_CYCLE_KEY, str(n))
    return (n - 1) % every == 0


def _log_youdo_fetch_every_n_skip(cfg: Config) -> None:
    log_pipeline_line(cfg.radar_log_path, "youdo:skip fetch_every_n")
    try:
        from exchange_trace import log_exchange_trace

        log_exchange_trace("youdo", stage="fetch_every_n_skip")
    except Exception:
        pass


def _storage_for_cfg(cfg: Config):
    from storage import ProjectStorage

    return ProjectStorage(cfg.sqlite_path)


def youdo_cooldown_active(storage) -> tuple[bool, str]:
    raw = storage.get_setting(YOUDO_COOLDOWN_KEY, "0").strip()
    try:
        until = float(raw or 0)
    except ValueError:
        until = 0.0
    now = time.time()
    if until > now:
        mins = max(1, int((until - now + 59) // 60))
        hhmm = time.strftime("%H:%M", time.localtime(until))
        return True, f"cooldown до {hhmm} ({mins} min)"
    return False, ""


def set_youdo_cooldown(storage) -> None:
    until = time.time() + _youdo_cooldown_min() * 60
    storage.set_setting(YOUDO_COOLDOWN_KEY, str(until))


def _log_youdo_cooldown_skip(cfg: Config, mins: int) -> None:
    log_pipeline_line(cfg.radar_log_path, f"youdo:skip cooldown {mins} min")
    try:
        from exchange_trace import log_exchange_trace

        log_exchange_trace("youdo", stage="cooldown_skip", err=f"{mins}min")
    except Exception:
        pass


def _on_youdo_fetch_fail(cfg: Config, storage) -> None:
    set_youdo_cooldown(storage)
    proxy = exchange_primary_proxy_url("youdo")
    if proxy:
        from exchange_browser_fetch import invalidate_browser_slot

        invalidate_browser_slot("youdo", proxy)


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
    storage,
) -> str:
    """Browser-only (O63/O156): primary slot, warm human path."""
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
        _on_youdo_fetch_fail(cfg, storage)
        raise YoudoListingError(f"browser failed ({exc})") from exc

    if _looks_like_antibot(html):
        saved = _save_listing_html_debug(html, tag="youdo_antibot")
        msg = f"browser_fail=antibot HTML saved={saved}"
        log_pipeline_line(cfg.radar_log_path, f"youdo_listing: {msg}")
        _on_youdo_fetch_fail(cfg, storage)
        raise YoudoListingError(
            "Ответ похож на антибот после browser — cooldown."
            f" HTML saved: {saved}"
        )
    return html


def _fetch_listing_html(
    url: str,
    cfg: Config,
    *,
    timeout_sec: float,
    storage,
) -> str:
    """EXCHANGE_LISTING_BROWSER=1 → только Playwright; иначе httpx → legacy Playwright."""
    if listing_browser_enabled() or youdo_browser_only():
        return _fetch_listing_html_browser(url, cfg, timeout_sec=timeout_sec, storage=storage)

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


def _parse_youdo_detail_html(html: str, *, fallback_snippet: str = "") -> str:
    """Полный текст ТЗ со страницы /t{id}."""
    if not html or not html.strip():
        return fallback_snippet
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if script and script.string:
        try:
            payload = json.loads(script.string)
            props = payload.get("props", {}).get("pageProps", {})
            for key in ("task", "taskData", "data"):
                block = props.get(key)
                if isinstance(block, dict):
                    for field in ("description", "text", "content", "body"):
                        val = block.get(field)
                        if isinstance(val, str) and len(val.strip()) > len(
                            (fallback_snippet or "").strip()
                        ):
                            return val.strip()
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass
    for sel in (
        '[class*="TaskDescription"]',
        '[class*="Description_text"]',
        '[class*="taskDescription"]',
        ".task-description",
        "article",
    ):
        node = soup.select_one(sel)
        if node:
            text = node.get_text(" ", strip=True)
            if len(text) > len((fallback_snippet or "").strip()):
                return text
    return fallback_snippet


def fetch_project_page_html(
    project_url: str,
    cfg: Config,
    *,
    timeout_sec: float = 45.0,
) -> tuple[str, bool]:
    url = (project_url or "").strip()
    if not url:
        return "", False
    if not _youdo_detail_fetch_enabled():
        return "", False
    if youdo_browser_only():
        try:
            html = fetch_youdo_detail_html(
                url,
                user_agent=cfg.http_user_agent,
                timeout_sec=timeout_sec,
            )
            if html and not _looks_like_antibot(html):
                return html, True
        except HtmlFetchError as exc:
            logger.warning("youdo_detail: browser failed: %s", exc)
        return "", False
    headers = {
        "User-Agent": cfg.http_user_agent,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Referer": "https://youdo.com/",
    }
    try:
        resp = exchange_get("youdo", url, headers=headers, timeout_sec=timeout_sec)
        if resp.status_code == 200:
            encoding = resp.encoding or "utf-8"
            html = resp.content.decode(encoding, errors="replace")
            if not _looks_like_antibot(html):
                return html, True
    except Exception:
        pass
    try:
        html = _fetch_html_playwright(url, cfg, timeout_sec=timeout_sec)
        if html and not _looks_like_antibot(html):
            return html, True
    except YoudoListingError:
        pass
    return "", False


def fetch_project_detail(
    project_url: str,
    cfg: Config,
    *,
    fallback_snippet: str = "",
    timeout_sec: float = 45.0,
) -> tuple[str, str, bool]:
    """(description, html, detail_ok)."""
    html, ok = fetch_project_page_html(project_url, cfg, timeout_sec=timeout_sec)
    if not ok:
        return fallback_snippet, "", False
    text = _parse_youdo_detail_html(html, fallback_snippet=fallback_snippet)
    detail_ok = bool(text and text != (fallback_snippet or "").strip())
    return text, html, detail_ok


def fetch_listing_projects(
    cfg: Config,
    *,
    timeout_sec: float = 45.0,
    storage=None,
) -> list[ListingProject]:
    """GET листинга YouDo; при антиботе — Playwright + прокси."""
    st = storage or _storage_for_cfg(cfg)
    active, msg = youdo_cooldown_active(st)
    if active:
        raw = st.get_setting(YOUDO_COOLDOWN_KEY, "0").strip()
        try:
            until = float(raw or 0)
            mins = max(1, int((until - time.time() + 59) // 60))
        except ValueError:
            mins = _youdo_cooldown_min()
        _log_youdo_cooldown_skip(cfg, mins)
        st.set_setting("status_youdo_cooldown_msg", msg)
        return []
    st.set_setting("status_youdo_cooldown_msg", "")
    if not _should_fetch_youdo_listing(st):
        _log_youdo_fetch_every_n_skip(cfg)
        return []
    url = _listing_url()
    exchange_fetch_begin("youdo")
    log_pipeline_line(cfg.radar_log_path, f"fetch:youdo proxy={proxy_log_hint('youdo')}")
    try:
        html = _fetch_listing_html(url, cfg, timeout_sec=timeout_sec, storage=st)
        return parse_listing_html(html, url)
    finally:
        exchange_fetch_end("youdo")
