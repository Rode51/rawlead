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
_FETCH_LOCKS_GUARD = threading.Lock()
_FETCH_LOCKS: dict[str, threading.Lock] = {}
_CONTEXTS: dict[str, Any] = {}
_PLAYWRIGHT = None
_PW_LOCK = threading.Lock()
_PW_THREAD_PREFIX = "rawlead-playwright"
_PW_EXECUTOR: ThreadPoolExecutor | None = None
_PW_EXECUTOR_LOCK = threading.Lock()


def _on_playwright_thread() -> bool:
    return threading.current_thread().name.startswith(_PW_THREAD_PREFIX)


def _pw_executor() -> ThreadPoolExecutor:
    global _PW_EXECUTOR
    with _PW_EXECUTOR_LOCK:
        if _PW_EXECUTOR is None:
            _PW_EXECUTOR = ThreadPoolExecutor(
                max_workers=1,
                thread_name_prefix=_PW_THREAD_PREFIX,
            )
        return _PW_EXECUTOR


def _playwright_sync(func, /, *args, **kwargs):
    if _on_playwright_thread():
        return func(*args, **kwargs)
    fut = _pw_executor().submit(lambda: func(*args, **kwargs))
    return fut.result()


def _playwright_sync_timed(func, timeout_sec: float):
    if _on_playwright_thread():
        return func()
    fut = _pw_executor().submit(func)
    return fut.result(timeout=max(float(timeout_sec), 1.0))


def _abort_playwright_worker() -> None:
    """Drop a hung Playwright worker; next fetch spawns a fresh dedicated thread."""
    global _PW_EXECUTOR, _PLAYWRIGHT
    _WARMED_YOUDO_KEYS.clear()
    with _LOCK:
        _CONTEXTS.clear()
    with _PW_EXECUTOR_LOCK:
        if _PW_EXECUTOR is not None:
            _PW_EXECUTOR.shutdown(wait=False, cancel_futures=True)
            _PW_EXECUTOR = None
    with _PW_LOCK:
        if _PLAYWRIGHT is not None:
            try:
                _PLAYWRIGHT.stop()
            except Exception:
                pass
            _PLAYWRIGHT = None

_STALE_BROWSER_MARKERS = (
    "chrome-headless",
    "headless_shell",
    "chromium",
    "ms-playwright",
    "playwright/chromium",
    "playwright/driver",
)

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


def _fetch_lock(source: str) -> threading.Lock:
    """Per-source fetch lock — FL hang must not block Kwork (O160)."""
    key = (source or "unknown").strip().lower() or "unknown"
    with _FETCH_LOCKS_GUARD:
        lock = _FETCH_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _FETCH_LOCKS[key] = lock
        return lock


def _radar_stage_log_enabled() -> bool:
    return os.getenv("RADAR_STAGE_LOG", "0").strip().lower() in ("1", "true", "yes")


def _stage_log(source: str, stage: str, *, proxy_url: str = "", detail: str = "") -> None:
    if not _radar_stage_log_enabled():
        return
    hint = _hint_from_url(proxy_url) if proxy_url else ""
    proxy_part = f" proxy={hint}" if hint else ""
    extra = f" {detail}" if detail else ""
    logger.info(
        "fetch:%s stage=%s started_at=%s%s%s",
        source,
        stage,
        time.strftime("%H:%M:%S"),
        proxy_part,
        extra,
    )


