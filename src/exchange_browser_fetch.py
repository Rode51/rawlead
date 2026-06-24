"""Playwright persistent context per proxy slot — FL/Kwork listing (O99)."""

from __future__ import annotations

import asyncio
import contextvars
import json
import logging
import os
import random
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from pathlib import Path
from dataclasses import dataclass
from typing import Any, NamedTuple

from config import normalize_proxy_url
from exchange_proxy import (
    _hint_from_url,
    exchange_alive_proxy_urls,
    exchange_primary_proxy_url,
    fl_browser_dead_proxy_fail,
    fl_dc_alive_urls,
    is_proxy_connection_error,
    youdo_proxy_in_dc_pool,
    youdo_ru_alive_urls,
)
from html_fetch import HtmlFetchError, _playwright_proxy

logger = logging.getLogger(__name__)

_youdo_fetch_tier_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "youdo_fetch_tier", default="dc"
)

_LOCK = threading.Lock()
_FETCH_LOCKS_GUARD = threading.Lock()
_FETCH_LOCKS: dict[str, threading.Lock] = {}
_CONTEXTS: dict[str, Any] = {}
_PLAYWRIGHT = None
_YOUDO_PW = None
_PW_LOCK = threading.Lock()
_YOUDO_PW_LOCK = threading.Lock()
_PW_THREAD_PREFIX = "rawlead-playwright"
_PW_EXECUTOR: ThreadPoolExecutor | None = None
_PW_EXECUTOR_LOCK = threading.Lock()


def _on_playwright_thread() -> bool:
    return threading.current_thread().name.startswith(_PW_THREAD_PREFIX)


def _clear_stale_asyncio_loop() -> None:
    """Playwright sync API rejects threads with a running asyncio loop (O190 t0e)."""
    asyncio.set_event_loop(None)


def _pw_thread_initializer() -> None:
    _clear_stale_asyncio_loop()


def _pw_executor() -> ThreadPoolExecutor:
    global _PW_EXECUTOR
    with _PW_EXECUTOR_LOCK:
        if _PW_EXECUTOR is None:
            _PW_EXECUTOR = ThreadPoolExecutor(
                max_workers=1,
                thread_name_prefix=_PW_THREAD_PREFIX,
                initializer=_pw_thread_initializer,
            )
        return _PW_EXECUTOR


def _playwright_sync(func, /, *args, **kwargs):
    if _on_playwright_thread():
        _clear_stale_asyncio_loop()
        return func(*args, **kwargs)
    _clear_stale_asyncio_loop()

    def _run() -> Any:
        _clear_stale_asyncio_loop()
        return func(*args, **kwargs)

    fut = _pw_executor().submit(_run)
    return fut.result()


def _playwright_sync_timed(func, timeout_sec: float):
    if _on_playwright_thread():
        _clear_stale_asyncio_loop()
        return func()
    _clear_stale_asyncio_loop()

    def _run() -> Any:
        _clear_stale_asyncio_loop()
        return func()

    fut = _pw_executor().submit(_run)
    return fut.result(timeout=max(float(timeout_sec), 1.0))


def _youdo_wall_clock_teardown(source: str) -> None:
    """On YouDo wall timeout — kill camoufox subprocess orphans (O262h / O254)."""
    if (source or "").strip().lower() == "youdo":
        try:
            youdo_browser_teardown()
        except Exception:
            _abort_playwright_worker()
    else:
        _abort_playwright_worker()


def _abort_playwright_worker() -> None:
    """Drop a hung Playwright worker; next fetch spawns a fresh dedicated thread."""
    global _PW_EXECUTOR, _PLAYWRIGHT, _YOUDO_PW
    _WARMED_YOUDO_KEYS.clear()
    with _LOCK:
        _CONTEXTS.clear()
    with _PW_EXECUTOR_LOCK:
        if _PW_EXECUTOR is not None:
            _PW_EXECUTOR.shutdown(wait=False, cancel_futures=True)
            _PW_EXECUTOR = None
    with _YOUDO_PW_LOCK:
        if _YOUDO_PW is not None:
            try:
                _YOUDO_PW.stop()
            except Exception:
                pass
            _YOUDO_PW = None
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
    "patchright",
)

_YOUDO_STALE_BROWSER_MARKERS = (
    "camoufox",
    "youdo_fetch_worker",
    "youdo_sticky_worker",
    "playwright/firefox",
    "firefox/firefox",
    "geckodriver",
)

_YOUDO_STICKY_PROC: subprocess.Popen[str] | None = None
_YOUDO_STICKY_PROXY: str | None = None
_YOUDO_STICKY_LAST_VALID: float = 0.0
_YOUDO_SESSION_LISTING_OK = False
_YOUDO_STICKY_LOCK = threading.Lock()
_YOUDO_SOFT_SP_FETCH_FAIL = False
_YOUDO_SOFT_SP_LOCK = threading.Lock()
_YOUDO_RU_BURST_DAY_KEY = "youdo_ru_burst_day"
_YOUDO_RU_BURST_COUNT_KEY = "youdo_ru_burst_count"

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


