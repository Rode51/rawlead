"""Playwright persistent context per proxy slot — FL/Kwork listing (O99)."""

from __future__ import annotations

import logging
import os
import random
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from pathlib import Path
from typing import Any

from config import normalize_proxy_url
from exchange_proxy import (
    _hint_from_url,
    exchange_alive_proxy_urls,
    exchange_primary_proxy_url,
)
from html_fetch import HtmlFetchError, _playwright_proxy

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_CONTEXTS: dict[str, Any] = {}
_PLAYWRIGHT = None
_PW_LOCK = threading.Lock()

_JITTER_MS = (200, 800)
_DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
_CHROME_UAS = (
    _DEFAULT_UA,
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
        "Gecko/20100101 Firefox/124.0"
    ),
)


def _data_root() -> Path:
    raw = os.getenv("EXCHANGE_BROWSER_DATA_DIR", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent.parent / "data" / "browser_profiles"


def listing_browser_enabled() -> bool:
    return os.getenv("EXCHANGE_LISTING_BROWSER", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def pick_browser_user_agent(preferred: str = "") -> str:
    """Random Chrome/Firefox UA for a **new** persistent context (O110-B)."""
    pref = (preferred or "").strip()
    low = pref.casefold()
    if pref and "flradar" not in low and "compatible;" not in low:
        return pref
    return random.choice(_CHROME_UAS)


def _wipe_on_ban_enabled() -> bool:
    return os.getenv("EXCHANGE_BROWSER_WIPE_ON_BAN", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def invalidate_browser_slot(
    source: str,
    proxy_url: str,
    *,
    wipe_disk: bool | None = None,
) -> None:
    """Close Playwright context (+ optional profile dir) after ban/challenge (O110-B)."""
    proxy = (proxy_url or "").strip()
    if not proxy:
        return
    key = _profile_key(source, proxy)
    with _LOCK:
        _close_context(key)
    do_wipe = _wipe_on_ban_enabled() if wipe_disk is None else wipe_disk
    if not do_wipe:
        return
    profile_dir = _data_root() / key
    if profile_dir.is_dir():
        try:
            shutil.rmtree(profile_dir, ignore_errors=True)
            logger.info(
                "browser: wiped profile %s after %s ban/challenge",
                key,
                source,
            )
        except OSError as exc:
            logger.warning("browser: wipe profile %s failed: %s", key, exc)



def _profile_key(source: str, proxy_url: str) -> str:
    hint = _hint_from_url(proxy_url) or "direct"
    return f"{source}_{hint}"


def _jitter_sleep() -> None:
    lo, hi = _JITTER_MS
    time.sleep(random.randint(lo, hi) / 1000.0)


def _get_playwright():
    global _PLAYWRIGHT
    with _PW_LOCK:
        if _PLAYWRIGHT is not None:
            return _PLAYWRIGHT
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise HtmlFetchError(
                "Playwright не установлен (pip install playwright && playwright install chromium)."
            ) from exc
        _PLAYWRIGHT = sync_playwright().start()
        return _PLAYWRIGHT


_HEAVY_RESOURCE_TYPES = frozenset({"image", "font", "media"})


def _should_abort_playwright_request(request) -> bool:
    url = request.url.lower()
    if request.resource_type in _HEAVY_RESOURCE_TYPES:
        return True
    if "tracker" in url or "tag.js" in url:
        return True
    return False


def _abort_heavy_route(route) -> None:
    if _should_abort_playwright_request(route.request):
        route.abort()
    else:
        route.continue_()


def _close_context(key: str) -> None:
    ctx = _CONTEXTS.pop(key, None)
    if ctx is not None:
        try:
            ctx.close()
        except Exception:
            pass


def _fetch_youdo_ephemeral(
    url: str,
    *,
    user_agent: str,
    timeout_sec: float,
    proxy_url: str,
) -> str:
    """YouDo: ephemeral Chromium (persistent profile ломает node-proxy)."""
    ua = _DEFAULT_UA  # YouDo режет FLRadar/бот User-Agent из cfg
    timeout_ms = max(int(timeout_sec * 1000), 5000)
    _jitter_sleep()
    px = _playwright_proxy(proxy_url)
    pw = _get_playwright()
    launch_kw: dict[str, Any] = {"headless": True}
    if px:
        launch_kw["proxy"] = px
    browser = pw.chromium.launch(**launch_kw)
    try:
        ctx = browser.new_context(user_agent=ua, locale="ru-RU")
        ctx.route("**/*", _abort_heavy_route)
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        try:
            page.wait_for_selector('a[data-id][href*="/t"]', timeout=min(45000, timeout_ms))
        except Exception:
            page.wait_for_timeout(5000)
        else:
            page.wait_for_timeout(1500)
        html = page.content()
    finally:
        browser.close()

    low = html.lower()
    if "cloudflare" in low and ("challenge" in low or "blocked" in low):
        raise HtmlFetchError(f"Cloudflare challenge (youdo, {_hint_from_url(proxy_url)})")
    if len(html.strip()) < 500:
        raise HtmlFetchError("Слишком короткий ответ Playwright (youdo).")
    return html


def fetch_listing_html_browser(
    source: str,
    url: str,
    *,
    user_agent: str,
    timeout_sec: float = 45.0,
    proxy_url: str | None = None,
) -> str:
    """GET листинга через Chromium persistent context (cookies на слот прокси)."""
    proxy = (proxy_url or "").strip() or exchange_primary_proxy_url(source)
    key = _profile_key(source, proxy)
    ua = pick_browser_user_agent(user_agent)
    timeout_ms = max(int(timeout_sec * 1000), 5000)
    _jitter_sleep()

    profile_dir = _data_root() / key
    profile_dir.mkdir(parents=True, exist_ok=True)

    with _LOCK:
        ctx = _CONTEXTS.get(key)
        if ctx is None:
            pw = _get_playwright()
            launch_kw: dict[str, Any] = {
                "user_data_dir": str(profile_dir),
                "headless": True,
                "user_agent": ua,
                "locale": "ru-RU",
                "viewport": {"width": 1366, "height": 768},
            }
            px = _playwright_proxy(proxy)
            if px:
                launch_kw["proxy"] = px
            try:
                ctx = pw.chromium.launch_persistent_context(**launch_kw)
            except Exception as exc:
                _close_context(key)
                raise HtmlFetchError(f"Playwright launch failed ({source}): {exc}") from exc
            _CONTEXTS[key] = ctx

    page = ctx.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_timeout(min(1500, timeout_ms // 4))
        html = page.content()
    finally:
        try:
            page.close()
        except Exception:
            pass

    low = html.lower()
    if "cloudflare" in low and ("challenge" in low or "blocked" in low):
        invalidate_browser_slot(source, proxy)
        raise HtmlFetchError(f"Cloudflare challenge ({source}, {key})")
    if len(html.strip()) < 500 or "проверьте, что вы не робот" in low:
        invalidate_browser_slot(source, proxy)
        raise HtmlFetchError(f"Слишком короткий ответ Playwright ({source}).")
    return html


def fetch_listing_html_browser_wall_clock(
    source: str,
    url: str,
    *,
    user_agent: str,
    timeout_sec: float = 45.0,
    wall_clock_sec: float = 120.0,
    proxy_url: str | None = None,
) -> str:
    """Hard cap on listing browser fetch — O117 Kwork hang guard."""
    wall = max(float(wall_clock_sec), 1.0)
    per_op = min(float(timeout_sec), wall)

    def _run() -> str:
        return fetch_listing_html_browser(
            source,
            url,
            user_agent=user_agent,
            timeout_sec=per_op,
            proxy_url=proxy_url,
        )

    pool = ThreadPoolExecutor(max_workers=1)
    fut = pool.submit(_run)
    try:
        return fut.result(timeout=wall)
    except FuturesTimeout:
        proxy = (proxy_url or "").strip() or exchange_primary_proxy_url(source)
        key = _profile_key(source, proxy)
        logger.warning(
            "%s_listing: wall-clock timeout after %ss — closing browser context",
            source,
            int(wall),
        )
        with _LOCK:
            _close_context(key)
        raise HtmlFetchError(f"wall-clock timeout after {int(wall)}s ({source})")
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def fetch_listing_html_browser_slots(
    source: str,
    url: str,
    *,
    user_agent: str,
    timeout_sec: float = 45.0,
    proxy_urls: list[str] | None = None,
) -> str:
    """Browser fetch с перебором живых слотов (O63 YouDo — без httpx fallback)."""
    slots = proxy_urls if proxy_urls is not None else exchange_alive_proxy_urls(source)
    if not slots:
        raise HtmlFetchError(f"{source}: no alive proxy slots for browser")
    last_exc: HtmlFetchError | None = None
    for proxy_url in slots:
        hint = _hint_from_url(proxy_url) or "direct"
        try:
            if source == "youdo":
                return _fetch_youdo_ephemeral(
                    url,
                    user_agent=user_agent,
                    timeout_sec=timeout_sec,
                    proxy_url=proxy_url,
                )
            return fetch_listing_html_browser(
                source,
                url,
                user_agent=user_agent,
                timeout_sec=timeout_sec,
                proxy_url=proxy_url,
            )
        except HtmlFetchError as exc:
            last_exc = exc
            invalidate_browser_slot(source, proxy_url)
            logger.warning(
                "%s_listing: browser slot %s failed: %s",
                source,
                hint,
                exc,
            )
    detail = str(last_exc) if last_exc else "unknown"
    raise HtmlFetchError(f"{source}: all browser slots failed ({len(slots)}): {detail}")


def reset_browser_contexts_for_tests() -> None:
    with _LOCK:
        for key in list(_CONTEXTS):
            _close_context(key)