def listing_browser_enabled() -> bool:
    return os.getenv("EXCHANGE_LISTING_BROWSER", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def youdo_browser_only() -> bool:
    if not listing_browser_enabled():
        return False
    return os.getenv("YOUDO_BROWSER_ONLY", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def youdo_one_slot_per_cycle() -> bool:
    return os.getenv("YOUDO_ONE_SLOT_PER_CYCLE", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def youdo_ephemeral() -> bool:
    return os.getenv("YOUDO_EPHEMERAL", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def youdo_warm_home_enabled() -> bool:
    """O177: warm youdo.com/ often hangs 45s on VPS proxy — listing SSR needs no warm."""
    return os.getenv("YOUDO_WARM_HOME", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _youdo_listing_goto_timeout_ms(timeout_sec: float) -> int:
    raw = os.getenv("YOUDO_GOTO_TIMEOUT_SEC", "").strip()
    if raw:
        try:
            return max(int(float(raw) * 1000), 5000)
        except ValueError:
            pass
    return max(int(float(timeout_sec) * 1000), 5000)


def _youdo_warm_goto_timeout_ms() -> int:
    raw = os.getenv("YOUDO_WARM_TIMEOUT_SEC", "20").strip()
    try:
        return max(int(float(raw) * 1000), 5000)
    except ValueError:
        return 20_000


def _youdo_slot_retry_max() -> int:
    raw = os.getenv("YOUDO_SLOT_RETRY_ON_TIMEOUT", "3").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 3


def _is_timeout_error(exc: BaseException) -> bool:
    msg = f"{type(exc).__name__} {exc}".casefold()
    return "timeout" in msg or "timed out" in msg


def _wrap_youdo_browser_error(exc: BaseException) -> HtmlFetchError:
    """Slot retry catches HtmlFetchError only — wrap Playwright TimeoutError (O177b)."""
    if isinstance(exc, HtmlFetchError):
        return exc
    return HtmlFetchError(f"{type(exc).__name__}: {exc}")


def _youdo_goto_wait_until() -> str:
    raw = os.getenv("YOUDO_GOTO_WAIT_UNTIL", "domcontentloaded").strip().casefold()
    if raw in ("commit", "domcontentloaded", "load", "networkidle"):
        return raw
    return "domcontentloaded"


def _youdo_goto_wait_until_for_attempt(slot_attempt: int) -> str:
    """Slot 2+ uses lighter wait (commit) — domcontentloaded often never fires on proxy (O179)."""
    if slot_attempt > 1:
        raw = os.getenv("YOUDO_RETRY_GOTO_WAIT_UNTIL", "commit").strip().casefold()
        if raw in ("commit", "domcontentloaded", "load", "networkidle"):
            return raw
        return "commit"
    return _youdo_goto_wait_until()


def _youdo_lean_route_on_attempt(slot_attempt: int) -> bool:
    """Full page load on retry — lean abort can block SSR hydration through node-proxy."""
    if slot_attempt <= 1:
        return True
    return os.getenv("YOUDO_LEAN_ON_RETRY", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _is_youdo_slot_retryable(exc: HtmlFetchError) -> bool:
    if _is_timeout_error(exc):
        return True
    msg = str(exc).casefold()
    markers = (
        "antibot",
        "короткий",
        "cloudflare",
        "forbidden",
        "empty html",
        "403",
    )
    return any(m in msg for m in markers)


def _save_youdo_debug_html(html: str, *, tag: str = "youdo_fail") -> str:
    root = _data_root().parent / "debug_listings"
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{tag}_{int(time.time())}.html"
    path.write_text((html or "")[:500_000], encoding="utf-8", errors="replace")
    return str(path)


def _youdo_ephemeral_on_slot_retry() -> bool:
    return os.getenv("YOUDO_EPHEMERAL_ON_RETRY", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _youdo_jitter_ms() -> tuple[int, int]:
    raw = os.getenv("YOUDO_JITTER_MS", "2000,8000").strip()
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if len(parts) >= 2:
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            pass
    return 2000, 8000


def _youdo_jitter_sleep() -> None:
    lo, hi = _youdo_jitter_ms()
    time.sleep(random.randint(lo, hi) / 1000.0)


_WARMED_YOUDO_KEYS: set[str] = set()


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
    if not _on_playwright_thread():
        _playwright_sync(
            invalidate_browser_slot,
            source,
            proxy_url,
            wipe_disk=wipe_disk,
        )
        return
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


def _log_browser_trace(
    source: str,
    proxy_url: str,
    stage: str,
    t0: float,
    **fields: Any,
) -> None:
    try:
        from exchange_trace import log_exchange_trace

        log_exchange_trace(
            source,
            stage=stage,
            ms=int((time.monotonic() - t0) * 1000),
            proxy=_hint_from_url(proxy_url),
            **fields,
        )
    except Exception:
        pass


def _log_youdo_browser_trace(
    *,
    launch_ms: int,
    goto_ms: int,
    status: str,
    html_len: int = 0,
    antibot_hit: bool = False,
    debug_path: str = "",
) -> None:
    try:
        from youdo_parser import log_youdo_trace_path

        log_youdo_trace_path(
            None,
            "browser",
            launch_ms=launch_ms,
            goto_ms=goto_ms,
            status=status,
            html_len=html_len,
            antibot_hit=1 if antibot_hit else 0,
            debug_path=debug_path or "",
        )
    except Exception:
        pass


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
_YOUDO_BLOCK_RESOURCE_TYPES = frozenset(
    {"image", "font", "media", "stylesheet", "xhr", "fetch", "websocket"}
)
_YOUDO_ANALYTICS_MARKERS = (
    "google-analytics",
    "googletagmanager",
    "mc.yandex",
    "metrika",
    "facebook.net",
    "doubleclick",
    "hotjar",
    "segment.io",
    "amplitude",
    "analytics",
)
_WARM_AT_KEY_PREFIX = "youdo_warm_at_"


def _should_abort_playwright_request(request) -> bool:
    url = request.url.lower()
    if request.resource_type in _HEAVY_RESOURCE_TYPES:
        return True
    if "tracker" in url or "tag.js" in url:
        return True
    return False


def _should_abort_youdo_request(request) -> bool:
    url = request.url.lower()
    rtype = request.resource_type
    # O157 lean: xhr/fetch нужны для API листинга — не резать youdo.com
    if rtype in ("xhr", "fetch") and "youdo.com" in url:
        return False
    if rtype in _YOUDO_BLOCK_RESOURCE_TYPES:
        return True
    if any(marker in url for marker in _YOUDO_ANALYTICS_MARKERS):
        return True
    if "tracker" in url or "tag.js" in url:
        return True
    return False


def _abort_heavy_route(route) -> None:
    if _should_abort_playwright_request(route.request):
        route.abort()
    else:
        route.continue_()


def _abort_youdo_lean_route(route) -> None:
    if _should_abort_youdo_request(route.request):
        route.abort()
    else:
        route.continue_()


def _youdo_warm_ttl_sec() -> float:
    return max(0.0, float(os.getenv("YOUDO_WARM_TTL_MIN", "45"))) * 60.0


def _youdo_settings_storage():
    from config import load_config
    from storage import ProjectStorage

    return ProjectStorage(load_config().sqlite_path)


def _youdo_warm_recent(key: str) -> bool:
    ttl = _youdo_warm_ttl_sec()
    if ttl <= 0:
        return False
    try:
        raw = _youdo_settings_storage().get_setting(f"{_WARM_AT_KEY_PREFIX}{key}", "0")
        return time.time() - float(raw or 0) < ttl
    except (ValueError, OSError):
        return False


def _mark_youdo_warm(key: str) -> None:
    _WARMED_YOUDO_KEYS.add(key)
    try:
        _youdo_settings_storage().set_setting(
            f"{_WARM_AT_KEY_PREFIX}{key}",
            str(time.time()),
        )
    except OSError:
        pass


def _maybe_warm_youdo_home(
    page,
    proxy_url: str,
    key: str,
    *,
    timeout_ms: int,
) -> None:
    if not youdo_warm_home_enabled():
        return
    if key in _WARMED_YOUDO_KEYS:
        return
    if _youdo_warm_recent(key):
        _log_browser_trace("youdo", proxy_url, "warm_home_skip", time.monotonic(), ms=0)
        _WARMED_YOUDO_KEYS.add(key)
        return
    _warm_youdo_home(page, proxy_url, timeout_ms=timeout_ms)
    _mark_youdo_warm(key)


def reset_youdo_warm_state_for_tests() -> None:
    _WARMED_YOUDO_KEYS.clear()


def _close_context(key: str) -> None:
    ctx = _CONTEXTS.pop(key, None)
    if ctx is not None:
        try:
            ctx.close()
        except Exception:
            pass


def close_all_browser_contexts() -> None:
    """Close every open Playwright persistent context (O132 cycle teardown)."""
    if not _on_playwright_thread():
        _playwright_sync(close_all_browser_contexts)
        return
    _WARMED_YOUDO_KEYS.clear()
    with _LOCK:
        for key in list(_CONTEXTS):
            _close_context(key)


def _is_stale_browser_process(name: str, cmd: str) -> bool:
    blob = f"{name} {cmd}".casefold()
    return any(marker in blob for marker in _STALE_BROWSER_MARKERS)


def _browser_process_tree() -> set[int]:
    import psutil

    root = os.getpid()
    tree = {root}
    try:
        proc = psutil.Process(root)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return tree
    for child in proc.children(recursive=True):
        try:
            tree.add(child.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return tree


def cleanup_stale_browser_processes() -> int:
    """Kill orphan chrome-headless / Playwright PIDs for the current user (O132)."""
    import getpass

    import psutil

    user = getpass.getuser().casefold()
    keep = _browser_process_tree()
    killed = 0
    for proc in psutil.process_iter(["pid", "username", "name", "cmdline"]):
        try:
            info = proc.info
            pid = int(info.get("pid") or 0)
            if pid <= 0 or pid in keep:
                continue
            owner = str(info.get("username") or "").casefold()
            if owner and owner != user:
                continue
            name = str(info.get("name") or "")
            cmdline = info.get("cmdline") or []
            cmd = " ".join(str(part) for part in cmdline)
            if not _is_stale_browser_process(name, cmd):
                continue
            proc.kill()
            killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, ProcessLookupError):
            pass
    if killed:
        logger.info("browser:cleanup killed=%d", killed)
    return killed


def _youdo_profile_key(proxy_url: str) -> str:
    return _profile_key("youdo", proxy_url)


def _launch_youdo_persistent_context(
    proxy_url: str,
    *,
    user_agent: str,
) -> Any:
    key = _youdo_profile_key(proxy_url)
    with _LOCK:
        ctx = _CONTEXTS.get(key)
        if ctx is not None:
            return ctx, key

    profile_dir = _data_root() / key
    profile_dir.mkdir(parents=True, exist_ok=True)
    pw = _get_playwright()
    ua = pick_browser_user_agent(user_agent)
    launch_kw: dict[str, Any] = {
        "user_data_dir": str(profile_dir),
        "headless": True,
        "user_agent": ua,
        "locale": "ru-RU",
        "timezone_id": "Europe/Moscow",
        "viewport": {"width": 1366, "height": 768},
    }
    px = _playwright_proxy(proxy_url)
    if px:
        launch_kw["proxy"] = px
    try:
        ctx = pw.chromium.launch_persistent_context(**launch_kw)
    except Exception as exc:
        _close_context(key)
        raise HtmlFetchError(f"Playwright launch failed (youdo): {exc}") from exc
    ctx.route("**/*", _abort_youdo_lean_route)
    with _LOCK:
        _CONTEXTS[key] = ctx
    return ctx, key


def _warm_youdo_home(page, proxy_url: str, *, timeout_ms: int) -> None:
    t0 = time.monotonic()
    page.goto("https://youdo.com/", wait_until="domcontentloaded", timeout=timeout_ms)
    page.wait_for_timeout(random.randint(2000, 5000))
    try:
        page.mouse.wheel(0, 400)
    except Exception:
        pass
    page.wait_for_timeout(random.randint(1000, 2000))
    _log_browser_trace("youdo", proxy_url, "warm_home", t0, http=200)


def _validate_youdo_html(html: str, proxy_url: str) -> None:
    low = html.lower()
    if not html.strip():
        raise HtmlFetchError("empty HTML after goto (youdo)")
    if "403 forbidden" in low[:3000]:
        raise HtmlFetchError("403 Forbidden (youdo)")
    if "cloudflare" in low and ("challenge" in low or "blocked" in low):
        raise HtmlFetchError(f"Cloudflare challenge (youdo, {_hint_from_url(proxy_url)})")
    if len(html.strip()) < 500:
        raise HtmlFetchError("Слишком короткий ответ Playwright (youdo).")
    if "проверьте, что вы не робот" in low:
        raise HtmlFetchError("Antibot HTML (youdo).")


def fetch_youdo_html_browser(
    url: str,
    *,
    user_agent: str,
    timeout_sec: float,
    proxy_url: str,
    stage: str = "listing",
    slot_attempt: int = 1,
    with_final_url: bool = False,
) -> str | tuple[str, str]:
    """O156: warm human Playwright path for YouDo listing/detail."""
    if not _on_playwright_thread():
        return _playwright_sync(
            fetch_youdo_html_browser,
            url,
            user_agent=user_agent,
            timeout_sec=timeout_sec,
            proxy_url=proxy_url,
            stage=stage,
            slot_attempt=slot_attempt,
            with_final_url=with_final_url,
        )
    if youdo_ephemeral():
        return _fetch_youdo_ephemeral(
            url,
            user_agent=user_agent,
            timeout_sec=timeout_sec,
            proxy_url=proxy_url,
            stage=stage,
            slot_attempt=slot_attempt,
        )

    _youdo_jitter_sleep()
    timeout_ms = max(int(timeout_sec * 1000), 5000)
    launch_t0 = time.monotonic()
    ctx, key = _launch_youdo_persistent_context(proxy_url, user_agent=user_agent)
    launch_ms = int((time.monotonic() - launch_t0) * 1000)
    page = ctx.new_page()
    goto_t0 = time.monotonic()
    listing_timeout_ms = _youdo_listing_goto_timeout_ms(timeout_sec)
    html = ""
    final_url = url
    try:
        if stage == "listing" and key not in _WARMED_YOUDO_KEYS and youdo_warm_home_enabled():
            try:
                _maybe_warm_youdo_home(
                    page,
                    proxy_url,
                    key,
                    timeout_ms=_youdo_warm_goto_timeout_ms(),
                )
            except Exception as warm_exc:
                logger.warning(
                    "youdo: warm_home failed (%s) — listing direct",
                    warm_exc,
                )
                _log_browser_trace(
                    "youdo",
                    proxy_url,
                    "warm_home_fail",
                    time.monotonic(),
                    err=type(warm_exc).__name__,
                )
        page.goto(
            url,
            wait_until=_youdo_goto_wait_until_for_attempt(slot_attempt),
            timeout=listing_timeout_ms,
        )
        if stage == "listing":
            try:
                page.wait_for_selector(
                    'a[data-id][href*="/t"]',
                    timeout=min(45000, listing_timeout_ms),
                )
            except Exception:
                page.wait_for_timeout(5000)
            else:
                page.wait_for_timeout(1500)
        else:
            page.wait_for_timeout(min(2000, timeout_ms // 4))
        html = page.content()
        final_url = page.url or url
        goto_ms = int((time.monotonic() - goto_t0) * 1000)
        bytes_est = len(html.encode("utf-8", errors="replace"))
        _log_browser_trace(
            "youdo", proxy_url, stage, goto_t0, http=200, bytes_est=bytes_est
        )
        _log_youdo_browser_trace(
            launch_ms=launch_ms,
            goto_ms=goto_ms,
            status="200",
            html_len=len(html),
            antibot_hit=False,
        )
    except Exception as exc:
        goto_ms = int((time.monotonic() - goto_t0) * 1000)
        err_status = "timeout" if _is_timeout_error(exc) else type(exc).__name__
        _log_browser_trace("youdo", proxy_url, stage, goto_t0, err=type(exc).__name__)
        _log_youdo_browser_trace(
            launch_ms=launch_ms,
            goto_ms=goto_ms,
            status=err_status,
            html_len=len(html),
            antibot_hit=False,
        )
        raise _wrap_youdo_browser_error(exc) from exc
    finally:
        try:
            page.close()
        except Exception:
            pass

    try:
        _validate_youdo_html(html, proxy_url)
    except HtmlFetchError as val_exc:
        if stage == "detail" and _youdo_delist_html_ok(html, final_url):
            if with_final_url:
                return html, final_url
            return html
        debug_path = ""
        if html.strip():
            debug_path = _save_youdo_debug_html(html, tag="youdo_antibot")
        _log_youdo_browser_trace(
            launch_ms=launch_ms,
            goto_ms=int((time.monotonic() - goto_t0) * 1000),
            status="antibot",
            html_len=len(html),
            antibot_hit=True,
            debug_path=debug_path,
        )
        raise val_exc
    if with_final_url:
        return html, final_url
    return html


def _youdo_delist_html_ok(html: str, final_url: str) -> bool:
    """Allow short/gone YouDo detail pages through delist validation."""
    low = (html or "").casefold()
    fin = (final_url or "").casefold()
    if "page-deleted" in fin:
        return True
    gone_bits = (
        "страница была удалена",
        "удалена или доступ к ней ограничен",
        "задание закрыто",
        "задание не найдено",
    )
    return any(m in low for m in gone_bits)


def fetch_youdo_detail_html(
    url: str,
    *,
    user_agent: str,
    timeout_sec: float = 45.0,
    proxy_url: str | None = None,
) -> str:
    proxy = (proxy_url or "").strip() or exchange_primary_proxy_url("youdo")
    if not proxy:
        raise HtmlFetchError("youdo: no proxy for detail fetch")
    return fetch_youdo_html_browser(
        url,
        user_agent=user_agent,
        timeout_sec=timeout_sec,
        proxy_url=proxy,
        stage="detail",
    )


def fetch_youdo_detail_snapshot(
    url: str,
    *,
    user_agent: str,
    timeout_sec: float = 60.0,
    proxy_url: str | None = None,
) -> tuple[str, str]:
    """O180 delist: Playwright detail page + final URL after redirects."""
    if (proxy_url or "").strip():
        candidates = [proxy_url.strip()]
    else:
        candidates = exchange_alive_proxy_urls("youdo")
        if not candidates:
            primary = exchange_primary_proxy_url("youdo")
            if primary:
                candidates = [primary]
    if not candidates:
        raise HtmlFetchError("youdo: no proxy for detail fetch")

    last_err: HtmlFetchError | None = None
    for proxy in candidates:
        try:
            # Ephemeral detail fetch — persistent ctx often hangs on VPS delist (O180).
            html = _fetch_youdo_ephemeral(
                url,
                user_agent=user_agent,
                timeout_sec=timeout_sec,
                proxy_url=proxy,
                stage="detail",
            )
            final_url = url
            low = html.casefold()
            if "page-deleted" in low:
                final_url = "https://youdo.com/?page-deleted"
            return html, final_url
        except HtmlFetchError as exc:
            last_err = exc
            logger.warning(
                "youdo: detail snapshot failed proxy=%s err=%s",
                _hint_from_url(proxy),
                exc,
            )
    raise last_err or HtmlFetchError("youdo: detail snapshot failed")


def _fetch_youdo_ephemeral(
    url: str,
    *,
    user_agent: str,
    timeout_sec: float,
    proxy_url: str,
    stage: str = "listing",
    slot_attempt: int = 1,
) -> str:
    """YouDo legacy: ephemeral Chromium (YOUDO_EPHEMERAL=1)."""
    with _fetch_lock("youdo"):
        ua = pick_browser_user_agent(user_agent)
        timeout_ms = max(int(timeout_sec * 1000), 5000)
        _youdo_jitter_sleep()
        px = _playwright_proxy(proxy_url)
        pw = _get_playwright()
        launch_kw: dict[str, Any] = {"headless": True}
        if px:
            launch_kw["proxy"] = px
        launch_t0 = time.monotonic()
        browser = pw.chromium.launch(**launch_kw)
        launch_ms = int((time.monotonic() - launch_t0) * 1000)
        goto_t0 = time.monotonic()
        html = ""
        try:
            ctx = browser.new_context(
                user_agent=ua,
                locale="ru-RU",
                timezone_id="Europe/Moscow",
                viewport={"width": 1366, "height": 768},
            )
            if _youdo_lean_route_on_attempt(slot_attempt):
                ctx.route("**/*", _abort_youdo_lean_route)
            page = ctx.new_page()
            listing_timeout_ms = _youdo_listing_goto_timeout_ms(timeout_sec)
            if stage == "listing" and youdo_warm_home_enabled():
                try:
                    _maybe_warm_youdo_home(
                        page,
                        proxy_url,
                        _youdo_profile_key(proxy_url),
                        timeout_ms=_youdo_warm_goto_timeout_ms(),
                    )
                except Exception as warm_exc:
                    logger.warning(
                        "youdo: warm_home failed (%s) — listing direct",
                        warm_exc,
                    )
            page.goto(
                url,
                wait_until=_youdo_goto_wait_until_for_attempt(slot_attempt),
                timeout=listing_timeout_ms,
            )
            if stage == "listing":
                try:
                    page.wait_for_selector(
                        'a[data-id][href*="/t"]',
                        timeout=min(45000, listing_timeout_ms),
                    )
                except Exception:
                    page.wait_for_timeout(5000)
                else:
                    page.wait_for_timeout(1500)
            else:
                page.wait_for_timeout(min(2000, timeout_ms // 4))
            html = page.content()
            goto_ms = int((time.monotonic() - goto_t0) * 1000)
            bytes_est = len(html.encode("utf-8", errors="replace"))
            _log_browser_trace(
                "youdo", proxy_url, stage, goto_t0, http=200, bytes_est=bytes_est
            )
            _log_youdo_browser_trace(
                launch_ms=launch_ms,
                goto_ms=goto_ms,
                status="200",
                html_len=len(html),
                antibot_hit=False,
            )
        except Exception as exc:
            goto_ms = int((time.monotonic() - goto_t0) * 1000)
            err_status = "timeout" if _is_timeout_error(exc) else type(exc).__name__
            _log_browser_trace("youdo", proxy_url, stage, goto_t0, err=type(exc).__name__)
            _log_youdo_browser_trace(
                launch_ms=launch_ms,
                goto_ms=goto_ms,
                status=err_status,
                html_len=len(html),
                antibot_hit=False,
            )
            raise _wrap_youdo_browser_error(exc) from exc
        finally:
            browser.close()

    try:
        _validate_youdo_html(html, proxy_url)
    except HtmlFetchError as val_exc:
        if stage == "detail" and _youdo_delist_html_ok(html, url):
            return html
        debug_path = ""
        if html.strip():
            debug_path = _save_youdo_debug_html(html, tag="youdo_antibot")
        _log_youdo_browser_trace(
            launch_ms=launch_ms,
            goto_ms=int((time.monotonic() - goto_t0) * 1000),
            status="antibot",
            html_len=len(html),
            antibot_hit=True,
            debug_path=debug_path,
        )
        raise val_exc
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
    if not _on_playwright_thread():
        return _playwright_sync(
            fetch_listing_html_browser,
            source,
            url,
            user_agent=user_agent,
            timeout_sec=timeout_sec,
            proxy_url=proxy_url,
        )
    with _fetch_lock(source):
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
        t0 = time.monotonic()
        _stage_log(source, "goto", proxy_url=proxy)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(min(1500, timeout_ms // 4))
            html = page.content()
            elapsed = time.monotonic() - t0
            if _radar_stage_log_enabled():
                logger.info(
                    "fetch:%s stage=goto elapsed=%.1fs ok%s",
                    source,
                    elapsed,
                    f" proxy={_hint_from_url(proxy)}" if proxy else "",
                )
            _log_browser_trace(source, proxy, "browser_goto", t0, http=200)
        except Exception as exc:
            elapsed = time.monotonic() - t0
            if _radar_stage_log_enabled():
                logger.info(
                    "fetch:%s stage=goto elapsed=%.1fs err=%s",
                    source,
                    elapsed,
                    type(exc).__name__,
                )
            _log_browser_trace(source, proxy, "browser_goto", t0, err=type(exc).__name__)
            raise
        finally:
            try:
                page.close()
            except Exception:
                pass
            with _LOCK:
                _close_context(key)

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

    try:
        return _playwright_sync_timed(_run, wall)
    except FuturesTimeout:
        logger.warning(
            "%s_listing: wall-clock timeout after %ss — closing browser context",
            source,
            int(wall),
        )
        if _radar_stage_log_enabled():
            logger.info(
                "fetch:%s stage=goto elapsed=%.1fs TIMEOUT → wall-clock kill",
                source,
                wall,
            )
        _abort_playwright_worker()
        raise HtmlFetchError(f"wall-clock timeout after {int(wall)}s ({source})")


def fetch_listing_html_browser_slots_wall_clock(
    source: str,
    url: str,
    *,
    user_agent: str,
    timeout_sec: float = 45.0,
    wall_clock_sec: float = 120.0,
    proxy_urls: list[str] | None = None,
) -> str:
    """Hard cap on slots browser fetch — O160 YouDo hang guard."""
    wall = max(float(wall_clock_sec), 1.0)
    per_op = min(float(timeout_sec), wall)

    def _run() -> str:
        return fetch_listing_html_browser_slots(
            source,
            url,
            user_agent=user_agent,
            timeout_sec=per_op,
            proxy_urls=proxy_urls,
        )

    try:
        return _playwright_sync_timed(_run, wall)
    except FuturesTimeout:
        logger.warning(
            "%s_listing: slots wall-clock timeout after %ss — closing browser context",
            source,
            int(wall),
        )
        if _radar_stage_log_enabled():
            logger.info(
                "fetch:%s stage=goto elapsed=%.1fs TIMEOUT → wall-clock kill",
                source,
                wall,
            )
        _abort_playwright_worker()
        raise HtmlFetchError(f"wall-clock timeout after {int(wall)}s ({source})")


def fetch_listing_html_browser_slots(
    source: str,
    url: str,
    *,
    user_agent: str,
    timeout_sec: float = 45.0,
    proxy_urls: list[str] | None = None,
) -> str:
    """Browser fetch с перебором живых слотов (O63 YouDo — без httpx fallback)."""
    if not _on_playwright_thread():
        return _playwright_sync(
            fetch_listing_html_browser_slots,
            source,
            url,
            user_agent=user_agent,
            timeout_sec=timeout_sec,
            proxy_urls=proxy_urls,
        )
    if proxy_urls is not None:
        slots = proxy_urls
    elif source == "youdo" and youdo_one_slot_per_cycle():
        primary = exchange_primary_proxy_url("youdo")
        alive = exchange_alive_proxy_urls(source)
        if primary and alive:
            # O177: primary first; on timeout retry other alive slots (up to cap).
            slots = [primary] + [u for u in alive if u != primary]
            slots = slots[: _youdo_slot_retry_max()]
        elif primary:
            slots = [primary]
        else:
            slots = []
    else:
        slots = exchange_alive_proxy_urls(source)
    if not slots:
        raise HtmlFetchError(f"{source}: no alive proxy slots for browser")
    last_exc: HtmlFetchError | None = None
    slots_tried = 0
    retry_cap = _youdo_slot_retry_max() if source == "youdo" else 1
    for proxy_url in slots:
        slots_tried += 1
        hint = _hint_from_url(proxy_url) or "direct"
        use_ephemeral = (
            source == "youdo"
            and slots_tried > 1
            and _youdo_ephemeral_on_slot_retry()
        )
        if source == "youdo" and slots_tried > 1:
            try:
                from youdo_parser import log_youdo_trace_path

                log_youdo_trace_path(
                    None,
                    "slot_retry",
                    slot=slots_tried,
                    proxy_hint=hint,
                    ephemeral=1 if use_ephemeral else 0,
                )
            except Exception:
                pass
        try:
            if source == "youdo":
                if youdo_ephemeral() or use_ephemeral:
                    return _fetch_youdo_ephemeral(
                        url,
                        user_agent=user_agent,
                        timeout_sec=timeout_sec,
                        proxy_url=proxy_url,
                        stage="listing",
                        slot_attempt=slots_tried,
                    )
                return fetch_youdo_html_browser(
                    url,
                    user_agent=user_agent,
                    timeout_sec=timeout_sec,
                    proxy_url=proxy_url,
                    stage="listing",
                    slot_attempt=slots_tried,
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
            if source == "youdo" and youdo_one_slot_per_cycle():
                if (
                    _is_youdo_slot_retryable(exc)
                    and slots_tried < min(len(slots), retry_cap)
                ):
                    _abort_playwright_worker()
                    continue
                break
    detail = str(last_exc) if last_exc else "unknown"
    raise HtmlFetchError(f"{source}: all browser slots failed ({len(slots)}): {detail}")


def reset_browser_contexts_for_tests() -> None:
    if not _on_playwright_thread():
        _playwright_sync(reset_browser_contexts_for_tests)
        return
    reset_youdo_warm_state_for_tests()
    with _LOCK:
        for key in list(_CONTEXTS):
            _close_context(key)


def reset_playwright_thread_for_tests() -> None:
    """Tear down dedicated Playwright thread between unit tests."""
    _abort_playwright_worker()