def youdo_persistent_profile_enabled() -> bool:
    """O267: Camoufox user_data_dir per DC proxy (data/youdo_{hint}/)."""
    return os.getenv("YOUDO_PERSISTENT_PROFILE", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def youdo_sticky_after_ok_enabled() -> bool:
    """O268: graduate slot1 from ephemeral to sticky after first large listing HTML."""
    return os.getenv("YOUDO_STICKY_AFTER_OK", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _youdo_session_listing_ok() -> bool:
    return _YOUDO_SESSION_LISTING_OK


def _maybe_mark_youdo_session_listing_ok(html: str) -> None:
    global _YOUDO_SESSION_LISTING_OK
    if len((html or "").strip()) > 100_000:
        _YOUDO_SESSION_LISTING_OK = True


def _youdo_profile_generation() -> str:
    return os.getenv("YOUDO_PROFILE_GENERATION", "").strip()


def _youdo_disk_profile_has_session(proxy_url: str) -> bool:
    """O269: Camoufox user_data_dir with cookies = session (survives fetch_every_n skips).

    Sticky worker reloads the same on-disk profile between cycles. Ephemeral-first (O268)
    is only for empty/wiped profiles — one-shot subprocess cannot warm-reload.
    """
    if not youdo_persistent_profile_enabled():
        return False
    proxy = (proxy_url or "").strip()
    if not proxy:
        return False
    return _youdo_profile_has_cookies(_youdo_persistent_profile_dir(proxy))


def _youdo_ephemeral_first_slot1(*, slots_tried: int, proxy_url: str = "") -> bool:
    """O268 cold goto on slot1 until session ok; O269 skips when disk profile has cookies."""
    if slots_tried != 1:
        return False
    if not (_youdo_is_camoufox() and youdo_persistent_profile_enabled()):
        return False
    if not youdo_sticky_after_ok_enabled():
        return True
    if _youdo_disk_profile_has_session(proxy_url):
        return False
    return not _youdo_session_listing_ok()


def _youdo_should_use_sticky_listing(
    *,
    slots_tried: int,
    use_ephemeral: bool,
    proxy_url: str = "",
) -> bool:
    if not (_youdo_is_camoufox() and _youdo_sticky_session_enabled()):
        return False
    if youdo_ephemeral() or use_ephemeral:
        return False
    if _youdo_ephemeral_first_slot1(slots_tried=slots_tried, proxy_url=proxy_url):
        return False
    return True


def _youdo_soft_servicepipe_ban_enabled() -> bool:
    return os.getenv("YOUDO_SOFT_SERVICEPIPE_BAN", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def youdo_last_fetch_was_soft_servicepipe() -> bool:
    """True when last listing fetch failed on first DC ServicePipe (O267 soft fail)."""
    with _YOUDO_SOFT_SP_LOCK:
        return _YOUDO_SOFT_SP_FETCH_FAIL


def _mark_youdo_soft_sp_fetch_fail() -> None:
    global _YOUDO_SOFT_SP_FETCH_FAIL
    with _YOUDO_SOFT_SP_LOCK:
        _YOUDO_SOFT_SP_FETCH_FAIL = True


def _clear_youdo_soft_sp_fetch_fail() -> None:
    global _YOUDO_SOFT_SP_FETCH_FAIL
    with _YOUDO_SOFT_SP_LOCK:
        _YOUDO_SOFT_SP_FETCH_FAIL = False


def _youdo_repo_data_dir() -> Path:
    raw = os.getenv("YOUDO_PROFILE_DATA_DIR", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent.parent / "data"


def _youdo_persistent_profile_dir(proxy_url: str) -> Path:
    hint = _hint_from_url(proxy_url) or "direct"
    gen = _youdo_profile_generation()
    suffix = f"_g{gen}" if gen else ""
    return _youdo_repo_data_dir() / f"youdo_{hint}{suffix}"


def _youdo_profile_has_cookies(profile_dir: Path) -> bool:
    cookies_db = profile_dir / "cookies.sqlite"
    try:
        return cookies_db.is_file() and cookies_db.stat().st_size > 512
    except OSError:
        return False


def _wipe_youdo_persistent_profiles(
    *,
    proxy_url: str | None = None,
    reason: str = "",
) -> int:
    wiped = 0
    if proxy_url:
        profile = _youdo_persistent_profile_dir(proxy_url)
        if profile.is_dir():
            shutil.rmtree(profile, ignore_errors=True)
            wiped = 1
            if reason == "sp":
                logger.info(
                    "fetch:youdo profile_wiped=sp dir=%s",
                    profile.name,
                )
            else:
                logger.info("fetch:youdo wiped persistent profile %s", profile.name)
        return wiped
    data_dir = _youdo_repo_data_dir()
    if not data_dir.is_dir():
        return 0
    for profile in data_dir.glob("youdo_*"):
        if profile.is_dir():
            shutil.rmtree(profile, ignore_errors=True)
            wiped += 1
    if wiped:
        logger.info("fetch:youdo wiped %d persistent profile dir(s)", wiped)
    return wiped


def youdo_warm_home_enabled() -> bool:
    """O177: warm youdo.com/ often hangs 45s on VPS proxy — listing SSR needs no warm."""
    return os.getenv("YOUDO_WARM_HOME", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def youdo_list_view_click_enabled() -> bool:
    """O262: YouDo default UI is map — click «Показать списком» before reading cards."""
    return os.getenv("YOUDO_LIST_VIEW_CLICK", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _youdo_list_view_force_min_html() -> int:
    """O262b: force list-view click when map HTML is large but no task cards."""
    raw = os.getenv("YOUDO_LIST_VIEW_FORCE_MIN_HTML", "50000").strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 50_000


def _youdo_list_view_allow_class_fallback() -> bool:
    """O262d: allow class:list as last-resort selector (default on until prod verified)."""
    return os.getenv("YOUDO_LIST_VIEW_ALLOW_CLASS_FALLBACK", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


@dataclass
class _YoudoListViewResult:
    clicked: bool
    selector: str
    data_id_count: int
    debug_path: str = ""
    html_len: int = 0
    force: bool = False
    pass_n: int = 1
    selector_tier: str = ""
    target_snip: str = ""


class _YoudoListViewClickResult(NamedTuple):
    clicked: bool
    selector: str
    selector_tier: str
    target_snip: str


class _YoudoCamoufoxFetchResult(NamedTuple):
    html: str
    list_view: _YoudoListViewResult


def _youdo_listing_goto_timeout_ms(timeout_sec: float) -> int:
    raw = os.getenv("YOUDO_GOTO_TIMEOUT_SEC", "").strip()
    if raw:
        try:
            return max(int(float(raw) * 1000), 5000)
        except ValueError:
            pass
    base = float(timeout_sec)
    if base < 120.0 and _youdo_goto_wait_until() in ("load", "networkidle"):
        base = 150.0
    return max(int(base * 1000), 5000)


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


def _youdo_dc_retry_max() -> int:
    from exchange_proxy import _youdo_dc_retry_max as dc_max

    return dc_max()


def _youdo_ru_retry_max() -> int:
    from exchange_proxy import _youdo_ru_retry_max as ru_max

    return ru_max()


def _youdo_fetch_tier_plan() -> list[tuple[str, str]]:
    """O260: [(proxy_url, tier)] — DC phase, optional dc_hard_reset, then RU fallback."""
    from exchange_proxy import youdo_dc_alive_urls, youdo_listing_slot_urls

    plan: list[tuple[str, str]] = []
    dc_cap = _youdo_dc_retry_max()
    for url in youdo_listing_slot_urls(include_ru=False)[:dc_cap]:
        plan.append((url, "dc"))
    return plan


def _youdo_log_tier_attempt(tier: str, proxy_url: str, slot_n: int) -> None:
    hint = _hint_from_url(proxy_url) or "direct"
    logger.info(
        "fetch:youdo tier=%s proxy_hint=%s slot=%d",
        tier,
        hint,
        slot_n,
    )


def _fl_slot_retry_max() -> int:
    raw = os.getenv("FL_SLOT_RETRY_MAX", "1").strip()
    try:
        return max(1, min(int(raw), 8))
    except ValueError:
        return 1


def fl_hard_reset_on_ban_enabled() -> bool:
    return os.getenv("FL_HARD_RESET_ON_BAN", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def fl_rotate_user_agent_enabled() -> bool:
    return os.getenv("FL_ROTATE_UA", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def fl_listing_user_agent(cfg_ua: str = "") -> str:
    """Pick browser UA for FL listing — rotate pool when FL_ROTATE_UA=1 (O222)."""
    if fl_rotate_user_agent_enabled():
        return pick_browser_user_agent("")
    return pick_browser_user_agent(cfg_ua)


def _wipe_fl_profile_dirs() -> int:
    root = _data_root()
    wiped = 0
    if not root.is_dir():
        return 0
    for path in root.glob("fl_*"):
        if path.is_dir():
            try:
                shutil.rmtree(path, ignore_errors=True)
                wiped += 1
            except OSError as exc:
                logger.warning("fetch:fl hard_reset wipe %s failed: %s", path.name, exc)
    return wiped


def fl_hard_reset(
    *,
    reason: str = "",
    storage: object | None = None,
    set_restart_source: bool = True,
) -> None:
    """Full FL browser teardown — new visitor on next cycle (O222/O233).

    O257: set_restart_source=False when called from soft-antibot / parsed-zero paths
    with subprocess enabled — teardown is inline, deferred flag only causes a no-op
    context close on the next cycle and extends the restart loop.
    """
    close_all_browser_contexts()
    _abort_playwright_worker()
    wiped = _wipe_fl_profile_dirs()
    cleared = 0
    try:
        from exchange_proxy import clear_fl_source_bans

        cleared = clear_fl_source_bans()
    except Exception as exc:
        logger.warning("fetch:fl hard_reset clear bans failed: %s", exc)
    logger.info(
        "fetch:fl hard_reset reason=%s profiles_wiped=%s bans_cleared=%s set_restart=%s",
        (reason or "unknown")[:200],
        wiped,
        cleared,
        set_restart_source,
    )
    if not set_restart_source:
        return
    st = storage
    if st is None:
        try:
            from exchange_proxy import _storage as _proxy_storage

            st = _proxy_storage()
        except Exception:
            st = None
    if st is not None:
        try:
            st.set_setting("restart_source_fl", "1")
        except Exception as exc:
            logger.debug("fetch:fl hard_reset restart_source skipped: %s", exc)


def _is_fl_dead_proxy_error(exc: BaseException) -> bool:
    return is_proxy_connection_error(exc)


def _youdo_max_dc_bans_per_fetch() -> int:
    from exchange_proxy import _youdo_max_dc_bans_per_fetch

    return _youdo_max_dc_bans_per_fetch()


def _youdo_browser_slot_fail_limited(
    proxy_url: str,
    exc: HtmlFetchError,
    *,
    dc_bans_this_fetch: list[int],
    skip_slot_ban: bool = False,
) -> bool:
    """Ban YouDo slot; return False when DC ban limit reached (O261)."""
    if skip_slot_ban:
        return True
    if youdo_proxy_in_dc_pool(proxy_url):
        if dc_bans_this_fetch[0] >= _youdo_max_dc_bans_per_fetch():
            try:
                from exchange_proxy import youdo_dc_alive_urls, youdo_dc_pool_size

                dc_alive_n = len(youdo_dc_alive_urls())
                dc_total = youdo_dc_pool_size()
                logger.info(
                    "fetch:youdo stage=dc_ban_limit_reached bans_this_fetch=%d dc_alive=%d/%d",
                    dc_bans_this_fetch[0],
                    dc_alive_n,
                    dc_total,
                )
            except Exception:
                pass
            return False
        dc_bans_this_fetch[0] += 1
    _youdo_browser_slot_fail(proxy_url, exc)
    return True


def _youdo_browser_slot_fail(proxy_url: str, exc: HtmlFetchError) -> None:
    try:
        from exchange_proxy import youdo_browser_slot_fail

        youdo_browser_slot_fail(
            proxy_url,
            reason=f"browser:{str(exc)[:120]}",
        )
    except Exception as ban_exc:
        logger.debug("fetch:youdo browser ban skipped: %s", ban_exc)


def _fl_browser_dead_proxy_fail(proxy_url: str, exc: HtmlFetchError) -> bool:
    try:
        return fl_browser_dead_proxy_fail(
            proxy_url,
            reason=f"dead_proxy:{str(exc)[:80]}",
        )
    except Exception as ban_exc:
        logger.debug("fetch:fl dead_proxy ban skipped: %s", ban_exc)
        return False


def _fl_browser_antibot_fail(
    proxy_url: str,
    exc: HtmlFetchError,
    *,
    storage: object | None = None,
) -> None:
    try:
        from exchange_proxy import _FL_RES_BAN_SOURCE, _ban_url, _urls_for_source

        _, ban_source, _ = _urls_for_source("fl")
        if ban_source != _FL_RES_BAN_SOURCE:
            _ban_url(
                proxy_url,
                source=ban_source,
                reason=f"browser:{str(exc)[:120]}",
            )
    except Exception as ban_exc:
        logger.debug("fetch:fl browser ban skipped: %s", ban_exc)
    if fl_hard_reset_on_ban_enabled():
        fl_hard_reset(
            reason=str(exc),
            storage=storage,
            set_restart_source=not fl_listing_subprocess_enabled(),
        )


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
    """Slot 1: networkidle (SPA); slot 2+: domcontentloaded + selector wait (O185 t6c P2)."""
    if slot_attempt > 1:
        raw = os.getenv("YOUDO_RETRY_GOTO_WAIT_UNTIL", "domcontentloaded").strip().casefold()
        if raw in ("commit", "domcontentloaded", "load", "networkidle"):
            return raw
        return "domcontentloaded"
    return _youdo_goto_wait_until()


def _youdo_headless() -> bool:
    return os.getenv("YOUDO_HEADLESS", "1").strip().lower() not in ("0", "false", "no")


def _youdo_lean_route_on_attempt(slot_attempt: int) -> bool:
    """Slot 1 needs full assets for SPA hydration; lean only on retry when opted in."""
    if slot_attempt <= 1:
        return False
    return os.getenv("YOUDO_LEAN_ON_RETRY", "0").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _youdo_stealth_enabled() -> bool:
    return os.getenv("YOUDO_STEALTH", "1").strip().lower() in ("1", "true", "yes")


def _youdo_chromium_args() -> list[str]:
    if not _youdo_stealth_enabled():
        return []
    return ["--disable-blink-features=AutomationControlled"]


def _apply_youdo_stealth(ctx: Any) -> None:
    if not _youdo_stealth_enabled() or _youdo_is_camoufox():
        return
    try:
        ctx.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = window.chrome || { runtime: {} };
            Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU', 'ru', 'en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', {
              get: () => [1, 2, 3, 4, 5],
            });
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) =>
              parameters.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : originalQuery(parameters);
            """
        )
    except Exception:
        pass


def _is_youdo_slot_retryable(exc: HtmlFetchError) -> bool:
    if _is_timeout_error(exc):
        return True
    msg = str(exc).casefold()
    markers = (
        "antibot",
        "servicepipe",
        "spa shell",
        "короткий",
        "cloudflare",
        "forbidden",
        "empty html",
        "403",
        "proxy",
        "connection_refused",
        "connection refused",
        "ns_error",
        "econnrefused",
        "connection closed",
        "connection_closed",
        "tunnel",
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


def _youdo_post_goto_jitter_ms() -> tuple[int, int]:
    raw = os.getenv("YOUDO_POST_GOTO_JITTER_MS", "1500,3500").strip()
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if len(parts) >= 2:
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            pass
    return 1500, 3500


def _youdo_post_goto_jitter_sleep() -> None:
    lo, hi = _youdo_post_goto_jitter_ms()
    time.sleep(random.randint(lo, hi) / 1000.0)


_YOUDO_LISTING_CARD_SELECTOR = 'a[data-id][href*="/t"]'
_YOUDO_LISTING_SHELL_SELECTORS = (_YOUDO_LISTING_CARD_SELECTOR, ".task-list")
_YOUDO_LIST_VIEW_LINK_TEXTS = ("Показать списком",)


def _youdo_html_has_task_cards(html: str) -> bool:
    low = (html or "").casefold()
    if re.search(r"/t\d+", html or ""):
        return True
    return "data-id" in low and 'href="/t' in low.replace("'", '"')


def _youdo_html_is_servicepipe(html: str) -> bool:
    """ServicePipe /exhkqyad interstitial before YouDo SPA (O262e)."""
    stripped = (html or "").strip()
    if not stripped or len(stripped) > 4000:
        return False
    low = stripped.casefold()
    if "servicepipe" in low:
        return True
    return "exhkqyad" in low and "__next" not in low and "data-id" not in low


def _youdo_fetch_tier() -> str:
    env_tier = os.getenv("YOUDO_FETCH_TIER", "").strip()
    if env_tier:
        return env_tier
    return _youdo_fetch_tier_ctx.get()


def _youdo_servicepipe_early_ru_enabled() -> bool:
    return os.getenv("YOUDO_SERVICEPIPE_EARLY_RU", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _is_youdo_servicepipe_error(exc: BaseException) -> bool:
    return "servicepipe" in str(exc).casefold()


def _youdo_servicepipe_wait_sec(*, tier: str | None = None) -> float:
    t = (tier or _youdo_fetch_tier()).strip() or "dc"
    if t.startswith("ru"):
        raw = os.getenv("YOUDO_SERVICEPIPE_WAIT_SEC_RU", "90").strip()
        try:
            return max(0.0, float(raw))
        except ValueError:
            return 90.0
    raw = os.getenv("YOUDO_SERVICEPIPE_WAIT_SEC", "90").strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 90.0


def _youdo_servicepipe_wait_ms(*, tier: str | None = None) -> int:
    return int(_youdo_servicepipe_wait_sec(tier=tier) * 1000)


def _youdo_page_html(page: Any) -> str:
    try:
        raw = page.content()
        return raw if isinstance(raw, str) else ""
    except Exception:
        return ""


async def _youdo_page_html_async(page: Any) -> str:
    try:
        raw = await page.content()
        return raw if isinstance(raw, str) else ""
    except Exception:
        return ""


def _youdo_wait_servicepipe_clear(page: Any, *, timeout_ms: int | None = None, tier: str | None = None) -> bool:
    """Wait for ServicePipe challenge to redirect/hydrate. True = clear or never was SP."""
    if timeout_ms is None:
        timeout_ms = _youdo_servicepipe_wait_ms(tier=tier)

    def _listing_ready(h: str) -> bool:
        if _youdo_html_has_task_cards(h):
            return True
        if len((h or "").strip()) >= 8000 and not _youdo_html_is_servicepipe(h):
            return True
        return False

    html = _youdo_page_html(page)
    if _listing_ready(html):
        return True
    if not _youdo_html_is_servicepipe(html) and len(html.strip()) >= 4000:
        return True
    logger.info(
        "fetch:youdo stage=servicepipe_wait html_len=%s timeout_sec=%s",
        len(html),
        timeout_ms // 1000,
    )
    t0 = time.monotonic()
    while int((time.monotonic() - t0) * 1000) < timeout_ms:
        try:
            page.wait_for_timeout(2000)
            html = _youdo_page_html(page)
        except Exception:
            break
        if _listing_ready(html):
            logger.info(
                "fetch:youdo stage=servicepipe_cleared html_len=%s",
                len(html),
            )
            return True
    final_len = len(_youdo_page_html(page))
    logger.info(
        "fetch:youdo stage=servicepipe_wait_fail html_len=%s",
        final_len,
    )
    return False


async def _youdo_wait_servicepipe_clear_async(
    page: Any, *, timeout_ms: int | None = None, tier: str | None = None
) -> bool:
    if timeout_ms is None:
        timeout_ms = _youdo_servicepipe_wait_ms(tier=tier)

    def _listing_ready(h: str) -> bool:
        if _youdo_html_has_task_cards(h):
            return True
        if len((h or "").strip()) >= 8000 and not _youdo_html_is_servicepipe(h):
            return True
        return False

    html = await _youdo_page_html_async(page)
    if _listing_ready(html):
        return True
    if not _youdo_html_is_servicepipe(html) and len(html.strip()) >= 4000:
        return True
    logger.info(
        "fetch:youdo stage=servicepipe_wait html_len=%s timeout_sec=%s",
        len(html),
        timeout_ms // 1000,
    )
    t0 = time.monotonic()
    while int((time.monotonic() - t0) * 1000) < timeout_ms:
        try:
            await page.wait_for_timeout(2000)
            html = await _youdo_page_html_async(page)
        except Exception:
            break
        if _listing_ready(html):
            logger.info(
                "fetch:youdo stage=servicepipe_cleared html_len=%s",
                len(html),
            )
            return True
    final_len = len(await _youdo_page_html_async(page))
    logger.info(
        "fetch:youdo stage=servicepipe_wait_fail html_len=%s",
        final_len,
    )
    return False


def _youdo_has_listing_cards(page: Any) -> bool:
    try:
        return page.locator(_YOUDO_LISTING_CARD_SELECTOR).count() > 0
    except Exception:
        return False


async def _youdo_has_listing_cards_async(page: Any) -> bool:
    try:
        return await page.locator(_YOUDO_LISTING_CARD_SELECTOR).count() > 0
    except Exception:
        return False


def _log_youdo_list_view_trace(result: _YoudoListViewResult) -> None:
    """O262b/O262c: grep-friendly list_view stage in radar_site.log."""
    try:
        from youdo_parser import log_youdo_trace_path

        fields: dict[str, object] = {
            "clicked": 1 if result.clicked else 0,
            "selector": result.selector or "none",
            "data_id": result.data_id_count,
            "html_len": result.html_len,
            "force": 1 if result.force else 0,
            "pass": result.pass_n,
        }
        if result.selector_tier:
            fields["selector_tier"] = result.selector_tier
        if result.target_snip:
            fields["target_snip"] = result.target_snip
        if result.debug_path:
            fields["debug_path"] = result.debug_path
        log_youdo_trace_path(None, "list_view", **fields)
    except Exception:
        pass


def _youdo_probe_diag_enabled() -> bool:
    """O262k: probe returns raw DC HTML without ingest validation."""
    return os.getenv("YOUDO_PROBE_SKIP_VALIDATE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _youdo_post_goto_list_view_wait(page: Any, *, tier: str | None = None) -> None:
    """O262c: SPA hydrate before map→list click (networkidle cap 15s, else 3s)."""
    try:
        page.wait_for_load_state("networkidle", timeout=15_000)
    except Exception:
        try:
            page.wait_for_timeout(3000)
        except Exception:
            pass
    if not _youdo_wait_servicepipe_clear(page, tier=tier):
        raise HtmlFetchError("ServicePipe antibot challenge (youdo).")


async def _youdo_post_goto_list_view_wait_async(page: Any, *, tier: str | None = None) -> None:
    try:
        await page.wait_for_load_state("networkidle", timeout=15_000)
    except Exception:
        try:
            await page.wait_for_timeout(3000)
        except Exception:
            pass
    if not await _youdo_wait_servicepipe_clear_async(page, tier=tier):
        raise HtmlFetchError("ServicePipe antibot challenge (youdo).")


def _youdo_data_id_count(page: Any) -> int:
    try:
        return page.locator(_YOUDO_LISTING_CARD_SELECTOR).count()
    except Exception:
        return 0


async def _youdo_data_id_count_async(page: Any) -> int:
    try:
        return await page.locator(_YOUDO_LISTING_CARD_SELECTOR).count()
    except Exception:
        return 0


def _youdo_list_view_selector_tier(sel_name: str) -> str:
    return "fallback" if sel_name == "class:list" else "primary"


def _youdo_list_view_target_snip(loc: Any) -> str:
    try:
        text = loc.inner_text(timeout=1000) or ""
    except Exception:
        text = ""
    return text.strip()[:40]


async def _youdo_list_view_target_snip_async(loc: Any) -> str:
    try:
        text = await loc.inner_text(timeout=1000) or ""
    except Exception:
        text = ""
    return text.strip()[:40]


def _youdo_list_view_target_has_spiskom(loc: Any) -> bool:
    try:
        text = (loc.inner_text(timeout=1000) or "").casefold()
        href = (loc.get_attribute("href") or "").casefold()
        return "списком" in text or "списком" in href
    except Exception:
        return False


async def _youdo_list_view_target_has_spiskom_async(loc: Any) -> bool:
    try:
        text = (await loc.inner_text(timeout=1000) or "").casefold()
        href = (await loc.get_attribute("href") or "").casefold()
        return "списком" in text or "списком" in href
    except Exception:
        return False


def _youdo_verify_list_view_click(page: Any, loc: Any) -> bool:
    if _youdo_data_id_count(page) > 0:
        return True
    return _youdo_list_view_target_has_spiskom(loc)


async def _youdo_verify_list_view_click_async(page: Any, loc: Any) -> bool:
    if await _youdo_data_id_count_async(page) > 0:
        return True
    return await _youdo_list_view_target_has_spiskom_async(loc)


def _youdo_list_view_selector_attempts(page: Any) -> list[tuple[str, Any]]:
    attempts: list[tuple[str, Any]] = [
        ("text:Показать списком", page.get_by_text("Показать списком", exact=False).first),
        (
            "role:link:списком",
            page.get_by_role("link", name=re.compile("списком", re.I)).first,
        ),
        (
            "filter:списком",
            page.locator("a,button").filter(has_text=re.compile("списком", re.I)).first,
        ),
    ]
    if _youdo_list_view_allow_class_fallback():
        attempts.append(
            ("class:list", page.locator('[class*="list"]').locator("a").first),
        )
    return attempts


def _youdo_try_list_view_click(page: Any, *, force: bool) -> _YoudoListViewClickResult:
    for sel_name, loc in _youdo_list_view_selector_attempts(page):
        try:
            if force:
                if loc.count() <= 0:
                    continue
                loc.click(timeout=5000, force=True)
            elif loc.is_visible(timeout=2000):
                loc.click(timeout=5000)
            else:
                continue
            page.wait_for_timeout(1500)
            if not _youdo_verify_list_view_click(page, loc):
                logger.info(
                    "fetch:youdo stage=list_view_click_reject selector=%r force=%s",
                    sel_name,
                    force,
                )
                continue
            tier = _youdo_list_view_selector_tier(sel_name)
            snip = _youdo_list_view_target_snip(loc)
            logger.info(
                "fetch:youdo stage=list_view_click selector=%r tier=%s force=%s",
                sel_name,
                tier,
                force,
            )
            return _YoudoListViewClickResult(True, sel_name, tier, snip)
        except Exception:
            continue
    return _YoudoListViewClickResult(False, "none", "", "")


async def _youdo_try_list_view_click_async(page: Any, *, force: bool) -> _YoudoListViewClickResult:
    for sel_name, loc in _youdo_list_view_selector_attempts(page):
        try:
            if force:
                if await loc.count() <= 0:
                    continue
                await loc.click(timeout=5000, force=True)
            elif await loc.is_visible(timeout=2000):
                await loc.click(timeout=5000)
            else:
                continue
            await page.wait_for_timeout(1500)
            if not await _youdo_verify_list_view_click_async(page, loc):
                logger.info(
                    "fetch:youdo stage=list_view_click_reject selector=%r force=%s",
                    sel_name,
                    force,
                )
                continue
            tier = _youdo_list_view_selector_tier(sel_name)
            snip = await _youdo_list_view_target_snip_async(loc)
            logger.info(
                "fetch:youdo stage=list_view_click selector=%r tier=%s force=%s",
                sel_name,
                tier,
                force,
            )
            return _YoudoListViewClickResult(True, sel_name, tier, snip)
        except Exception:
            continue
    return _YoudoListViewClickResult(False, "none", "", "")


def _youdo_pass1_from_list_view_out(
    list_view_out: list[_YoudoListViewResult] | None,
) -> _YoudoListViewResult | None:
    if not list_view_out:
        return None
    for item in list_view_out:
        if item.pass_n == 1:
            return item
    return None


def _youdo_should_run_list_view_pass2(
    page: Any,
    *,
    list_view_out: list[_YoudoListViewResult] | None = None,
) -> bool:
    """O262c/O262d: second pass when large HTML still has no cards (incl. false pass1 click)."""
    data_id = _youdo_data_id_count(page)
    if data_id > 0:
        return False
    html = ""
    try:
        html = page.content()
    except Exception:
        pass
    min_html = _youdo_list_view_force_min_html()
    if len(html) >= min_html:
        return True
    pass1 = _youdo_pass1_from_list_view_out(list_view_out)
    if (
        pass1
        and pass1.clicked
        and pass1.data_id_count == 0
        and pass1.html_len >= min_html
    ):
        return True
    return False


async def _youdo_should_run_list_view_pass2_async(
    page: Any,
    *,
    list_view_out: list[_YoudoListViewResult] | None = None,
) -> bool:
    data_id = await _youdo_data_id_count_async(page)
    if data_id > 0:
        return False
    html = ""
    try:
        html = await page.content()
    except Exception:
        pass
    min_html = _youdo_list_view_force_min_html()
    if len(html) >= min_html:
        return True
    pass1 = _youdo_pass1_from_list_view_out(list_view_out)
    if (
        pass1
        and pass1.clicked
        and pass1.data_id_count == 0
        and pass1.html_len >= min_html
    ):
        return True
    return False


def _youdo_list_view_attempt(page: Any, *, pass_n: int = 1) -> _YoudoListViewResult:
    """Map→list switch with force path for large HTML without cards (O262/O262b/O262c)."""
    if not youdo_list_view_click_enabled():
        result = _YoudoListViewResult(
            clicked=False,
            selector="disabled",
            data_id_count=0,
            pass_n=pass_n,
        )
        _log_youdo_list_view_trace(result)
        return result

    data_id_before = _youdo_data_id_count(page)
    if data_id_before > 0:
        result = _YoudoListViewResult(
            clicked=False,
            selector="skip_has_cards",
            data_id_count=data_id_before,
            pass_n=pass_n,
        )
        _log_youdo_list_view_trace(result)
        return result

    html = ""
    try:
        html = page.content()
    except Exception:
        pass
    html_len = len(html)
    force = html_len >= _youdo_list_view_force_min_html() and data_id_before == 0
    click_result = _youdo_try_list_view_click(page, force=force)
    clicked = click_result.clicked
    selector = click_result.selector
    if clicked:
        try:
            page.wait_for_selector(_YOUDO_LISTING_CARD_SELECTOR, timeout=15_000)
        except Exception:
            pass
        _youdo_post_goto_jitter_sleep()

    data_id_after = _youdo_data_id_count(page)
    debug_path = ""
    if data_id_after == 0 and (clicked or force):
        try:
            from youdo_parser import _save_listing_html_debug

            snap = html
            if not snap:
                try:
                    snap = page.content()
                except Exception:
                    snap = ""
            debug_path = _save_listing_html_debug(snap, tag="youdo_list_view_fail")
        except Exception:
            pass

    result = _YoudoListViewResult(
        clicked=clicked,
        selector=selector,
        data_id_count=data_id_after,
        debug_path=debug_path,
        html_len=html_len,
        force=force,
        pass_n=pass_n,
        selector_tier=click_result.selector_tier,
        target_snip=click_result.target_snip,
    )
    _log_youdo_list_view_trace(result)
    return result


async def _youdo_list_view_attempt_async(page: Any, *, pass_n: int = 1) -> _YoudoListViewResult:
    if not youdo_list_view_click_enabled():
        result = _YoudoListViewResult(
            clicked=False,
            selector="disabled",
            data_id_count=0,
            pass_n=pass_n,
        )
        _log_youdo_list_view_trace(result)
        return result

    data_id_before = await _youdo_data_id_count_async(page)
    if data_id_before > 0:
        result = _YoudoListViewResult(
            clicked=False,
            selector="skip_has_cards",
            data_id_count=data_id_before,
            pass_n=pass_n,
        )
        _log_youdo_list_view_trace(result)
        return result

    html = ""
    try:
        html = await page.content()
    except Exception:
        pass
    html_len = len(html)
    force = html_len >= _youdo_list_view_force_min_html() and data_id_before == 0
    click_result = await _youdo_try_list_view_click_async(page, force=force)
    clicked = click_result.clicked
    selector = click_result.selector
    if clicked:
        try:
            await page.wait_for_selector(_YOUDO_LISTING_CARD_SELECTOR, timeout=15_000)
        except Exception:
            pass
        _youdo_post_goto_jitter_sleep()

    data_id_after = await _youdo_data_id_count_async(page)
    debug_path = ""
    if data_id_after == 0 and (clicked or force):
        try:
            from youdo_parser import _save_listing_html_debug

            snap = html
            if not snap:
                try:
                    snap = await page.content()
                except Exception:
                    snap = ""
            debug_path = _save_listing_html_debug(snap, tag="youdo_list_view_fail")
        except Exception:
            pass

    result = _YoudoListViewResult(
        clicked=clicked,
        selector=selector,
        data_id_count=data_id_after,
        debug_path=debug_path,
        html_len=html_len,
        force=force,
        pass_n=pass_n,
        selector_tier=click_result.selector_tier,
        target_snip=click_result.target_snip,
    )
    _log_youdo_list_view_trace(result)
    return result


def _youdo_click_list_view_if_needed(page: Any) -> _YoudoListViewResult:
    """Switch map UI to task list when link is visible (O262/O262b)."""
    return _youdo_list_view_attempt(page)


async def _youdo_click_list_view_if_needed_async(page: Any) -> _YoudoListViewResult:
    """Async map→list switch for camoufox listing (O262/O262b)."""
    return await _youdo_list_view_attempt_async(page)


def _youdo_maybe_list_view_pass2(
    page: Any,
    *,
    list_view_out: list[_YoudoListViewResult] | None = None,
) -> None:
    """O262c/O262d: retry map→list when shell wait finished but large HTML still has no cards."""
    if not _youdo_should_run_list_view_pass2(page, list_view_out=list_view_out):
        return
    result2 = _youdo_list_view_attempt(page, pass_n=2)
    if list_view_out is not None:
        list_view_out.append(result2)
    if result2.clicked:
        try:
            page.wait_for_selector(_YOUDO_LISTING_CARD_SELECTOR, timeout=15_000)
        except Exception:
            pass
        _youdo_post_goto_jitter_sleep()


async def _youdo_maybe_list_view_pass2_async(
    page: Any,
    *,
    list_view_out: list[_YoudoListViewResult] | None = None,
) -> None:
    if not await _youdo_should_run_list_view_pass2_async(page, list_view_out=list_view_out):
        return
    result2 = await _youdo_list_view_attempt_async(page, pass_n=2)
    if list_view_out is not None:
        list_view_out.append(result2)
    if result2.clicked:
        try:
            await page.wait_for_selector(_YOUDO_LISTING_CARD_SELECTOR, timeout=15_000)
        except Exception:
            pass
        _youdo_post_goto_jitter_sleep()


def _youdo_wait_listing_ready(
    page: Any,
    listing_timeout_ms: int,
    *,
    list_view_out: list[_YoudoListViewResult] | None = None,
    tier: str | None = None,
) -> None:
    """Wait for SPA task cards (or shell container) before reading HTML (O185 t6c)."""
    if _youdo_probe_diag_enabled():
        try:
            page.wait_for_timeout(3000)
        except Exception:
            pass
        return
    _youdo_post_goto_list_view_wait(page, tier=tier)
    try:
        html = page.content()
    except Exception:
        html = ""
    if _youdo_html_is_servicepipe(html):
        raise HtmlFetchError("ServicePipe antibot challenge (youdo).")
    result = _youdo_list_view_attempt(page, pass_n=1)
    if list_view_out is not None:
        list_view_out.append(result)
    pass2_done = False
    min_html = _youdo_list_view_force_min_html()
    if result.clicked and result.data_id_count == 0 and result.html_len >= min_html:
        _youdo_maybe_list_view_pass2(page, list_view_out=list_view_out)
        pass2_done = True
        if _youdo_data_id_count(page) > 0:
            return
    card_timeout = min(45000, listing_timeout_ms)
    if _youdo_html_is_servicepipe(html):
        raise HtmlFetchError("ServicePipe antibot challenge (youdo).")
    for sel in _YOUDO_LISTING_SHELL_SELECTORS:
        try:
            page.wait_for_selector(sel, timeout=card_timeout)
            page.wait_for_timeout(1500)
            _youdo_post_goto_jitter_sleep()
            if not pass2_done:
                _youdo_maybe_list_view_pass2(page, list_view_out=list_view_out)
            return
        except Exception:
            continue
    page.wait_for_timeout(5000)
    _youdo_post_goto_jitter_sleep()
    if not pass2_done:
        _youdo_maybe_list_view_pass2(page, list_view_out=list_view_out)


async def _youdo_wait_listing_ready_async(
    page: Any,
    listing_timeout_ms: int,
    *,
    list_view_out: list[_YoudoListViewResult] | None = None,
    tier: str | None = None,
) -> None:
    """Async SPA wait for camoufox ephemeral listing (O190 t0g)."""
    if _youdo_probe_diag_enabled():
        try:
            await page.wait_for_timeout(3000)
        except Exception:
            pass
        return
    await _youdo_post_goto_list_view_wait_async(page, tier=tier)
    try:
        html = await page.content()
    except Exception:
        html = ""
    if _youdo_html_is_servicepipe(html):
        raise HtmlFetchError("ServicePipe antibot challenge (youdo).")
    result = await _youdo_list_view_attempt_async(page, pass_n=1)
    if list_view_out is not None:
        list_view_out.append(result)
    pass2_done = False
    min_html = _youdo_list_view_force_min_html()
    if result.clicked and result.data_id_count == 0 and result.html_len >= min_html:
        await _youdo_maybe_list_view_pass2_async(page, list_view_out=list_view_out)
        pass2_done = True
        if await _youdo_data_id_count_async(page) > 0:
            return
    card_timeout = min(45000, listing_timeout_ms)
    if _youdo_html_is_servicepipe(html):
        raise HtmlFetchError("ServicePipe antibot challenge (youdo).")
    for sel in _YOUDO_LISTING_SHELL_SELECTORS:
        try:
            await page.wait_for_selector(sel, timeout=card_timeout)
            await page.wait_for_timeout(1500)
            _youdo_post_goto_jitter_sleep()
            if not pass2_done:
                await _youdo_maybe_list_view_pass2_async(page, list_view_out=list_view_out)
            return
        except Exception:
            continue
    await page.wait_for_timeout(5000)
    _youdo_post_goto_jitter_sleep()
    if not pass2_done:
        await _youdo_maybe_list_view_pass2_async(page, list_view_out=list_view_out)


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


def youdo_browser_backend() -> str:
    """O189 patchright · O190 camoufox — FL/Kwork stay on playwright."""
    raw = os.getenv("YOUDO_BROWSER", "patchright").strip().casefold()
    if raw in ("patchright", "playwright", "camoufox"):
        return raw
    return "patchright"


def _youdo_is_camoufox() -> bool:
    return youdo_browser_backend() == "camoufox"


def _playwright_version_tuple() -> tuple[int, ...]:
    try:
        import playwright
    except ImportError:
        return ()
    parts: list[int] = []
    for seg in str(getattr(playwright, "__version__", "") or "").split(".")[:3]:
        try:
            parts.append(int(seg.split("-")[0]))
        except ValueError:
            break
    return tuple(parts)


def _check_camoufox_playwright_compat() -> None:
    """Camoufox Juggler + playwright>=1.60 → driver crash on Page.uncaughtError (camoufox#617)."""
    if not _youdo_is_camoufox():
        return
    ver = _playwright_version_tuple()
    if ver >= (1, 60, 0):
        raise HtmlFetchError(
            "Camoufox incompatible with playwright>=1.60 (youdo.com JS crashes FF driver). "
            "Pin playwright<1.60 on VPS (pip install 'playwright==1.58.0')."
        )


def _youdo_use_subprocess_worker() -> bool:
    """O194: camoufox listing+detail via youdo_fetch_worker — no sync PW in radar."""
    return youdo_ephemeral() or _youdo_is_camoufox()


def _youdo_browser_launcher(pw: Any) -> Any:
    return pw.firefox if _youdo_is_camoufox() else pw.chromium


def _youdo_launch_extra_kw() -> dict[str, Any]:
    if _youdo_is_camoufox():
        try:
            from camoufox.pkgman import launch_path
        except ImportError as exc:
            raise HtmlFetchError(
                "Camoufox не установлен (pip install camoufox && python -m camoufox fetch)."
            ) from exc
        return {"executable_path": launch_path()}
    stealth_args = _youdo_chromium_args()
    if stealth_args:
        return {"args": stealth_args, "ignore_default_args": ["--enable-automation"]}
    return {}


def _get_playwright():
    if not _on_playwright_thread():
        return _playwright_sync(_get_playwright)
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


def _get_youdo_playwright():
    if not _on_playwright_thread():
        return _playwright_sync(_get_youdo_playwright)
    _clear_stale_asyncio_loop()
    global _YOUDO_PW
    with _YOUDO_PW_LOCK:
        if _YOUDO_PW is not None:
            return _YOUDO_PW
        backend = youdo_browser_backend()
        if backend == "camoufox":
            try:
                from playwright.sync_api import sync_playwright as sync_pw
            except ImportError as exc:
                raise HtmlFetchError(
                    "Playwright не установлен (pip install playwright && playwright install firefox)."
                ) from exc
        elif backend == "patchright":
            try:
                from patchright.sync_api import sync_playwright as sync_pw
            except ImportError as exc:
                raise HtmlFetchError(
                    "Patchright не установлен (pip install patchright && patchright install chromium)."
                ) from exc
        else:
            try:
                from playwright.sync_api import sync_playwright as sync_pw
            except ImportError as exc:
                raise HtmlFetchError(
                    "Playwright не установлен (pip install playwright && playwright install chromium)."
                ) from exc
        _YOUDO_PW = sync_pw().start()
        logger.info("youdo:browser backend=%s", backend)
        return _YOUDO_PW


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


async def _abort_youdo_lean_route_async(route) -> None:
    if _should_abort_youdo_request(route.request):
        await route.abort()
    else:
        await route.continue_()


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
    try:
        if not _on_playwright_thread():
            _playwright_sync(close_all_browser_contexts)
            return
        _WARMED_YOUDO_KEYS.clear()
        with _LOCK:
            for key in list(_CONTEXTS):
                _close_context(key)
    except Exception as exc:
        logger.warning("close_all_browser_contexts: %s", exc)


def _is_stale_browser_process(name: str, cmd: str) -> bool:
    blob = f"{name} {cmd}".casefold()
    return any(marker in blob for marker in _STALE_BROWSER_MARKERS)


def _is_stale_youdo_browser_process(name: str, cmd: str) -> bool:
    blob = f"{name} {cmd}".casefold()
    return any(marker in blob for marker in _YOUDO_STALE_BROWSER_MARKERS)


def cleanup_stale_youdo_browser_processes() -> int:
    """Kill orphan camoufox / youdo_fetch_worker PIDs for current user (O254)."""
    import getpass

    import psutil

    user = getpass.getuser().casefold()
    keep = _browser_process_tree() | _youdo_sticky_pids_to_keep()
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
            if not _is_stale_youdo_browser_process(name, cmd):
                continue
            proc.kill()
            killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, ProcessLookupError):
            pass
    if killed:
        logger.info("fetch:youdo browser_cleanup killed=%d", killed)
    return killed


def _youdo_sticky_session_enabled() -> bool:
    return os.getenv("YOUDO_STICKY_SESSION", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _youdo_sticky_max_age_sec() -> float:
    raw = os.getenv("YOUDO_STICKY_MAX_AGE_SEC", "3600").strip()
    try:
        return max(60.0, float(raw))
    except ValueError:
        return 3600.0


def _youdo_sticky_reload_wait_until() -> str:
    return (
        os.getenv("YOUDO_STICKY_RELOAD_WAIT_UNTIL", "domcontentloaded").strip()
        or "domcontentloaded"
    )


def _youdo_sticky_reload_sp_abort_sec() -> float:
    raw = os.getenv("YOUDO_STICKY_RELOAD_SP_ABORT_SEC", "15").strip()
    try:
        return max(3.0, float(raw))
    except ValueError:
        return 15.0


# --- Click-through detail (§ YOUDO-DETAIL-BREAKTHROUGH) ---


def youdo_click_detail_enabled() -> bool:
    return os.getenv("YOUDO_CLICK_DETAIL", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _youdo_click_detail_max() -> int:
    raw = os.getenv("YOUDO_CLICK_DETAIL_MAX", "10").strip()
    try:
        return max(1, min(20, int(raw)))
    except ValueError:
        return 10


def youdo_click_through_details(
    lead_ids: list[str],
    *,
    listing_url: str,
    user_agent: str,
    timeout_sec: float = 60.0,
    proxy_url: str = "",
) -> dict[str, dict[str, Any]]:
    """Send click_through_details command to sticky worker. Returns {ext_id: {body, ...}}."""
    if not _on_playwright_thread():
        return _playwright_sync(
            youdo_click_through_details,
            lead_ids,
            listing_url=listing_url,
            user_agent=user_agent,
            timeout_sec=timeout_sec,
            proxy_url=proxy_url,
        )
    if not lead_ids:
        return {}
    if not _youdo_sticky_session_enabled() or not _youdo_is_camoufox():
        return {}
    capped = lead_ids[:_youdo_click_detail_max()]

    with _fetch_lock("youdo"):
        with _YOUDO_STICKY_LOCK:
            proc = _YOUDO_STICKY_PROC
            if proc is None or proc.poll() is not None:
                return {}
            if not _YOUDO_STICKY_PROXY or _YOUDO_STICKY_PROXY != proxy_url:
                return {}

        req = {
            "cmd": "click_through_details",
            "lead_ids": capped,
            "listing_url": listing_url,
            "timeout": timeout_sec,
        }
        try:
            result = _youdo_sticky_send_json(
                proc,
                req,
                timeout_sec=timeout_sec + 30.0,
            )
        except HtmlFetchError:
            return {}

    results_raw = result.get("results") or {}
    out: dict[str, dict[str, Any]] = {}
    for ext_id, info in results_raw.items():
        if not isinstance(info, dict):
            continue
        body = info.get("body") or ""
        detail_ok = info.get("outcome") in ("ok", "fallback_ok") and len(body) >= 100
        out[str(ext_id)] = {
            "body": body,
            "detail_ok": detail_ok,
            "outcome": info.get("outcome", ""),
            "selector": info.get("selector", ""),
            "clicked": info.get("clicked", 0),
            "ms": info.get("ms", 0),
            "fallback": info.get("fallback", ""),
        }
    return out


def _youdo_ru_burst_max_per_day() -> int:
    raw = os.getenv("YOUDO_RU_BURST_MAX_PER_DAY", "2").strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 2


def _youdo_ru_burst_today_count() -> tuple[str, int]:
    from datetime import date

    from exchange_proxy import _storage

    today = date.today().isoformat()
    try:
        st = _storage()
        day = st.get_setting(_YOUDO_RU_BURST_DAY_KEY, "").strip()
        if day != today:
            return today, 0
        return today, int(st.get_setting(_YOUDO_RU_BURST_COUNT_KEY, "0") or "0")
    except Exception:
        return today, 0


def _youdo_ru_burst_allowed() -> tuple[bool, int, int]:
    max_per = _youdo_ru_burst_max_per_day()
    if max_per <= 0:
        return False, 0, max_per
    _today, count = _youdo_ru_burst_today_count()
    return count < max_per, count, max_per


def _consume_youdo_ru_burst() -> None:
    from exchange_proxy import _storage

    max_per = _youdo_ru_burst_max_per_day()
    today, count = _youdo_ru_burst_today_count()
    new_count = count + 1
    try:
        st = _storage()
        st.set_setting(_YOUDO_RU_BURST_DAY_KEY, today)
        st.set_setting(_YOUDO_RU_BURST_COUNT_KEY, str(new_count))
    except Exception:
        pass
    logger.info("fetch:youdo ru_burst=%d/%d", new_count, max_per)


def _wipe_youdo_profile_on_poison(*, proxy_url: str, html: str, exc: BaseException) -> None:
    if not youdo_persistent_profile_enabled():
        return
    html_len = len((html or "").strip())
    if _is_youdo_servicepipe_error(exc) or html_len < 5000:
        _wipe_youdo_persistent_profiles(proxy_url=proxy_url, reason="sp")


def youdo_sticky_session_warm() -> bool:
    """True when sticky worker holds a recent valid listing session (O266)."""
    with _YOUDO_STICKY_LOCK:
        return _youdo_sticky_is_warm_unlocked()


def _youdo_sticky_is_warm_unlocked(*, proxy_url: str | None = None) -> bool:
    if not _youdo_sticky_session_enabled():
        return False
    proc = _YOUDO_STICKY_PROC
    if proc is None or proc.poll() is not None:
        return False
    if not _YOUDO_STICKY_PROXY:
        return False
    if proxy_url is not None and proxy_url != _YOUDO_STICKY_PROXY:
        return False
    if _YOUDO_STICKY_LAST_VALID <= 0:
        return False
    if time.time() - _YOUDO_STICKY_LAST_VALID > _youdo_sticky_max_age_sec():
        return False
    return True


def _youdo_sticky_teardown_unlocked(*, log_trace: bool = True) -> None:
    global _YOUDO_STICKY_PROC, _YOUDO_STICKY_PROXY, _YOUDO_STICKY_LAST_VALID
    proc = _YOUDO_STICKY_PROC
    proxy_hint = _hint_from_url(_YOUDO_STICKY_PROXY or "") or ""
    _YOUDO_STICKY_PROC = None
    _YOUDO_STICKY_PROXY = None
    _YOUDO_STICKY_LAST_VALID = 0.0
    if proc is not None and proc.poll() is None:
        try:
            _youdo_sticky_send_json(proc, {"cmd": "teardown"}, timeout_sec=15.0)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        try:
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    if log_trace:
        try:
            from youdo_parser import log_youdo_trace_path

            log_youdo_trace_path(
                None,
                "sticky_teardown",
                proxy_hint=proxy_hint,
                warm=0,
            )
        except Exception:
            pass


def _youdo_sticky_teardown(*, log_trace: bool = True) -> None:
    with _YOUDO_STICKY_LOCK:
        _youdo_sticky_teardown_unlocked(log_trace=log_trace)


def _youdo_sticky_read_json_line(
    proc: subprocess.Popen[str],
    *,
    timeout_sec: float,
) -> str:
    if proc.stdout is None:
        raise HtmlFetchError("youdo sticky worker missing stdout pipe")
    box: list[str] = []

    def _reader() -> None:
        try:
            box.append(proc.stdout.readline())  # type: ignore[union-attr]
        except Exception:
            pass

    thread = threading.Thread(target=_reader, daemon=True)
    thread.start()
    thread.join(timeout=max(timeout_sec, 5.0))
    if thread.is_alive():
        raise HtmlFetchError(f"youdo sticky worker timeout after {int(timeout_sec)}s")
    if not box or not box[0].strip():
        if proc.poll() is not None:
            err_tail = ""
            if proc.stderr is not None:
                try:
                    err_tail = (proc.stderr.read() or "")[-500:]
                except Exception:
                    pass
            raise HtmlFetchError(
                f"youdo sticky worker died rc={proc.returncode} {err_tail}".strip()
            )
        raise HtmlFetchError("youdo sticky worker empty response")
    return box[0]


def _youdo_sticky_send_json(
    proc: subprocess.Popen[str],
    payload: dict[str, Any],
    *,
    timeout_sec: float,
) -> dict[str, Any]:
    if proc.stdin is None:
        raise HtmlFetchError("youdo sticky worker missing stdin pipe")
    line = json.dumps(payload, ensure_ascii=False) + "\n"
    proc.stdin.write(line)
    proc.stdin.flush()
    out_line = _youdo_sticky_read_json_line(proc, timeout_sec=timeout_sec)
    try:
        return json.loads(out_line)
    except json.JSONDecodeError as je:
        raise HtmlFetchError(f"youdo sticky worker bad json: {je}") from je


def _youdo_sticky_spawn_worker(*, proxy_url: str, user_agent: str) -> subprocess.Popen[str]:
    worker = (
        Path(__file__).resolve().parent.parent / "scripts" / "youdo_sticky_worker.py"
    )
    env = {
        **os.environ,
        "PYTHONPATH": str(Path(__file__).resolve().parent),
        "YOUDO_STICKY_RELOAD_WAIT_UNTIL": _youdo_sticky_reload_wait_until(),
        "YOUDO_PERSISTENT_PROFILE": (
            "1" if youdo_persistent_profile_enabled() else "0"
        ),
        "YOUDO_STICKY_RELOAD_SP_ABORT_SEC": str(_youdo_sticky_reload_sp_abort_sec()),
        "YOUDO_PROFILE_GENERATION": _youdo_profile_generation(),
    }
    if youdo_persistent_profile_enabled():
        profile_dir = _youdo_persistent_profile_dir(proxy_url)
        env["YOUDO_PROFILE_DATA_DIR"] = str(_youdo_repo_data_dir())
    cmd = [
        sys.executable,
        str(worker),
        "--proxy",
        proxy_url,
        "--user-agent",
        user_agent,
    ]
    return subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env,
    )


def _youdo_sticky_start_stderr_drain(proc: subprocess.Popen[str]) -> None:
    """Prevent sticky worker stderr pipe fill (O269)."""
    if proc.stderr is None:
        return

    def _drain() -> None:
        try:
            for _ in proc.stderr:
                pass
        except Exception:
            pass

    threading.Thread(
        target=_drain,
        daemon=True,
        name="youdo-sticky-stderr",
    ).start()


def _youdo_sticky_pids_to_keep() -> set[int]:
    """PIDs that must survive cleanup_stale_youdo_browser_processes (O269)."""
    pids: set[int] = set()
    with _YOUDO_STICKY_LOCK:
        proc = _YOUDO_STICKY_PROC
        if proc is None or proc.poll() is not None:
            return pids
        pid = int(proc.pid or 0)
        if pid <= 0:
            return pids
        pids.add(pid)
        try:
            import psutil

            for child in psutil.Process(pid).children(recursive=True):
                pids.add(int(child.pid))
        except Exception:
            pass
    return pids


def youdo_sticky_keepalive_ping() -> None:
    """Keep warm sticky worker alive across fetch_every_n skip cycles (O269)."""
    if not _youdo_sticky_session_enabled():
        return
    with _YOUDO_STICKY_LOCK:
        proc = _YOUDO_STICKY_PROC
        if proc is None or proc.poll() is not None:
            return
        if _YOUDO_STICKY_LAST_VALID <= 0:
            return
        try:
            _youdo_sticky_send_json(proc, {"cmd": "ping"}, timeout_sec=10.0)
        except Exception as exc:
            logger.debug("fetch:youdo sticky_keepalive failed: %s", exc)


def _fetch_youdo_sticky_listing(
    url: str,
    *,
    user_agent: str,
    timeout_sec: float,
    proxy_url: str,
    tier: str = "dc",
    allow_warm: bool = True,
    allow_cold_retry: bool = True,
) -> str:
    """O266: long-lived Camoufox tab — reload after first valid listing HTML."""
    if not _on_playwright_thread():
        return _playwright_sync(
            _fetch_youdo_sticky_listing,
            url,
            user_agent=user_agent,
            timeout_sec=timeout_sec,
            proxy_url=proxy_url,
            tier=tier,
            allow_warm=allow_warm,
            allow_cold_retry=allow_cold_retry,
        )
    if not _youdo_sticky_session_enabled() or not _youdo_is_camoufox():
        return _fetch_youdo_ephemeral(
            url,
            user_agent=user_agent,
            timeout_sec=timeout_sec,
            proxy_url=proxy_url,
            stage="listing",
            slot_attempt=1,
            tier=tier,
        )

    hint = _hint_from_url(proxy_url) or "direct"
    global _YOUDO_STICKY_PROC, _YOUDO_STICKY_PROXY, _YOUDO_STICKY_LAST_VALID
    with _fetch_lock("youdo"):
        use_warm = allow_warm
        cold_retries_left = 1 if allow_cold_retry else 0
        spawn_attempts = 0
        while True:
            with _YOUDO_STICKY_LOCK:
                warm = use_warm and _youdo_sticky_is_warm_unlocked(proxy_url=proxy_url)
                proc = _YOUDO_STICKY_PROC
                if proc is not None and proc.poll() is not None:
                    logger.info(
                        "fetch:youdo sticky_worker_died rc=%s — respawn",
                        proc.returncode,
                    )
                    _youdo_sticky_teardown_unlocked(log_trace=False)
                    proc = None
                    warm = False
                if proc is not None and _YOUDO_STICKY_PROXY and _YOUDO_STICKY_PROXY != proxy_url:
                    _youdo_sticky_teardown_unlocked(log_trace=False)
                    proc = None
                    warm = False
                if proc is not None and _YOUDO_STICKY_LAST_VALID > 0:
                    if time.time() - _YOUDO_STICKY_LAST_VALID > _youdo_sticky_max_age_sec():
                        _youdo_sticky_teardown_unlocked(log_trace=False)
                        proc = None
                        warm = False
                if proc is None:
                    spawn_attempts += 1
                    if spawn_attempts > 3:
                        raise HtmlFetchError("youdo sticky worker spawn loop exceeded")
                    _YOUDO_STICKY_PROC = _youdo_sticky_spawn_worker(
                        proxy_url=proxy_url,
                        user_agent=user_agent,
                    )
                    _youdo_sticky_start_stderr_drain(_YOUDO_STICKY_PROC)
                    _YOUDO_STICKY_PROXY = proxy_url
                    warm = False
                    proc = _YOUDO_STICKY_PROC

                cmd = "reload" if warm else "goto"
                stage = f"sticky_{cmd}"
                req = {
                    "cmd": cmd,
                    "url": url,
                    "tier": tier,
                    "timeout": timeout_sec,
                }
                try:
                    result = _youdo_sticky_send_json(
                        proc,
                        req,
                        timeout_sec=timeout_sec + 45.0,
                    )
                except HtmlFetchError:
                    _youdo_sticky_teardown_unlocked(log_trace=False)
                    if cold_retries_left > 0 and use_warm:
                        use_warm = False
                        cold_retries_left = 0
                        continue
                    return _fetch_youdo_ephemeral(
                        url,
                        user_agent=user_agent,
                        timeout_sec=timeout_sec,
                        proxy_url=proxy_url,
                        stage="listing",
                        slot_attempt=1,
                        tier=tier,
                    )

                if result.get("error"):
                    err = str(result["error"])
                    fail_html = str(result.get("html") or "")
                    _wipe_youdo_profile_on_poison(
                        proxy_url=proxy_url,
                        html=fail_html,
                        exc=HtmlFetchError(err),
                    )
                    _youdo_sticky_teardown_unlocked(log_trace=False)
                    if cold_retries_left > 0 and use_warm:
                        use_warm = False
                        cold_retries_left = 0
                        continue
                    raise HtmlFetchError(err)

                html = str(result.get("html") or "")
                goto_ms = int(result.get("goto_ms") or 0)
                try:
                    _validate_youdo_html(html, proxy_url)
                except HtmlFetchError as val_exc:
                    _log_youdo_browser_trace(
                        launch_ms=0,
                        goto_ms=goto_ms,
                        status="antibot",
                        html_len=len(html),
                        antibot_hit=True,
                    )
                    _wipe_youdo_profile_on_poison(
                        proxy_url=proxy_url,
                        html=html,
                        exc=val_exc,
                    )
                    _youdo_sticky_teardown_unlocked(log_trace=False)
                    if cold_retries_left > 0 and use_warm:
                        use_warm = False
                        cold_retries_left = 0
                        continue
                    raise val_exc

                _YOUDO_STICKY_LAST_VALID = time.time()
                _YOUDO_STICKY_PROXY = proxy_url
                try:
                    from youdo_parser import log_youdo_trace_path

                    log_youdo_trace_path(
                        None,
                        stage,
                        proxy_hint=hint,
                        html_len=len(html),
                        warm=1 if warm else 0,
                        goto_ms=goto_ms,
                    )
                except Exception:
                    pass
                _log_youdo_browser_trace(
                    launch_ms=0,
                    goto_ms=goto_ms,
                    status="200",
                    html_len=len(html),
                    antibot_hit=False,
                )
                _clear_youdo_soft_sp_fetch_fail()
                _maybe_mark_youdo_session_listing_ok(html)
                return html


def reset_youdo_sticky_for_tests() -> None:
    global _YOUDO_SESSION_LISTING_OK
    _YOUDO_SESSION_LISTING_OK = False
    with _YOUDO_STICKY_LOCK:
        _youdo_sticky_teardown_unlocked(log_trace=False)


def youdo_browser_teardown() -> int:
    """Full YouDo browser teardown — contexts, worker thread, camoufox orphans (O254)."""
    _youdo_sticky_teardown(log_trace=True)
    if youdo_persistent_profile_enabled():
        _wipe_youdo_persistent_profiles()
    close_all_browser_contexts()
    _abort_playwright_worker()
    return cleanup_stale_youdo_browser_processes()


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
    if not _on_playwright_thread():
        return _playwright_sync(
            _launch_youdo_persistent_context,
            proxy_url,
            user_agent=user_agent,
        )
    key = _youdo_profile_key(proxy_url)
    with _LOCK:
        ctx = _CONTEXTS.get(key)
        if ctx is not None:
            return ctx, key

    profile_dir = _data_root() / key
    profile_dir.mkdir(parents=True, exist_ok=True)
    pw = _get_youdo_playwright()
    ua = pick_browser_user_agent(user_agent)
    launch_kw: dict[str, Any] = {
        "user_data_dir": str(profile_dir),
        "headless": _youdo_headless(),
        "user_agent": ua,
        "locale": "ru-RU",
        "timezone_id": "Europe/Moscow",
        "viewport": {"width": 1366, "height": 768},
    }
    launch_kw.update(_youdo_launch_extra_kw())
    px = _playwright_proxy(proxy_url)
    if px:
        launch_kw["proxy"] = px
    try:
        ctx = _youdo_browser_launcher(pw).launch_persistent_context(**launch_kw)
    except Exception as exc:
        _close_context(key)
        raise HtmlFetchError(f"Playwright launch failed (youdo): {exc}") from exc
    _apply_youdo_stealth(ctx)
    if os.getenv("YOUDO_LEAN_PERSISTENT", "0").strip().lower() in ("1", "true", "yes"):
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


async def _warm_youdo_home_async(page, proxy_url: str, *, timeout_ms: int) -> None:
    t0 = time.monotonic()
    await page.goto("https://youdo.com/", wait_until="domcontentloaded", timeout=timeout_ms)
    await page.wait_for_timeout(random.randint(2000, 5000))
    try:
        await page.mouse.wheel(0, 400)
    except Exception:
        pass
    await page.wait_for_timeout(random.randint(1000, 2000))
    _log_browser_trace("youdo", proxy_url, "warm_home", t0, http=200)


async def _maybe_warm_youdo_home_async(
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
    await _warm_youdo_home_async(page, proxy_url, timeout_ms=timeout_ms)
    _mark_youdo_warm(key)


def _validate_youdo_html(html: str, proxy_url: str) -> None:
    low = html.lower()
    stripped = html.strip()
    if not stripped:
        raise HtmlFetchError("empty HTML after goto (youdo)")
    if _youdo_html_is_servicepipe(html):
        raise HtmlFetchError("ServicePipe antibot challenge (youdo).")
    if "403 forbidden" in low[:3000]:
        raise HtmlFetchError("403 Forbidden (youdo)")
    if "cloudflare" in low and ("challenge" in low or "blocked" in low):
        raise HtmlFetchError(f"Cloudflare challenge (youdo, {_hint_from_url(proxy_url)})")
    if len(stripped) <= 1500:
        raise HtmlFetchError("SPA shell / antibot HTML (youdo, too short).")
    if len(stripped) < 8000 and not _youdo_html_has_task_cards(html):
        raise HtmlFetchError("SPA shell without task cards (youdo).")
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
    tier: str = "dc",
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
            tier=tier,
        )
    if _youdo_use_subprocess_worker():
        html = _fetch_youdo_ephemeral(
            url,
            user_agent=user_agent,
            timeout_sec=timeout_sec,
            proxy_url=proxy_url,
            stage=stage,
            slot_attempt=slot_attempt,
            tier=tier,
        )
        if with_final_url:
            return html, url
        return html

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
            _youdo_wait_listing_ready(page, listing_timeout_ms, tier=tier)
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
        if stage == "detail" and _youdo_detail_html_ok(html, url, final_url=final_url):
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


def _youdo_detail_html_ok(html: str, page_url: str = "", *, final_url: str = "") -> bool:
    """Detail pages skip listing card checks (O194 subprocess ingest path)."""
    if _youdo_delist_html_ok(html, final_url or page_url):
        return True
    stripped = (html or "").strip()
    if len(stripped) < 2000:
        return False
    low = stripped.casefold()
    if "__next_data__" in low and re.search(r"/t\d+", stripped):
        return True
    return len(stripped) >= 5000


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
    if not _on_playwright_thread():
        return _playwright_sync(
            fetch_youdo_detail_snapshot,
            url,
            user_agent=user_agent,
            timeout_sec=timeout_sec,
            proxy_url=proxy_url,
        )
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


async def _fetch_youdo_camoufox_async(
    url: str,
    *,
    user_agent: str,
    timeout_sec: float,
    proxy_url: str,
    stage: str = "listing",
    slot_attempt: int = 1,
    tier: str = "dc",
) -> _YoudoCamoufoxFetchResult:
    """Camoufox ephemeral fetch via AsyncCamoufox (O190 t0g — radar-safe asyncio)."""
    _check_camoufox_playwright_compat()
    try:
        from camoufox.async_api import AsyncCamoufox
    except ImportError as exc:
        raise HtmlFetchError(
            "Camoufox не установлен (pip install camoufox && python -m camoufox fetch)."
        ) from exc

    ua = pick_browser_user_agent(user_agent)
    timeout_ms = max(int(timeout_sec * 1000), 5000)
    _youdo_jitter_sleep()
    px = _playwright_proxy(proxy_url)
    launch_kw: dict[str, Any] = {"headless": _youdo_headless()}
    launch_kw.update(_youdo_launch_extra_kw())
    if px:
        launch_kw["proxy"] = px
    launch_t0 = time.monotonic()
    launch_ms = 0
    goto_t0 = time.monotonic()
    html = ""
    list_view_results: list[_YoudoListViewResult] = []
    try:
        async with AsyncCamoufox(**launch_kw) as browser:
            launch_ms = int((time.monotonic() - launch_t0) * 1000)
            goto_t0 = time.monotonic()
            ctx = await browser.new_context(
                user_agent=ua,
                locale="ru-RU",
                timezone_id="Europe/Moscow",
                viewport={"width": 1366, "height": 768},
            )
            if _youdo_lean_route_on_attempt(slot_attempt):
                await ctx.route("**/*", _abort_youdo_lean_route_async)
            page = await ctx.new_page()
            listing_timeout_ms = _youdo_listing_goto_timeout_ms(timeout_sec)
            if stage == "listing" and youdo_warm_home_enabled() and not _youdo_is_camoufox():
                try:
                    await _maybe_warm_youdo_home_async(
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
            await page.goto(
                url,
                wait_until=_youdo_goto_wait_until_for_attempt(slot_attempt),
                timeout=listing_timeout_ms,
            )
            if stage == "listing":
                await _youdo_wait_listing_ready_async(
                    page,
                    listing_timeout_ms,
                    list_view_out=list_view_results,
                    tier=tier,
                )
            else:
                await page.wait_for_timeout(min(2000, timeout_ms // 4))
            html = await page.content()
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
    list_view = (
        list_view_results[-1]
        if list_view_results
        else _YoudoListViewResult(clicked=False, selector="none", data_id_count=0)
    )
    if stage == "listing":
        _log_youdo_list_view_trace(list_view)
    try:
        _validate_youdo_html(html, proxy_url)
    except HtmlFetchError as val_exc:
        if stage == "detail" and _youdo_detail_html_ok(html, url):
            return _YoudoCamoufoxFetchResult(html=html, list_view=list_view)
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
        if os.getenv("YOUDO_PROBE_SKIP_VALIDATE", "").strip().lower() in (
            "1",
            "true",
            "yes",
        ):
            return _YoudoCamoufoxFetchResult(html=html, list_view=list_view)
        raise val_exc
    return _YoudoCamoufoxFetchResult(html=html, list_view=list_view)


def _fetch_youdo_ephemeral(
    url: str,
    *,
    user_agent: str,
    timeout_sec: float,
    proxy_url: str,
    stage: str = "listing",
    slot_attempt: int = 1,
    tier: str = "dc",
) -> str:
    """YouDo legacy: ephemeral Chromium (YOUDO_EPHEMERAL=1)."""
    if not _on_playwright_thread():
        return _playwright_sync(
            _fetch_youdo_ephemeral,
            url,
            user_agent=user_agent,
            timeout_sec=timeout_sec,
            proxy_url=proxy_url,
            stage=stage,
            slot_attempt=slot_attempt,
            tier=tier,
        )
    if _youdo_is_camoufox():
        worker = Path(__file__).resolve().parent.parent / "scripts" / "youdo_fetch_worker.py"
        cmd = [
            sys.executable,
            str(worker),
            "--url",
            url,
            "--proxy",
            proxy_url,
            "--user-agent",
            user_agent,
            "--timeout",
            str(int(timeout_sec)),
            "--stage",
            stage,
            "--slot-attempt",
            str(slot_attempt),
            "--tier",
            tier,
            "--json",
        ]
        env = {
            **os.environ,
            "PYTHONPATH": str(Path(__file__).resolve().parent),
            "YOUDO_FETCH_TIER": tier,
        }
        with _fetch_lock("youdo"):
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec + 30,
                    env=env,
                )
            except subprocess.TimeoutExpired as te:
                raise HtmlFetchError(
                    f"youdo subprocess timeout after {int(timeout_sec) + 30}s"
                ) from te
        out_lines = (proc.stdout or "").strip().splitlines()
        if proc.returncode != 0 or not out_lines:
            err_msg = "youdo subprocess failed"
            for line in reversed(out_lines or (proc.stderr or "").strip().splitlines()):
                try:
                    err_obj = json.loads(line)
                    err_msg = str(err_obj.get("error", err_msg))
                    break
                except json.JSONDecodeError:
                    if line.strip():
                        err_msg = line.strip()[:300]
                        break
            raise HtmlFetchError(err_msg)
        try:
            result = json.loads(out_lines[-1])
        except json.JSONDecodeError as je:
            raise HtmlFetchError(f"youdo subprocess bad json: {je}") from je
        if "error" in result:
            raise HtmlFetchError(str(result["error"]))
        html = result["html"]
        try:
            _validate_youdo_html(html, proxy_url)
        except HtmlFetchError as val_exc:
            if stage == "detail" and _youdo_detail_html_ok(html, url):
                return html
            debug_path = ""
            if html.strip():
                debug_path = _save_youdo_debug_html(html, tag="youdo_antibot")
            _log_youdo_browser_trace(
                launch_ms=0,
                goto_ms=0,
                status="antibot",
                antibot_hit=True,
                html_len=len(html),
                debug_path=debug_path,
            )
            raise val_exc
        return html

    _clear_stale_asyncio_loop()
    with _fetch_lock("youdo"):
        ua = pick_browser_user_agent(user_agent)
        timeout_ms = max(int(timeout_sec * 1000), 5000)
        _youdo_jitter_sleep()
        px = _playwright_proxy(proxy_url)
        pw = _get_youdo_playwright()
        launch_kw: dict[str, Any] = {"headless": _youdo_headless()}
        launch_kw.update(_youdo_launch_extra_kw())
        if px:
            launch_kw["proxy"] = px
        launch_t0 = time.monotonic()
        browser = _youdo_browser_launcher(pw).launch(**launch_kw)
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
            _apply_youdo_stealth(ctx)
            if _youdo_lean_route_on_attempt(slot_attempt):
                ctx.route("**/*", _abort_youdo_lean_route)
            page = ctx.new_page()
            listing_timeout_ms = _youdo_listing_goto_timeout_ms(timeout_sec)
            if stage == "listing" and youdo_warm_home_enabled() and not _youdo_is_camoufox():
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
                _youdo_wait_listing_ready(page, listing_timeout_ms, tier=tier)
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
        if stage == "detail" and _youdo_detail_html_ok(html, url):
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


def fl_listing_subprocess_enabled() -> bool:
    """O193: FL listing via fl_fetch_worker.py — rollback with FL_LISTING_SUBPROCESS=0."""
    return os.getenv("FL_LISTING_SUBPROCESS", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _validate_listing_browser_html(
    html: str,
    source: str,
    proxy: str,
    *,
    profile_key: str = "",
) -> None:
    key = profile_key or _profile_key(source, proxy)
    low = html.lower()
    if "cloudflare" in low and ("challenge" in low or "blocked" in low):
        invalidate_browser_slot(source, proxy)
        raise HtmlFetchError(f"Cloudflare challenge ({source}, {key})")
    if len(html.strip()) < 500 or "проверьте, что вы не робот" in low:
        invalidate_browser_slot(source, proxy)
        raise HtmlFetchError(f"Слишком короткий ответ Playwright ({source}).")
    if source == "fl" and "b-page__lenta_item" not in low and "b-page__lenta" not in low:
        invalidate_browser_slot(source, proxy)
        raise HtmlFetchError(
            f"FL listing без карточек ленты (antibot/пустая страница, {key})."
        )


def fetch_fl_listing_ephemeral_standalone(
    url: str,
    *,
    user_agent: str,
    timeout_sec: float,
    proxy_url: str,
) -> str:
    """Isolated ephemeral Chromium fetch — fl_fetch_worker subprocess entry (O193)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise HtmlFetchError(
            "Playwright не установлен (pip install playwright && playwright install chromium)."
        ) from exc

    ua = pick_browser_user_agent(user_agent)
    timeout_ms = max(int(timeout_sec * 1000), 5000)
    proxy = (proxy_url or "").strip()
    _jitter_sleep()
    px = _playwright_proxy(proxy) if proxy else None
    _clear_stale_asyncio_loop()

    with sync_playwright() as pw:
        launch_kw: dict[str, Any] = {"headless": True}
        if px:
            launch_kw["proxy"] = px
        browser = pw.chromium.launch(**launch_kw)
        try:
            ctx = browser.new_context(
                user_agent=ua,
                locale="ru-RU",
                viewport={"width": 1366, "height": 768},
            )
            page = ctx.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(min(1500, timeout_ms // 4))
            html = page.content()
        finally:
            try:
                browser.close()
            except Exception:
                pass

    _validate_listing_browser_html(html, "fl", proxy)
    return html


def _parse_fetch_worker_json(
    stdout: str,
    *,
    label: str,
    stderr: str = "",
) -> str:
    out_lines = [ln.strip() for ln in (stdout or "").splitlines() if ln.strip()]
    if not out_lines:
        raise HtmlFetchError(f"{label} subprocess empty stdout")
    last_je: json.JSONDecodeError | None = None
    for line in reversed(out_lines):
        try:
            result = json.loads(line)
        except json.JSONDecodeError as je:
            last_je = je
            continue
        if not isinstance(result, dict):
            continue
        if result.get("error"):
            raise HtmlFetchError(str(result["error"]))
        if result.get("ok") is False:
            raise HtmlFetchError(str(result.get("error") or f"{label} subprocess failed"))
        html = result.get("html")
        if isinstance(html, str):
            return html
    err_tail = (stderr or "").strip().splitlines()[-3:]
    tail = " | ".join(err_tail)[:400] if err_tail else ""
    detail = f"{label} subprocess bad json: {last_je or 'no json object'}"
    if tail:
        detail = f"{detail}; stderr_tail={tail}"
    raise HtmlFetchError(detail)


def _log_fl_subprocess_json_fail(detail: str, stderr: str) -> None:
    """O233: subprocess JSON parse failure → radar_site.log."""
    tail = " | ".join((stderr or "").strip().splitlines()[-5:])[:500]
    msg = f"fetch:fl subprocess bad json: {detail[:200]}"
    if tail:
        msg = f"{msg} stderr_tail={tail}"
    logger.warning(msg)
    try:
        from config import load_config
        from radar_cycle_log import log_pipeline_line

        log_pipeline_line(load_config().radar_log_path, msg)
    except Exception:
        pass


def _fetch_fl_listing_subprocess(
    url: str,
    *,
    user_agent: str,
    timeout_sec: float,
    proxy_url: str | None = None,
) -> str:
    """FL listing via fl_fetch_worker.py — asyncio isolation (O193)."""
    if not _on_playwright_thread():
        return _playwright_sync(
            _fetch_fl_listing_subprocess,
            url,
            user_agent=user_agent,
            timeout_sec=timeout_sec,
            proxy_url=proxy_url,
        )
    proxy = (proxy_url or "").strip() or exchange_primary_proxy_url("fl")
    worker = Path(__file__).resolve().parent.parent / "scripts" / "fl_fetch_worker.py"
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parent)}
    cmd = [
        sys.executable,
        str(worker),
        "--url",
        url,
        "--user-agent",
        user_agent,
        "--timeout",
        str(int(timeout_sec)),
        "--json",
    ]
    if proxy:
        cmd.extend(["--proxy", proxy])
    with _fetch_lock("fl"):
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec + 30,
                env=env,
            )
        except subprocess.TimeoutExpired as te:
            raise HtmlFetchError(
                f"fl subprocess timeout after {int(timeout_sec) + 30}s"
            ) from te
    if proc.returncode != 0:
        err_msg = "fl subprocess failed"
        for line in reversed(
            (proc.stdout or "").strip().splitlines()
            or (proc.stderr or "").strip().splitlines()
        ):
            try:
                err_obj = json.loads(line)
                err_msg = str(err_obj.get("error", err_msg))
                break
            except json.JSONDecodeError:
                if line.strip():
                    err_msg = line.strip()[:300]
                    break
        raise HtmlFetchError(err_msg)
    try:
        html = _parse_fetch_worker_json(
            proc.stdout or "",
            label="fl",
            stderr=proc.stderr or "",
        )
    except HtmlFetchError as exc:
        _log_fl_subprocess_json_fail(str(exc), proc.stderr or "")
        raise
    _validate_listing_browser_html(html, "fl", proxy)
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
    if source == "fl" and fl_listing_subprocess_enabled():
        return _fetch_fl_listing_subprocess(
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
            raise HtmlFetchError(f"{type(exc).__name__}: {exc}") from exc
        finally:
            try:
                page.close()
            except Exception:
                pass
            with _LOCK:
                _close_context(key)

    _validate_listing_browser_html(html, source, proxy, profile_key=key)
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
    if not _on_playwright_thread():
        return _playwright_sync(
            fetch_listing_html_browser_wall_clock,
            source,
            url,
            user_agent=user_agent,
            timeout_sec=timeout_sec,
            wall_clock_sec=wall_clock_sec,
            proxy_url=proxy_url,
        )
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
        _youdo_wall_clock_teardown(source)
        raise HtmlFetchError(f"wall-clock timeout after {int(wall)}s ({source})")


def fetch_listing_html_browser_slots_wall_clock(
    source: str,
    url: str,
    *,
    user_agent: str,
    timeout_sec: float = 45.0,
    wall_clock_sec: float = 120.0,
    proxy_urls: list[str] | None = None,
    storage: object | None = None,
) -> str:
    """Hard cap on slots browser fetch — O160 YouDo hang guard."""
    if not _on_playwright_thread():
        return _playwright_sync(
            fetch_listing_html_browser_slots_wall_clock,
            source,
            url,
            user_agent=user_agent,
            timeout_sec=timeout_sec,
            wall_clock_sec=wall_clock_sec,
            proxy_urls=proxy_urls,
            storage=storage,
        )
    wall = max(float(wall_clock_sec), 1.0)
    per_op = min(float(timeout_sec), wall)

    def _run() -> str:
        return fetch_listing_html_browser_slots(
            source,
            url,
            user_agent=user_agent,
            timeout_sec=per_op,
            proxy_urls=proxy_urls,
            storage=storage,
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
        _youdo_wall_clock_teardown(source)
        raise HtmlFetchError(f"wall-clock timeout after {int(wall)}s ({source})")


def _fetch_youdo_one_browser_slot(
    url: str,
    *,
    user_agent: str,
    timeout_sec: float,
    proxy_url: str,
    slots_tried: int,
    tier: str = "dc",
) -> str:
    hint = _hint_from_url(proxy_url) or "direct"
    use_ephemeral = slots_tried > 1 and _youdo_ephemeral_on_slot_retry()
    if slots_tried > 1:
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
    if _youdo_should_use_sticky_listing(
        slots_tried=slots_tried,
        use_ephemeral=use_ephemeral,
        proxy_url=proxy_url,
    ):
        return _fetch_youdo_sticky_listing(
            url,
            user_agent=user_agent,
            timeout_sec=timeout_sec,
            proxy_url=proxy_url,
            tier=tier,
        )
    use_ephemeral_listing = (
        youdo_ephemeral()
        or use_ephemeral
        or (
            _youdo_is_camoufox()
            and _youdo_ephemeral_first_slot1(
                slots_tried=slots_tried,
                proxy_url=proxy_url,
            )
        )
    )
    if use_ephemeral_listing:
        html = _fetch_youdo_ephemeral(
            url,
            user_agent=user_agent,
            timeout_sec=timeout_sec,
            proxy_url=proxy_url,
            stage="listing",
            slot_attempt=slots_tried,
            tier=tier,
        )
        _maybe_mark_youdo_session_listing_ok(html)
        return html
    return fetch_youdo_html_browser(
        url,
        user_agent=user_agent,
        timeout_sec=timeout_sec,
        proxy_url=proxy_url,
        stage="listing",
        slot_attempt=slots_tried,
        tier=tier,
    )


def _fetch_youdo_listing_dc_first(
    url: str,
    *,
    user_agent: str,
    timeout_sec: float,
) -> str:
    """O260/O262f: DC tier → early RU on ServicePipe streak → dc_hard_reset → RU carousel."""
    from exchange_proxy import youdo_dc_alive_urls, youdo_listing_slot_urls

    last_exc: HtmlFetchError | None = None
    slots_tried = 0
    dc_bans_this_fetch = [0]
    servicepipe_streak = 0
    ru_early = False
    dc_cap = _youdo_dc_retry_max()
    retry_cap = min(dc_cap, _youdo_slot_retry_max())
    _clear_youdo_soft_sp_fetch_fail()

    def _attempt(proxy_url: str, tier: str) -> str | None:
        nonlocal last_exc, slots_tried, servicepipe_streak, ru_early
        tier_token = _youdo_fetch_tier_ctx.set(tier)
        try:
            if (
                tier.startswith("dc")
                and dc_bans_this_fetch[0] >= _youdo_max_dc_bans_per_fetch()
                and youdo_proxy_in_dc_pool(proxy_url)
            ):
                try:
                    from exchange_proxy import youdo_dc_pool_size

                    dc_alive_n = len(youdo_dc_alive_urls())
                    dc_total = youdo_dc_pool_size()
                    logger.info(
                        "fetch:youdo stage=dc_ban_limit_reached bans_this_fetch=%d dc_alive=%d/%d",
                        dc_bans_this_fetch[0],
                        dc_alive_n,
                        dc_total,
                    )
                except Exception:
                    pass
                return None
            slots_tried += 1
            _youdo_log_tier_attempt(tier, proxy_url, slots_tried)
            hint = _hint_from_url(proxy_url) or "direct"
            if tier == "ru_fallback" and not youdo_ru_alive_urls():
                logger.info(
                    "fetch:youdo reason=ru_pool_dead proxy=%s slot=%d — skip",
                    hint,
                    slots_tried,
                )
                last_exc = HtmlFetchError(
                    f"youdo: ru_pool_dead proxy={hint} slot={slots_tried}"
                )
                return None
            try:
                html = _fetch_youdo_one_browser_slot(
                    url,
                    user_agent=user_agent,
                    timeout_sec=timeout_sec,
                    proxy_url=proxy_url,
                    slots_tried=slots_tried,
                    tier=tier,
                )
                _clear_youdo_soft_sp_fetch_fail()
                return html
            except HtmlFetchError as exc:
                last_exc = exc
                is_sp = _is_youdo_servicepipe_error(exc)
                if tier.startswith("dc") and is_sp:
                    servicepipe_streak += 1
                    if (
                        servicepipe_streak >= 2
                        and _youdo_servicepipe_early_ru_enabled()
                    ):
                        ru_early = True
                        logger.info(
                            "fetch:youdo stage=ru_early reason=servicepipe_streak=%d",
                            servicepipe_streak,
                        )
                        try:
                            from youdo_parser import log_youdo_trace_path

                            log_youdo_trace_path(
                                None,
                                "ru_early",
                                reason="servicepipe_streak",
                                streak=servicepipe_streak,
                            )
                        except Exception:
                            pass
                        return None
                soft_sp = _youdo_soft_servicepipe_ban_enabled()
                skip_ban = (
                    tier.startswith("dc")
                    and is_sp
                    and (
                        (soft_sp and servicepipe_streak == 1)
                        or (
                            servicepipe_streak >= 2
                            and len(youdo_dc_alive_urls()) > 1
                        )
                    )
                )
                if skip_ban:
                    if soft_sp and servicepipe_streak == 1:
                        _mark_youdo_soft_sp_fetch_fail()
                    logger.info(
                        "fetch:youdo stage=servicepipe_skip_ban dc_alive=%d streak=%d soft=%d",
                        len(youdo_dc_alive_urls()),
                        servicepipe_streak,
                        1 if soft_sp and servicepipe_streak == 1 else 0,
                    )
                else:
                    invalidate_browser_slot("youdo", proxy_url)
                    logger.warning(
                        "youdo_listing: browser slot %s failed: %s", hint, exc
                    )
                if not _youdo_browser_slot_fail_limited(
                    proxy_url,
                    exc,
                    dc_bans_this_fetch=dc_bans_this_fetch,
                    skip_slot_ban=skip_ban,
                ):
                    return None
                if not _is_youdo_slot_retryable(exc):
                    return None
                if tier.startswith("dc") and _is_youdo_slot_retryable(exc):
                    try:
                        from exchange_proxy import youdo_dc_pool_size

                        dc_alive_n = len(youdo_dc_alive_urls())
                        dc_total = youdo_dc_pool_size()
                        logger.info(
                            "fetch:youdo stage=dc_rotate slot=%d proxy_hint=%s "
                            "reason=%s dc_alive=%d/%d",
                            slots_tried + 1,
                            hint,
                            "spa_shell"
                            if "spa shell" in str(exc).casefold()
                            else "slot_fail",
                            dc_alive_n,
                            dc_total,
                        )
                    except Exception:
                        pass
                    _abort_playwright_worker()
                return None
        finally:
            _youdo_fetch_tier_ctx.reset(tier_token)

    dc_plan = _youdo_fetch_tier_plan()
    for proxy_url, tier in dc_plan:
        if ru_early or slots_tried >= retry_cap:
            break
        if (
            tier.startswith("dc")
            and dc_bans_this_fetch[0] >= _youdo_max_dc_bans_per_fetch()
        ):
            break
        result = _attempt(proxy_url, tier)
        if result is not None:
            return result
        if ru_early:
            break
        if (
            dc_bans_this_fetch[0] >= _youdo_max_dc_bans_per_fetch()
            and tier.startswith("dc")
        ):
            break
        if last_exc and not _is_youdo_slot_retryable(last_exc):
            break

    if not ru_early and youdo_dc_alive_urls():
        try:
            from youdo_parser import youdo_hard_reset

            youdo_hard_reset(reason="dc_fetch_exhausted")
        except Exception as exc:
            logger.warning("fetch:youdo dc_hard_reset failed: %s", exc)
        for proxy_url in youdo_listing_slot_urls(include_ru=False)[:dc_cap]:
            if ru_early or dc_bans_this_fetch[0] >= _youdo_max_dc_bans_per_fetch():
                break
            result = _attempt(proxy_url, "dc_hard_reset")
            if result is not None:
                return result

    ru_slots: list[str] = []
    ru_allowed, ru_count, ru_max = _youdo_ru_burst_allowed()
    if ru_early and _youdo_servicepipe_early_ru_enabled():
        if ru_allowed:
            ru_slots = youdo_ru_alive_urls()[: _youdo_ru_retry_max()]
        else:
            logger.info(
                "fetch:youdo stage=ru_burst_skip ru_burst=%d/%d reason=early_ru",
                ru_count,
                ru_max,
            )
    elif not youdo_dc_alive_urls():
        if ru_allowed:
            ru_slots = youdo_ru_alive_urls()[: _youdo_ru_retry_max()]
        else:
            logger.info(
                "fetch:youdo stage=ru_burst_skip ru_burst=%d/%d reason=dc_exhausted",
                ru_count,
                ru_max,
            )
    if ru_slots:
        if ru_early:
            logger.info(
                "fetch:youdo stage=ru_early reason=servicepipe_streak=%d",
                servicepipe_streak,
            )
        for proxy_url in ru_slots:
            _consume_youdo_ru_burst()
            result = _attempt(proxy_url, "ru_fallback")
            if result is not None:
                return result

    detail = str(last_exc) if last_exc else "unknown"
    raise HtmlFetchError(
        f"youdo: all browser slots failed (dc+ru): {detail}"
    )


def fetch_listing_html_browser_slots(
    source: str,
    url: str,
    *,
    user_agent: str,
    timeout_sec: float = 45.0,
    proxy_urls: list[str] | None = None,
    storage: object | None = None,
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
            storage=storage,
        )
    if proxy_urls is not None:
        slots = proxy_urls
    elif source == "youdo" and youdo_one_slot_per_cycle():
        return _fetch_youdo_listing_dc_first(
            url,
            user_agent=user_agent,
            timeout_sec=timeout_sec,
        )
    elif source == "fl":
        dc_alive = fl_dc_alive_urls()
        if dc_alive:
            primary = exchange_primary_proxy_url("fl")
            if primary and primary in dc_alive:
                slots = [primary] + [u for u in dc_alive if u != primary]
            else:
                slots = list(dc_alive)
        else:
            slots = exchange_alive_proxy_urls("fl")
            if not slots:
                primary = exchange_primary_proxy_url("fl")
                slots = [primary] if primary else []
    else:
        slots = exchange_alive_proxy_urls(source)
    if not slots:
        raise HtmlFetchError(f"{source}: no alive proxy slots for browser")
    last_exc: HtmlFetchError | None = None
    slots_tried = 0
    retry_cap = (
        _youdo_slot_retry_max()
        if source == "youdo"
        else (
            max(_fl_slot_retry_max(), len(slots))
            if source == "fl" and slots
            else (_fl_slot_retry_max() if source == "fl" else 1)
        )
    )
    dc_bans_this_fetch = [0]
    # O257 Phase 4: pre-compute RU slot set for YouDo dead-pool skip.
    _youdo_ru_set: frozenset[str] = frozenset()
    if source == "youdo" and len(slots) > 1:
        try:
            _youdo_ru_set = frozenset(youdo_ru_alive_urls())
        except Exception:
            pass
    for proxy_url in slots:
        slots_tried += 1
        hint = _hint_from_url(proxy_url) or "direct"
        # O257: skip RU slot retry when RU pool is dead to avoid hammering dead node-proxy.
        if source == "youdo" and slots_tried > 1 and proxy_url in _youdo_ru_set:
            try:
                if not youdo_ru_alive_urls():
                    logger.info(
                        "fetch:youdo reason=ru_pool_dead proxy=%s slot=%d — skip",
                        hint,
                        slots_tried,
                    )
                    last_exc = HtmlFetchError(
                        f"youdo: ru_pool_dead proxy={hint} slot={slots_tried}"
                    )
                    break
            except Exception:
                pass
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
                use_ephemeral_listing = (
                    youdo_ephemeral()
                    or use_ephemeral
                    or (
                        _youdo_is_camoufox()
                        and _youdo_ephemeral_first_slot1(
                            slots_tried=slots_tried,
                            proxy_url=proxy_url,
                        )
                    )
                )
                if (
                    not use_ephemeral_listing
                    and _youdo_should_use_sticky_listing(
                        slots_tried=slots_tried,
                        use_ephemeral=use_ephemeral,
                        proxy_url=proxy_url,
                    )
                ):
                    html = _fetch_youdo_sticky_listing(
                        url,
                        user_agent=user_agent,
                        timeout_sec=timeout_sec,
                        proxy_url=proxy_url,
                    )
                    _maybe_mark_youdo_session_listing_ok(html)
                    return html
                if use_ephemeral_listing:
                    html = _fetch_youdo_ephemeral(
                        url,
                        user_agent=user_agent,
                        timeout_sec=timeout_sec,
                        proxy_url=proxy_url,
                        stage="listing",
                        slot_attempt=slots_tried,
                    )
                    _maybe_mark_youdo_session_listing_ok(html)
                    return html
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
                if not _youdo_browser_slot_fail_limited(
                    proxy_url, exc, dc_bans_this_fetch=dc_bans_this_fetch
                ):
                    break
                if (
                    _is_youdo_slot_retryable(exc)
                    and slots_tried < min(len(slots), retry_cap)
                ):
                    exc_low = str(exc).casefold()
                    rotate_reason = (
                        "spa_shell"
                        if "spa shell" in exc_low
                        else "slot_fail"
                    )
                    try:
                        from exchange_proxy import (
                            youdo_dc_alive_urls,
                            youdo_dc_pool_size,
                        )

                        dc_alive_n = len(youdo_dc_alive_urls())
                        dc_total = youdo_dc_pool_size()
                        next_hint = _hint_from_url(
                            slots[slots_tried] if slots_tried < len(slots) else ""
                        )
                        logger.info(
                            "fetch:youdo stage=dc_rotate slot=%d proxy_hint=%s "
                            "reason=%s dc_alive=%d/%d",
                            slots_tried + 1,
                            next_hint,
                            rotate_reason,
                            dc_alive_n,
                            dc_total,
                        )
                    except Exception:
                        pass
                    _abort_playwright_worker()
                    continue
                break
            if source == "fl":
                if _is_fl_dead_proxy_error(exc):
                    hint = _hint_from_url(proxy_url) or "direct"
                    if _fl_browser_dead_proxy_fail(proxy_url, exc):
                        logger.info(
                            "fetch:fl stage=dead_proxy_rotate slot=%d proxy_hint=%s",
                            slots_tried + 1,
                            hint,
                        )
                    _abort_playwright_worker()
                    if slots_tried < min(len(slots), retry_cap):
                        continue
                    break
                _fl_browser_antibot_fail(proxy_url, exc, storage=storage)
                if not fl_hard_reset_on_ban_enabled() and slots_tried < min(
                    len(slots), retry_cap
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
