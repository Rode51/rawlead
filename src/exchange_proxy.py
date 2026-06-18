"""Sticky cascade прокси для fetch бирж (FL/Kwork и др., не TG).

Primary pool (FL/Kwork): EXCHANGE_PROXY_URLS — баны per-source (fl / kwork).
Secondary (YouDo, Пчёл, …): EXCHANGE_PROXY_URLS_SECONDARY или primary + TELETHON acc2/3.
403/429 → бан только для этого source; connect — 3 подряд.
"""

from __future__ import annotations

import json
import logging
import os
import random
import time
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import requests

from config import DIRECT_REQUESTS_PROXIES, normalize_proxy_url, radar_timestamp

logger = logging.getLogger(__name__)

_FAILOVER_HTTP = frozenset({403, 429})
_BAN_TTL_SEC = float(os.getenv("EXCHANGE_PROXY_BAN_TTL_SEC", "3600"))
_STRIKES_TO_BAN = max(1, int(os.getenv("EXCHANGE_PROXY_STRIKES", "3")))
_HTTP_STRIKES_TO_BAN = max(2, int(os.getenv("EXCHANGE_PROXY_HTTP_STRIKES", "2")))


def _http_strikes_to_ban(source: str) -> int:
    src = (source or "").strip()
    if src == "youdo":
        return max(2, int(os.getenv("YOUDO_HTTP_STRIKES", "4")))
    return _HTTP_STRIKES_TO_BAN
_CONNECT_TIMEOUT_SEC = float(os.getenv("EXCHANGE_PROXY_CONNECT_TIMEOUT_SEC", "5"))
_READ_TIMEOUT_SEC = float(os.getenv("EXCHANGE_PROXY_READ_TIMEOUT_SEC", "20"))
_ALERT_COOLDOWN_SEC = float(os.getenv("EXCHANGE_PROXY_ALERT_COOLDOWN_SEC", "600"))
_ALERT_LOW_POOL_SEC = float(os.getenv("EXCHANGE_PROXY_LOW_POOL_COOLDOWN_SEC", "300"))
_FAILOVER_COOLDOWN_MIN_SEC = float(os.getenv("EXCHANGE_PROXY_FAILOVER_COOLDOWN_MIN_SEC", "5"))
_FAILOVER_COOLDOWN_MAX_SEC = float(os.getenv("EXCHANGE_PROXY_FAILOVER_COOLDOWN_MAX_SEC", "15"))

_BANS_STORAGE_KEY = "exchange_proxy_bans_v2"
_BANS_STORAGE_KEY_LEGACY = "exchange_proxy_bans_v1"
_ACTIVE_SLOT_KEY = "exchange_proxy_active_slot_v1"
_YOUDO_DC_BANNED_SINCE_KEY = "youdo_dc_banned_since"
_PRIMARY_SOURCES = frozenset({"fl", "kwork"})
_TELETHON_POOL_ENV = (
    "TELETHON_PROXY_ACC2",
    "TELETHON_PROXY_ACC3",
    "TELETHON_PROXY_ACC4",
)
# Никогда в биржевой пул: Bot API + acc1 (DEPLOY_VPS)
_EXCHANGE_POOL_FORBIDDEN_ENV = (
    "TG_PROXY_URL",
    "TELETHON_PROXY_ACC1",
    "TELETHON_PROXY_URL",
    "OPENROUTER_HTTP_PROXY",
)

_sessions: dict[str, "ExchangeFetchSession"] = {}
# host:port → unix until
_banned_until: dict[str, float] = {}
_ban_meta: dict[str, dict[str, Any]] = {}
_strike_count: dict[str, int] = {}
_active_slot: dict[str, int] = {}
_last_owner_alert_at: float = 0.0
_last_pool_exhausted_alert_at: float = 0.0
_PROXY_ALERT_PREFIX = "FLPARSING · прокси бирж"
_persistence_loaded: bool = False


def _parse_proxy_list(env_plural: str, env_single: str) -> list[str]:
    raw = os.getenv(env_plural, "").strip()
    parts = [p.strip() for p in raw.split(",") if p.strip()] if raw else []
    if not parts:
        one = os.getenv(env_single, "").strip()
        if one:
            parts = [one]
    out: list[str] = []
    for p in parts:
        try:
            out.append(normalize_proxy_url(p))
        except ValueError:
            continue
    return out


def _dedupe_urls(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        h = _hint_from_url(u)
        if not h or h == "direct" or h in seen:
            continue
        seen.add(h)
        out.append(u)
    return out


def _primary_exchange_pool() -> list[str]:
    urls = _parse_proxy_list("EXCHANGE_PROXY_URLS", "EXCHANGE_PROXY_URL")
    if urls:
        return urls
    return _parse_proxy_list("FL_PROXY_URLS", "FL_PROXY_URL")


def _forbidden_exchange_hosts() -> set[str]:
    hosts: set[str] = set()
    for key in _EXCHANGE_POOL_FORBIDDEN_ENV:
        raw = os.getenv(key, "").strip()
        if not raw:
            continue
        try:
            hosts.add(_hint_from_url(normalize_proxy_url(raw)))
        except ValueError:
            continue
    return hosts


def _telethon_exchange_extras() -> list[str]:
    forbidden = _forbidden_exchange_hosts()
    out: list[str] = []
    for key in _TELETHON_POOL_ENV:
        raw = os.getenv(key, "").strip()
        if not raw:
            continue
        try:
            url = normalize_proxy_url(raw)
        except ValueError:
            continue
        if _hint_from_url(url) in forbidden:
            logger.warning(
                "fetch:proxy skip %s — host reserved for TG, not exchanges",
                key,
            )
            continue
        out.append(url)
    return _dedupe_urls(out)


def _filter_forbidden_urls(urls: list[str]) -> list[str]:
    forbidden = _forbidden_exchange_hosts()
    if not forbidden:
        return urls
    return [u for u in urls if _hint_from_url(u) not in forbidden]


def _secondary_exchange_pool() -> list[str]:
    explicit = _parse_proxy_list(
        "EXCHANGE_PROXY_URLS_SECONDARY",
        "EXCHANGE_PROXY_URL_SECONDARY",
    )
    extras = _telethon_exchange_extras()
    if explicit:
        hints = {_hint_from_url(u) for u in explicit}
        merged = explicit + [u for u in extras if _hint_from_url(u) not in hints]
        return _filter_forbidden_urls(_dedupe_urls(merged))
    base = _primary_exchange_pool()
    hints = {_hint_from_url(u) for u in base}
    merged = base + [u for u in extras if _hint_from_url(u) not in hints]
    return _filter_forbidden_urls(_dedupe_urls(merged))


def _shared_exchange_pool() -> list[str]:
    """Обратная совместимость: primary pool."""
    return _primary_exchange_pool()


_FL_RES_BAN_SOURCE = "fl_res"
FL_DC_PARSED_INGEST_OK = 25


def _fl_dc_pool() -> list[str]:
    return _parse_proxy_list("FL_PROXY_URLS", "FL_PROXY_URL") or _primary_exchange_pool()


def _fl_residential_pool() -> list[str]:
    return _parse_proxy_list("FL_PROXY_URLS_RESIDENTIAL", "FL_PROXY_URL_RESIDENTIAL")


def _fl_pool_triple() -> tuple[str, str, list[str]]:
    """pool_key, ban_source, urls — DC tier first; residential when DC alive==0 (O210)."""
    _ensure_loaded()
    dc = _fl_dc_pool()
    if dc and _alive_urls(dc, "fl"):
        return "fl", "fl", dc
    res = _fl_residential_pool()
    if res:
        return "fl", _FL_RES_BAN_SOURCE, res
    return "fl", "fl", dc


def fl_dc_tier_exhausted() -> bool:
    """True when all DC FL slots are banned (residential may still work)."""
    _ensure_loaded()
    dc = _fl_dc_pool()
    if not dc:
        return False
    alive, total = _pool_counts(dc, "fl")
    return total > 0 and alive == 0


def fl_on_residential_tier() -> bool:
    _ensure_loaded()
    _, ban_source, urls = _fl_pool_triple()
    return ban_source == _FL_RES_BAN_SOURCE and bool(urls)


def fl_residential_counts() -> tuple[int, int]:
    """Alive/total residential FL slots (0,0 if pool empty)."""
    _ensure_loaded()
    res = _fl_residential_pool()
    return _pool_counts(res, _FL_RES_BAN_SOURCE)


def fl_dc_alive_urls() -> list[str]:
    _ensure_loaded()
    return _alive_urls(_fl_dc_pool(), "fl")


def fl_res_alive_urls() -> list[str]:
    _ensure_loaded()
    return _alive_urls(_fl_residential_pool(), _FL_RES_BAN_SOURCE)


def fl_one_slot_res_per_cycle() -> bool:
    """O215: on residential tier — one browser slot per cycle (do not burn 25 res)."""
    return os.getenv("FL_ONE_SLOT_RES_PER_CYCLE", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _fl_slot_retry_max() -> int:
    raw = os.getenv("FL_SLOT_RETRY_MAX", "1").strip()
    try:
        return max(1, min(int(raw), 8))
    except ValueError:
        return 1


def _fl_hard_reset_on_ban_enabled() -> bool:
    return os.getenv("FL_HARD_RESET_ON_BAN", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def fl_browser_slot_urls() -> list[str]:
    """DC primary; residential only when DC exhausted; res = 1 slot/cycle (O191/O215)."""
    dc_alive = fl_dc_alive_urls()
    if dc_alive:
        primary = exchange_primary_proxy_url("fl")
        if primary and primary in dc_alive:
            slots = [primary] + [u for u in dc_alive if u != primary]
        else:
            slots = list(dc_alive)
        return slots[: _fl_slot_retry_max()]
    res_alive = fl_res_alive_urls()
    if not res_alive:
        return []
    primary = exchange_primary_proxy_url("fl")
    if fl_one_slot_res_per_cycle():
        if primary and primary in res_alive:
            return [primary]
        return [res_alive[0]]
    if primary and primary in res_alive:
        slots = [primary] + [u for u in res_alive if u != primary]
    else:
        slots = list(res_alive)
    return slots[: min(_fl_slot_retry_max(), 2)]


def _youdo_dc_slot_count() -> int:
    raw = os.getenv("YOUDO_O191_DC_SLOTS", "1").strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 1


def _youdo_dc_pool() -> list[str]:
    if _youdo_dc_slot_count() == 0:
        return []
    explicit = _parse_proxy_list("YOUDO_DC_PROXY_URLS", "YOUDO_DC_PROXY_URL")
    if explicit:
        return explicit
    fl = _fl_dc_pool()
    if fl:
        return fl[: _youdo_dc_slot_count()]
    all_urls = _parse_proxy_list("YOUDO_PROXY_URLS", "YOUDO_PROXY_URL")
    if not all_urls:
        return []
    return all_urls[: _youdo_dc_slot_count()]


def _youdo_ru_pool() -> list[str]:
    all_urls = _parse_proxy_list("YOUDO_PROXY_URLS", "YOUDO_PROXY_URL") or _secondary_exchange_pool()
    dc_hints = {_hint_from_url(u) for u in _youdo_dc_pool()}
    return [u for u in all_urls if _hint_from_url(u) not in dc_hints]


def youdo_dc_pool_size() -> int:
    return len(_youdo_dc_pool())


def youdo_dc_alive_urls() -> list[str]:
    _ensure_loaded()
    return _alive_urls(_youdo_dc_pool(), "youdo")


def youdo_ru_alive_urls() -> list[str]:
    _ensure_loaded()
    return _alive_urls(_youdo_ru_pool(), "youdo")


_YOUDO_POOL_KEY = "youdo"


def _youdo_dc_retry_max() -> int:
    raw = os.getenv("YOUDO_DC_RETRY_MAX", "").strip()
    if raw:
        try:
            return max(1, int(raw))
        except ValueError:
            pass
    raw = os.getenv("YOUDO_SLOT_RETRY_ON_TIMEOUT", "3").strip()
    try:
        cap = max(1, int(raw))
    except ValueError:
        cap = 3
    dc_n = youdo_dc_pool_size()
    return min(cap, dc_n) if dc_n else cap


def _youdo_ru_retry_max() -> int:
    raw = os.getenv("YOUDO_RU_RETRY_MAX", "5").strip()
    try:
        return max(0, int(raw))
    except ValueError:
        return 5


def _youdo_dc_slot_index_raw() -> int:
    dc_urls = _youdo_dc_pool()
    if not dc_urls:
        return 0
    _ensure_loaded()
    return _active_slot.get(_YOUDO_POOL_KEY, 0) % len(dc_urls)


def _resolve_youdo_dc_slot_index() -> int:
    """Active slot index within DC pool only (O260)."""
    dc_urls = _youdo_dc_pool()
    if not dc_urls:
        return 0
    _ensure_loaded()
    idx = _youdo_dc_slot_index_raw()
    if not _is_banned(dc_urls[idx], "youdo"):
        return idx
    for off in range(len(dc_urls)):
        j = (idx + off) % len(dc_urls)
        if not _is_banned(dc_urls[j], "youdo"):
            if j != idx:
                _active_slot[_YOUDO_POOL_KEY] = j
                _persist_bans()
            return j
    return idx


def _youdo_primary_dc_url() -> str:
    dc_urls = _youdo_dc_pool()
    dc_alive = youdo_dc_alive_urls()
    if not dc_alive or not dc_urls:
        return ""
    idx = _resolve_youdo_dc_slot_index()
    preferred = dc_urls[idx]
    if not _is_banned(preferred, "youdo"):
        return preferred
    return dc_alive[0]


def youdo_realign_to_dc_tier() -> bool:
    """O260: after ban TTL — active slot back to first alive DC."""
    _ensure_loaded()
    dc_urls = _youdo_dc_pool()
    dc_alive = youdo_dc_alive_urls()
    if not dc_urls or not dc_alive:
        return False
    first_idx = _index_of_url(dc_alive[0], dc_urls)
    old_idx = _youdo_dc_slot_index_raw()
    if old_idx == first_idx and not _is_banned(dc_urls[first_idx], "youdo"):
        return False
    _active_slot[_YOUDO_POOL_KEY] = first_idx
    _persist_bans()
    logger.info(
        "fetch:youdo tier=dc_restored dc_alive=%d/%d slot=%d",
        len(dc_alive),
        len(dc_urls),
        first_idx + 1,
    )
    return True


def _normalize_youdo_active_slot() -> None:
    """O260: persisted slot may index full YOUDO_PROXY_URLS (RU) — realign to DC pool."""
    dc_urls = _youdo_dc_pool()
    if not dc_urls:
        return
    _ensure_loaded()
    raw = _active_slot.get(_YOUDO_POOL_KEY, 0)
    if raw >= len(dc_urls):
        youdo_realign_to_dc_tier()


def youdo_listing_slot_urls(*, include_ru: bool = False) -> list[str]:
    """O260: ordered DC slots; RU (max 1) only when include_ru and all DC banned."""
    dc_alive = youdo_dc_alive_urls()
    if dc_alive:
        primary = _youdo_primary_dc_url()
        if primary:
            slots = [primary]
            slots.extend(u for u in dc_alive if u != primary)
            return _dedupe_urls(slots)
        return list(dc_alive)
    if include_ru:
        ru_alive = youdo_ru_alive_urls()
        return ru_alive[: _youdo_ru_retry_max()]
    return []


def youdo_browser_slot_urls() -> list[str]:
    """O260: DC carousel; RU only when all DC banned."""
    dc_alive = youdo_dc_alive_urls()
    if dc_alive:
        return youdo_listing_slot_urls(include_ru=False)
    return youdo_listing_slot_urls(include_ru=True)


def _urls_for_source(source: str) -> tuple[str, str, list[str]]:
    """pool_key, ban_source, urls."""
    src = (source or "").strip() or "exchange"
    if src == "fl":
        return _fl_pool_triple()
    if src == "kwork":
        urls = _parse_proxy_list("KWORK_PROXY_URLS", "KWORK_PROXY_URL")
        return src, src, urls or _primary_exchange_pool()
    if src == "youdo":
        urls = _parse_proxy_list("YOUDO_PROXY_URLS", "YOUDO_PROXY_URL")
        return src, src, urls or _secondary_exchange_pool()
    if src == "freelance_ru":
        urls = _parse_proxy_list("FREELANCE_RU_PROXY_URLS", "FREELANCE_RU_PROXY_URL")
        return src, src, urls or _secondary_exchange_pool()
    if src == "freelancejob":
        urls = _parse_proxy_list("FREELANCEJOB_PROXY_URLS", "FREELANCEJOB_PROXY_URL")
        return src, src, urls or _secondary_exchange_pool()
    if src == "pchyol":
        urls = _parse_proxy_list("PCHYOL_PROXY_URLS", "PCHYOL_PROXY_URL")
        return src, src, urls or _secondary_exchange_pool()
    if src in _PRIMARY_SOURCES:
        urls = _primary_exchange_pool()
        return src, src, urls
    urls = _secondary_exchange_pool()
    return src, src, urls


def _hint_from_url(url: str | None) -> str:
    if not url:
        return "direct"
    try:
        p = urlparse(url)
        return f"{p.hostname}:{p.port or ''}".rstrip(":")
    except Exception:
        return "proxy"


def _ban_key(url: str, source: str = "") -> str:
    src = (source or "").strip() or "exchange"
    return f"{src}:{_hint_from_url(url)}"


def _proxies_dict(url: str | None) -> dict[str, str | None]:
    if not url:
        return DIRECT_REQUESTS_PROXIES
    return {"http": url, "https": url}


def request_timeout_tuple() -> tuple[float, float]:
    return (_CONNECT_TIMEOUT_SEC, _READ_TIMEOUT_SEC)


def _storage():
    from config import load_config
    from storage import ProjectStorage

    cfg = load_config()
    return ProjectStorage(cfg.sqlite_path)


def _prune_expired_bans() -> None:
    now = time.time()
    _ensure_loaded()
    dc_before = len(youdo_dc_alive_urls())
    expired = [k for k, until in _banned_until.items() if until <= now]
    youdo_expired = [k for k in expired if k.startswith("youdo:")]
    for k in expired:
        _banned_until.pop(k, None)
        _ban_meta.pop(k, None)
    if youdo_expired and dc_before == 0:
        dc_after = len(youdo_dc_alive_urls())
        if dc_after > 0:
            youdo_realign_to_dc_tier()
    _youdo_update_dc_banned_since()


def _load_persistence() -> None:
    global _persistence_loaded
    if _persistence_loaded:
        return
    _persistence_loaded = True
    try:
        st = _storage()
        raw = st.get_setting(_BANS_STORAGE_KEY, "").strip()
        if raw:
            data = json.loads(raw)
            if isinstance(data, dict):
                now = time.time()
                for hint, meta in data.items():
                    if not isinstance(meta, dict):
                        continue
                    until = float(meta.get("until", 0))
                    if until > now:
                        _banned_until[str(hint)] = until
                        _ban_meta[str(hint)] = meta
        # v1 (глобальные баны) не подмешиваем — иначе снова «все в бане» для всех бирж
        slot_raw = st.get_setting(_ACTIVE_SLOT_KEY, "").strip()
        if slot_raw:
            slots = json.loads(slot_raw)
            if isinstance(slots, dict):
                for k, v in slots.items():
                    try:
                        _active_slot[str(k)] = int(v)
                    except (TypeError, ValueError):
                        pass
    except Exception as exc:
        logger.warning("fetch:proxy load persistence failed: %s", exc)
    _prune_fl_res_bans()
    _normalize_youdo_active_slot()


def _prune_fl_res_bans() -> None:
    """Residential FL slots are never auto-banned — drop stale persisted bans (O215)."""
    prefix = f"{_FL_RES_BAN_SOURCE}:"
    stale = [k for k in list(_banned_until) if k.startswith(prefix)]
    if not stale:
        return
    for k in stale:
        _banned_until.pop(k, None)
        _ban_meta.pop(k, None)
    logger.info("fetch:proxy cleared %d stale residential FL ban(s)", len(stale))


def clear_fl_source_bans(*, persist: bool = True) -> int:
    """Drop fl:* keys from ban table — full FL refresh without waiting TTL (O233)."""
    _ensure_loaded()
    prefix = "fl:"
    stale = [k for k in list(_banned_until) if k.startswith(prefix)]
    if not stale:
        return 0
    for k in stale:
        _banned_until.pop(k, None)
        _ban_meta.pop(k, None)
    if persist:
        _persist_bans()
    logger.info("fetch:proxy cleared %d FL ban(s)", len(stale))
    return len(stale)


def clear_youdo_source_bans(*, persist: bool = True, dc_only: bool = False) -> int:
    """Drop youdo:* keys from ban table — manual recovery / hard reset (O254/O261)."""
    _ensure_loaded()
    prefix = "youdo:"
    dc_hints: frozenset[str] | None = None
    if dc_only:
        dc_hints = frozenset(_hint_from_url(u) for u in _youdo_dc_pool())
    stale = [k for k in list(_banned_until) if k.startswith(prefix)]
    cleared = 0
    for k in stale:
        if dc_only:
            host = k.split(":", 1)[-1] if ":" in k else ""
            if host not in dc_hints:
                continue
        _banned_until.pop(k, None)
        _ban_meta.pop(k, None)
        cleared += 1
    if cleared and persist:
        _persist_bans()
    if cleared:
        logger.info(
            "fetch:proxy cleared %d YouDo ban(s)%s",
            cleared,
            " (DC only)" if dc_only else "",
        )
    _youdo_update_dc_banned_since()
    return cleared


def _youdo_max_dc_bans_per_fetch() -> int:
    raw = os.getenv("YOUDO_MAX_DC_BANS_PER_FETCH", "2").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 2


def _youdo_auto_unban_min_sec() -> float:
    raw = os.getenv("YOUDO_AUTO_UNBAN_MIN", "20").strip()
    try:
        return max(1.0, float(raw)) * 60.0
    except ValueError:
        return 20.0 * 60.0


def _fl_dead_proxy_ban_ttl_sec() -> float:
    raw = os.getenv("FL_DEAD_PROXY_BAN_TTL_SEC", "300").strip()
    try:
        return max(30.0, float(raw))
    except ValueError:
        return 300.0


def is_proxy_connection_error(exc: BaseException) -> bool:
    """True for dead/unreachable proxy (O261 FL httpx + browser rotate)."""
    msg = f"{type(exc).__name__} {exc}".casefold()
    markers = (
        "err_proxy_connection_failed",
        "net::err_proxy",
        "proxyerror",
        "proxy connection",
        "tunnel connection failed",
        "connect tunnel failed",
        "407 proxy",
        "unable to connect to proxy",
    )
    return any(m in msg for m in markers)


def youdo_proxy_in_dc_pool(proxy_url: str) -> bool:
    if not proxy_url:
        return False
    hint = _hint_from_url(proxy_url)
    return any(_hint_from_url(u) == hint for u in _youdo_dc_pool())


def _youdo_update_dc_banned_since() -> None:
    """Track when all YouDo DC slots became banned (O261 auto-unban timer)."""
    try:
        st = _storage()
    except Exception:
        return
    if youdo_dc_alive_urls():
        try:
            st.set_setting(_YOUDO_DC_BANNED_SINCE_KEY, "")
        except Exception:
            pass
        return
    try:
        if not st.get_setting(_YOUDO_DC_BANNED_SINCE_KEY, "").strip():
            st.set_setting(_YOUDO_DC_BANNED_SINCE_KEY, str(time.time()))
    except Exception:
        pass


def youdo_maybe_auto_unban_dc() -> bool:
    """Clear DC bans + hard reset when dc_alive=0 longer than YOUDO_AUTO_UNBAN_MIN."""
    _ensure_loaded()
    if youdo_dc_alive_urls():
        return False
    try:
        st = _storage()
    except Exception:
        return False
    raw = st.get_setting(_YOUDO_DC_BANNED_SINCE_KEY, "").strip()
    if not raw:
        _youdo_update_dc_banned_since()
        return False
    try:
        since = float(raw)
    except ValueError:
        _youdo_update_dc_banned_since()
        return False
    if time.time() - since < _youdo_auto_unban_min_sec():
        return False
    cleared = clear_youdo_source_bans(dc_only=True)
    try:
        st.set_setting(_YOUDO_DC_BANNED_SINCE_KEY, "")
    except Exception:
        pass
    youdo_realign_to_dc_tier()
    try:
        from youdo_parser import youdo_hard_reset

        youdo_hard_reset(reason="dc_auto_unban", storage=st)
    except Exception as exc:
        logger.warning("fetch:youdo dc_auto_unban hard_reset failed: %s", exc)
    logger.info("fetch:youdo tier=dc_auto_unban cleared=%d", cleared)
    return True


def fl_browser_dead_proxy_fail(
    proxy_url: str,
    *,
    reason: str = "dead_proxy",
) -> bool:
    """Ban dead FL DC proxy (short TTL) and advance to next alive DC (O261)."""
    _ensure_loaded()
    dc_urls = _fl_dc_pool()
    if not proxy_url or not dc_urls:
        return False
    failed_hint = _hint_from_url(proxy_url)
    if not any(_hint_from_url(u) == failed_hint for u in dc_urls):
        return False
    slot_idx = _index_of_url(proxy_url, dc_urls)
    _ban_url(
        proxy_url,
        source="fl",
        reason=reason,
        slot_idx=slot_idx,
        ttl_sec=_fl_dead_proxy_ban_ttl_sec(),
    )
    _invalidate_browser_slot_for_ban("fl", proxy_url)
    dc_alive = _alive_urls(dc_urls, "fl")
    if not dc_alive:
        return False
    cur = _active_slot.get("fl", 0) % len(dc_urls)
    start = 0
    for i, u in enumerate(dc_urls):
        if _hint_from_url(u) == failed_hint:
            start = i
            break
    for off in range(1, len(dc_urls) + 1):
        cand = dc_urls[(start + off) % len(dc_urls)]
        if not _is_banned(cand, "fl"):
            new_idx = _index_of_url(cand, dc_urls)
            if new_idx != cur:
                _apply_active_slot(
                    "fl",
                    dc_urls,
                    new_idx,
                    old_idx=cur,
                    reason=reason,
                    notify=True,
                )
            return True
    return False


def _index_of_url(url: str, urls: list[str]) -> int:
    hint = _hint_from_url(url)
    for i, u in enumerate(urls):
        if u == url or _hint_from_url(u) == hint:
            return i
    return 0


def youdo_browser_slot_fail(
    proxy_url: str,
    *,
    reason: str,
) -> bool:
    """Ban failed YouDo browser proxy and advance active slot within DC pool (O260)."""
    _ensure_loaded()
    source = "youdo"
    dc_urls = _youdo_dc_pool()
    ru_urls = _youdo_ru_pool()
    if not proxy_url:
        return False
    failed_hint = _hint_from_url(proxy_url)
    in_dc = any(_hint_from_url(u) == failed_hint for u in dc_urls)
    in_ru = any(_hint_from_url(u) == failed_hint for u in ru_urls)
    slot_idx = _index_of_url(proxy_url, dc_urls if in_dc else ru_urls or dc_urls)
    _ban_url(
        proxy_url,
        source=source,
        reason=reason,
        slot_idx=slot_idx,
    )
    _invalidate_browser_slot_for_ban("youdo", proxy_url)
    if in_dc and dc_urls:
        dc_alive = _alive_urls(dc_urls, source)
        if not dc_alive:
            ru_alive = _alive_urls(ru_urls, source)
            return bool(ru_alive)
        cur = _youdo_dc_slot_index_raw()
        start = 0
        for i, u in enumerate(dc_urls):
            if _hint_from_url(u) == failed_hint:
                start = i
                break
        for off in range(1, len(dc_urls) + 1):
            cand = dc_urls[(start + off) % len(dc_urls)]
            if not _is_banned(cand, source):
                new_idx = _index_of_url(cand, dc_urls)
                if new_idx != cur:
                    _apply_youdo_dc_slot(
                        new_idx,
                        old_idx=cur,
                        reason=reason,
                        notify=True,
                    )
                return True
    elif in_ru:
        return not _alive_urls(ru_urls, source)
    alive_dc, total_dc = _pool_counts(dc_urls, source)
    alive_ru, total_ru = _pool_counts(ru_urls, source)
    _send_owner_proxy_alert(
        f"{_PROXY_ALERT_PREFIX}\n\n"
        f"Источник: youdo\n"
        f"Забанен: {_slot_label(slot_idx)} ({_hint_from_url(proxy_url)})\n"
        f"Причина: {_reason_human(reason)}\n\n"
        f"🛑 Нет свободных прокси для youdo (DC {alive_dc}/{total_dc}, RU {alive_ru}/{total_ru}).",
        pool_exhausted=True,
    )
    return False


def _apply_youdo_dc_slot(
    new_idx: int,
    *,
    old_idx: int,
    reason: str,
    notify: bool,
) -> None:
    dc_urls = _youdo_dc_pool()
    if not dc_urls:
        return
    new_idx = new_idx % len(dc_urls)
    _active_slot[_YOUDO_POOL_KEY] = new_idx
    _persist_bans()
    logger.info(
        "fetch:proxy cascade switch pool=youdo_dc %s→%s slot=%s/%s reason=%s",
        _hint_from_url(dc_urls[old_idx % len(dc_urls)]),
        _hint_from_url(dc_urls[new_idx]),
        new_idx + 1,
        len(dc_urls),
        reason,
    )
    if notify and new_idx != old_idx:
        _notify_proxy_switch(
            dc_urls,
            source="youdo",
            old_idx=old_idx % len(dc_urls),
            new_idx=new_idx,
            reason=reason,
        )


def _persist_bans() -> None:
    _prune_expired_bans()
    try:
        st = _storage()
        payload = {
            hint: {
                **meta,
                "until": _banned_until[hint],
            }
            for hint, meta in _ban_meta.items()
            if hint in _banned_until
        }
        st.set_setting(_BANS_STORAGE_KEY, json.dumps(payload, ensure_ascii=False))
        st.set_setting(_ACTIVE_SLOT_KEY, json.dumps(_active_slot, ensure_ascii=False))
    except Exception as exc:
        logger.warning("fetch:proxy persist bans failed: %s", exc)


def _is_banned(url: str, source: str) -> bool:
    _ensure_loaded()
    if source == _FL_RES_BAN_SOURCE:
        return False
    key = _ban_key(url, source)
    until = _banned_until.get(key, 0.0)
    if until and time.time() >= until:
        _banned_until.pop(key, None)
        _ban_meta.pop(key, None)
        return False
    return time.time() < until


def _ensure_loaded() -> None:
    _load_persistence()


def _alive_urls(urls: list[str], source: str) -> list[str]:
    return [u for u in urls if not _is_banned(u, source)]


def _pool_counts(urls: list[str], source: str) -> tuple[int, int]:
    if not urls:
        return (0, 0)
    alive = len(_alive_urls(urls, source))
    return (alive, len(urls))


def _ban_url(
    url: str,
    *,
    source: str,
    reason: str,
    slot_idx: int | None = None,
    ttl_sec: float | None = None,
) -> None:
    if not url:
        return
    if source == _FL_RES_BAN_SOURCE:
        logger.info(
            "fetch:proxy skip residential ban %s reason=%s",
            _hint_from_url(url),
            reason,
        )
        return
    key = _ban_key(url, source)
    ttl = float(ttl_sec) if ttl_sec is not None else _BAN_TTL_SEC
    until = time.time() + ttl
    _banned_until[key] = until
    _ban_meta[key] = {
        "reason": reason,
        "banned_at": radar_timestamp(),
        "until": until,
        "slot": (slot_idx + 1) if slot_idx is not None else None,
        "source": source,
        "host": _hint_from_url(url),
    }
    _strike_count.pop(key, None)
    _persist_bans()
    logger.warning(
        "fetch:proxy banned %s reason=%s ttl=%.0fs",
        key,
        reason,
        ttl,
    )
    if source == "youdo":
        _youdo_update_dc_banned_since()


def _http_strike_key(url: str, source: str, http_code: int) -> str:
    return f"{_ban_key(url, source)}:http_{http_code}"


def _record_success(url: str, source: str) -> None:
    if not url:
        return
    key = _ban_key(url, source)
    _strike_count.pop(key, None)
    for code in _FAILOVER_HTTP:
        _strike_count.pop(_http_strike_key(url, source, code), None)


def _record_failure(url: str, *, source: str, http_code: int | None = None) -> bool:
    if not url:
        return False
    key = _ban_key(url, source)
    if http_code in _FAILOVER_HTTP:
        hk = _http_strike_key(url, source, http_code)
        n = _strike_count.get(hk, 0) + 1
        _strike_count[hk] = n
        return n >= _http_strikes_to_ban(source)
    n = _strike_count.get(key, 0) + 1
    _strike_count[key] = n
    return n >= _STRIKES_TO_BAN


def _slot_label(idx: int) -> str:
    return f"Proxy_{idx + 1}"


def _reason_human(reason: str) -> str:
    if reason.startswith("http_"):
        return f"HTTP {reason[5:]}"
    if reason.startswith("timeout:"):
        return f"сеть ({reason[8:]})"
    if reason.startswith("strikes_"):
        return f"обрывы ×{reason.split('_', 1)[-1]}"
    return reason


def _format_until(hint: str) -> str:
    meta = _ban_meta.get(hint) or {}
    banned_at = str(meta.get("banned_at", "")).strip()
    if banned_at:
        return banned_at
    until = _banned_until.get(hint, 0.0)
    if until:
        return time.strftime("%H:%M", time.localtime(until))
    return "?"


def _banned_list_text(urls: list[str], source: str) -> str:
    lines: list[str] = []
    for i, u in enumerate(urls):
        key = _ban_key(u, source)
        if _is_banned(u, source):
            meta = _ban_meta.get(key) or {}
            reason = _reason_human(str(meta.get("reason", "ban")))
            host = _hint_from_url(u)
            lines.append(f"  · {_slot_label(i)} {host} — {reason}")
    return "\n".join(lines) if lines else "  · (нет)"


def _send_owner_proxy_alert(
    text: str,
    *,
    force: bool = False,
    low_pool: bool = False,
    pool_exhausted: bool = False,
) -> None:
    global _last_owner_alert_at, _last_pool_exhausted_alert_at
    now = time.time()
    cooldown = _ALERT_LOW_POOL_SEC if low_pool else _ALERT_COOLDOWN_SEC
    if pool_exhausted:
        if now - _last_pool_exhausted_alert_at < cooldown:
            return
        _last_pool_exhausted_alert_at = now
    elif not force and now - _last_owner_alert_at < cooldown:
        return
    _last_owner_alert_at = now
    try:
        from health_check import send_flparsing_admin_text

        ok, err = send_flparsing_admin_text(text)
        if not ok:
            logger.warning("fetch:proxy tg alert failed: %s", err)
    except Exception as exc:
        logger.warning("fetch:proxy tg alert error: %s", exc)


def _failover_cooldown_sleep(*, reason: str, banned_url: str | None) -> None:
    """Pause 5–15s before next proxy slot after ban (O110-B)."""
    if not banned_url and not str(reason).startswith("http_"):
        return
    lo = max(0.0, _FAILOVER_COOLDOWN_MIN_SEC)
    hi = max(lo, _FAILOVER_COOLDOWN_MAX_SEC)
    if hi <= 0:
        return
    delay = random.uniform(lo, hi)
    if delay > 0:
        logger.info("fetch:proxy cooldown %.1fs (%s)", delay, reason)
        time.sleep(delay)


def _invalidate_browser_slot_for_ban(source: str, proxy_url: str) -> None:
    try:
        from exchange_browser_fetch import invalidate_browser_slot

        invalidate_browser_slot(source, proxy_url)
    except Exception as exc:
        logger.debug("fetch:proxy browser invalidate skipped: %s", exc)


def _notify_proxy_switch(
    urls: list[str],
    *,
    source: str,
    old_idx: int,
    new_idx: int,
    reason: str,
) -> None:
    if not urls:
        return
    old_hint = _hint_from_url(urls[old_idx % len(urls)])
    new_hint = _hint_from_url(urls[new_idx % len(urls)])
    alive, total = _pool_counts(urls, source)
    banned_n = total - alive

    lines = [
        _PROXY_ALERT_PREFIX,
        f"Источник: {source}",
        "",
        f"Забанен: {_slot_label(old_idx)} ({old_hint})",
        f"Причина: {_reason_human(reason)}",
        "",
        f"Подключились: {_slot_label(new_idx)} ({new_hint})",
        "",
        f"Свободно для {source}: {alive} из {total}",
        f"В бане у {source}: {banned_n}",
    ]
    if banned_n:
        lines.append("Список банов:")
        lines.append(_banned_list_text(urls, source))

    if alive <= 1:
        lines.append("")
        lines.append("⚠️ Остался последний прокси — докупи или смени IP в панели.")
    if alive == 0:
        lines.append("")
        lines.append(f"🛑 Для {source} нет живых прокси — fetch пропущен до TTL.")

    force = alive <= 1
    _send_owner_proxy_alert("\n".join(lines), force=force, low_pool=alive <= 2)


def _slot_index(pool_key: str, urls: list[str], source: str) -> int:
    if not urls:
        return 0
    _ensure_loaded()
    alive = _alive_urls(urls, source)
    if not alive:
        return 0
    idx = _active_slot.get(pool_key, 0) % len(urls)
    if not _is_banned(urls[idx], source):
        return idx
    for off in range(len(urls)):
        j = (idx + off) % len(urls)
        if not _is_banned(urls[j], source):
            _active_slot[pool_key] = j
            _persist_bans()
            return j
    return idx


def _apply_active_slot(
    pool_key: str,
    urls: list[str],
    new_idx: int,
    *,
    old_idx: int,
    reason: str,
    notify: bool,
) -> None:
    if not urls:
        return
    new_idx = new_idx % len(urls)
    _active_slot[pool_key] = new_idx
    _persist_bans()
    logger.info(
        "fetch:proxy cascade switch pool=%s %s→%s slot=%s/%s reason=%s",
        pool_key,
        _hint_from_url(urls[old_idx]),
        _hint_from_url(urls[new_idx]),
        new_idx + 1,
        len(urls),
        reason,
    )
    if notify and (new_idx != old_idx):
        _notify_proxy_switch(
            urls,
            source=pool_key,
            old_idx=old_idx,
            new_idx=new_idx,
            reason=reason,
        )


def exchange_pool_health(source: str) -> tuple[int, int]:
    _key, ban_source, urls = _urls_for_source(source)
    return _pool_counts(urls, ban_source)


def exchange_alive_proxy_urls(source: str) -> list[str]:
    """Живые слоты прокси для source (browser retry, O63 YouDo)."""
    _ensure_loaded()
    if source == "youdo":
        return youdo_browser_slot_urls()
    if source == "fl":
        return fl_browser_slot_urls()
    _key, ban_source, urls = _urls_for_source(source)
    if not urls:
        return []
    alive = _alive_urls(urls, ban_source)
    return alive if alive else []


def _pool_status_slice(urls: list[str], source: str, pool_key: str) -> dict[str, Any]:
    _ensure_loaded()
    alive, total = _pool_counts(urls, source)
    slot = _active_slot.get(pool_key, _active_slot.get(source, 0))
    alive_list = _alive_urls(urls, source)
    if alive_list:
        active_hint = _hint_from_url(alive_list[0])
        for i, u in enumerate(urls):
            if u == alive_list[0]:
                slot = i
                break
    else:
        active_hint = _hint_from_url(urls[slot % len(urls)]) if urls else "direct"
    banned = [
        {
            "slot": i + 1,
            "host": _hint_from_url(u),
            "source": source,
            "reason": (_ban_meta.get(_ban_key(u, source)) or {}).get("reason"),
        }
        for i, u in enumerate(urls)
        if _is_banned(u, source)
    ]
    return {
        "source": source,
        "pool_size": total,
        "active_slot": slot + 1 if urls else 0,
        "active_host": active_hint,
        "alive": alive,
        "total": total,
        "banned": banned,
    }


def cascade_status_summary() -> dict[str, Any]:
    """Для /status и watchdog: primary (fl) + youdo DC tier (O260)."""
    primary_urls = _fl_dc_pool()
    fl = _pool_status_slice(primary_urls, "fl", "fl")
    youdo_dc = _youdo_dc_pool()
    youdo = _pool_status_slice(youdo_dc, "youdo", _YOUDO_POOL_KEY)
    ru_alive = len(youdo_ru_alive_urls())
    ru_total = len(_youdo_ru_pool())
    youdo["ru_alive"] = ru_alive
    youdo["ru_total"] = ru_total
    youdo["tier"] = "dc" if youdo.get("alive", 0) else ("ru" if ru_alive else "exhausted")
    return {
        **fl,
        "primary": fl,
        "secondary": youdo,
        "secondary_total": len(youdo_dc) + ru_total,
    }


@dataclass
class ExchangeFetchSession:
    pool_key: str
    source: str
    urls: list[str]
    slot: int = 0
    try_offset: int = 0

    @property
    def current_url(self) -> str | None:
        ordered = self.urls
        if not ordered:
            return None
        if not _alive_urls(ordered, self.source):
            return None
        base = (self.slot + self.try_offset) % len(ordered)
        for off in range(len(ordered)):
            idx = (base + off) % len(ordered)
            url = ordered[idx]
            if not _is_banned(url, self.source):
                return url
        return None

    def current_proxies(self) -> dict[str, str | None]:
        if self.current_url:
            return _proxies_dict(self.current_url)
        if self.urls:
            raise requests.RequestException(
                f"exchange_proxy:{self.source}: pool exhausted, no alive proxy"
            )
        return DIRECT_REQUESTS_PROXIES

    def log_hint(self) -> str:
        alive, total = _pool_counts(self.urls, self.source)
        slot_n = self.slot + 1 if self.urls else 0
        host = _hint_from_url(self.current_url)
        if self.urls and not self.current_url:
            host = "pool_exhausted"
        elif self.source == _FL_RES_BAN_SOURCE and host not in ("direct", "pool_exhausted"):
            host = f"{host} res"
        return f"{host} slot={slot_n}/{total} alive={alive}/{total}"

    def advance_failover(self, *, reason: str, banned_url: str | None = None) -> bool:
        if not self.urls:
            return False
        old_idx = self.slot
        if banned_url:
            _ban_url(
                banned_url,
                source=self.source,
                reason=reason,
                slot_idx=old_idx,
            )
            _invalidate_browser_slot_for_ban(self.source, banned_url)
            if self.source in ("fl", _FL_RES_BAN_SOURCE) and _fl_hard_reset_on_ban_enabled():
                try:
                    from exchange_browser_fetch import fl_hard_reset

                    fl_hard_reset(reason=reason, storage=_storage())
                except Exception as exc:
                    logger.warning("fetch:fl hard_reset on failover failed: %s", exc)
                return False
            _failover_cooldown_sleep(reason=reason, banned_url=banned_url)
        for off in range(1, len(self.urls) + 1):
            idx = (old_idx + off) % len(self.urls)
            if _is_banned(self.urls[idx], self.source):
                continue
            notify = bool(banned_url) or idx != old_idx
            self.slot = idx
            self.try_offset = 0
            _apply_active_slot(
                self.pool_key,
                self.urls,
                idx,
                old_idx=old_idx,
                reason=reason,
                notify=notify,
            )
            return True
        alive, total = _pool_counts(self.urls, self.source)
        _send_owner_proxy_alert(
            f"{_PROXY_ALERT_PREFIX}\n\n"
            f"Источник: {self.source}\n"
            + (
                f"Забанен: {_slot_label(old_idx)} ({_hint_from_url(banned_url or '')})\n"
                f"Причина: {_reason_human(reason)}\n\n"
                if banned_url
                else ""
            )
            + f"🛑 Нет свободных прокси для {self.source} ({alive}/{total}).",
            pool_exhausted=True,
        )
        return False


def exchange_fetch_begin(source: str) -> ExchangeFetchSession:
    _ensure_loaded()
    _prune_expired_bans()
    pool_key, ban_source, urls = _urls_for_source(source)
    youdo_dc_urls: list[str] = []
    if source == "youdo":
        youdo_maybe_auto_unban_dc()
        _prune_expired_bans()
        youdo_dc_urls = _youdo_dc_pool()
        if youdo_dc_urls:
            urls = youdo_dc_urls
            pool_key = _YOUDO_POOL_KEY
    if not urls:
        session = ExchangeFetchSession(pool_key=pool_key, source=ban_source, urls=[])
        _sessions[source] = session
        logger.info("fetch:%s proxy=direct", source)
        return session
    slot = _slot_index(pool_key, urls, ban_source)
    if source == "youdo" and youdo_dc_urls:
        slot = _resolve_youdo_dc_slot_index()
    session = ExchangeFetchSession(pool_key=pool_key, source=ban_source, urls=urls, slot=slot)
    alive, total = _pool_counts(urls, ban_source)
    dc_exhausted = source == "fl" and ban_source == "fl" and alive == 0 and bool(_fl_residential_pool())
    if alive == 0:
        if dc_exhausted:
            logger.warning(
                "fetch:%s DC proxy tier exhausted (0/%s) — residential fallback next",
                source,
                total,
            )
        else:
            logger.error(
                "fetch:%s proxy pool exhausted (0/%s alive) pool=%s tier=%s",
                source,
                total,
                pool_key,
                ban_source,
            )
            _send_owner_proxy_alert(
                f"{_PROXY_ALERT_PREFIX}\n\n"
                f"🛑 Для {source}: 0/{total} прокси (tier={ban_source}).\n"
                f"Ждём TTL {_BAN_TTL_SEC / 60:.0f} мин или clear-vps-proxy-bans.py",
                pool_exhausted=True,
            )
    else:
        tier_note = " res" if ban_source == _FL_RES_BAN_SOURCE else ""
        logger.info(
            "fetch:%s proxy=%s%s cascade slot=%s/%s alive=%s/%s",
            source,
            _hint_from_url(session.current_url),
            tier_note,
            slot + 1,
            total,
            alive,
            total,
        )
    try:
        from exchange_trace import log_exchange_trace

        log_exchange_trace(
            source,
            stage="proxy_pick",
            proxy=_hint_from_url(session.current_url),
            alive=alive,
            total=total,
            err="pool_exhausted" if urls and alive == 0 else "",
        )
    except Exception:
        pass
    _sessions[source] = session
    return session


def exchange_fetch_end(source: str) -> None:
    _sessions.pop(source, None)


def _active_session(source: str) -> ExchangeFetchSession | None:
    return _sessions.get(source)


def exchange_primary_proxy_url(source: str) -> str:
    if source == "youdo":
        dc_url = _youdo_primary_dc_url()
        if dc_url:
            return dc_url
        ru_alive = youdo_ru_alive_urls()
        return ru_alive[0] if ru_alive else ""
    pool_key, ban_source, urls = _urls_for_source(source)
    if not urls:
        return ""
    slot = _slot_index(pool_key, urls, ban_source)
    u = urls[slot % len(urls)]
    alive = _alive_urls(urls, ban_source)
    return u if not _is_banned(u, ban_source) else (alive[0] if alive else "")


def requests_proxies_for(source: str) -> dict[str, str | None]:
    session = _active_session(source)
    if session:
        return session.current_proxies()
    pool_key, ban_source, urls = _urls_for_source(source)
    if not urls:
        return DIRECT_REQUESTS_PROXIES
    alive = _alive_urls(urls, ban_source)
    if not alive:
        return DIRECT_REQUESTS_PROXIES
    slot = _slot_index(pool_key, urls, ban_source)
    u = urls[slot % len(urls)]
    if _is_banned(u, ban_source):
        u = alive[0]
    return _proxies_dict(u)


def proxy_log_hint(source: str) -> str:
    session = _active_session(source)
    if session and source != "youdo":
        return session.log_hint()
    if source == "youdo":
        dc_urls = _youdo_dc_pool()
        dc_alive = youdo_dc_alive_urls()
        dc_total = len(dc_urls)
        dc_alive_n = len(dc_alive)
        ru_alive_n = len(youdo_ru_alive_urls())
        if dc_alive and dc_urls:
            idx = _resolve_youdo_dc_slot_index()
            u = dc_urls[idx]
            if _is_banned(u, "youdo"):
                u = dc_alive[0]
            hint = _hint_from_url(u)
            base = (
                f"{hint} tier=dc slot={idx + 1}/{dc_total} "
                f"alive={dc_alive_n}/{dc_total}"
            )
            if ru_alive_n:
                base += f" ru_alive={ru_alive_n}"
            return base
        if ru_alive_n:
            ru_urls = youdo_ru_alive_urls()
            u = ru_urls[0]
            return (
                f"{_hint_from_url(u)} tier=ru slot=1/1 "
                f"alive={ru_alive_n}/{len(_youdo_ru_pool())} dc_alive=0/{dc_total}"
            )
        if dc_urls:
            return f"pool_exhausted tier=dc slot=0/{dc_total} alive=0/{dc_total}"
        return "direct"
    pool_key, ban_source, urls = _urls_for_source(source)
    if not urls:
        return "direct"
    slot = _slot_index(pool_key, urls, ban_source)
    alive, total = _pool_counts(urls, ban_source)
    u = urls[slot % len(urls)]
    alive_list = _alive_urls(urls, ban_source)
    if _is_banned(u, ban_source) and alive_list:
        u = alive_list[0]
    hint = _hint_from_url(u)
    if ban_source == _FL_RES_BAN_SOURCE and hint != "direct":
        hint = f"{hint} res"
    if urls and not alive_list:
        hint = "pool_exhausted"
    return f"{hint} slot={slot + 1}/{total} alive={alive}/{total}"


def exchange_get(
    source: str,
    url: str,
    *,
    headers: dict[str, str],
    timeout_sec: float | tuple[float, float] | None = None,
    max_bans: int | None = None,
) -> requests.Response:
    if timeout_sec is None:
        timeout = request_timeout_tuple()
    elif isinstance(timeout_sec, tuple):
        timeout = timeout_sec
    else:
        timeout = (_CONNECT_TIMEOUT_SEC, float(timeout_sec))

    session = _active_session(source)
    own_session = session is None
    if own_session:
        session = exchange_fetch_begin(source)
    assert session is not None
    if not session.current_url and session.urls:
        raise requests.RequestException(
            f"exchange_get:{source}: all proxies banned (0/{len(session.urls)} alive)"
        )

    max_attempts = max(4, len(session.urls) * (_STRIKES_TO_BAN + 1))
    if max_bans is not None:
        max_attempts = min(max_attempts, max(1, max_bans + 1))
    attempts = 0
    bans_used = 0
    ban_source = session.source
    try:
        while attempts < max_attempts:
            attempts += 1
            proxy_url = session.current_url
            if not proxy_url:
                break
            t0 = time.monotonic()
            try:
                resp = requests.get(
                    url,
                    headers=headers,
                    timeout=timeout,
                    proxies=session.current_proxies(),
                )
            except requests.RequestException as exc:
                ms = int((time.monotonic() - t0) * 1000)
                try:
                    from exchange_trace import log_exchange_trace

                    log_exchange_trace(
                        source,
                        stage="html",
                        ms=ms,
                        proxy=_hint_from_url(proxy_url),
                        err=type(exc).__name__,
                    )
                except Exception:
                    pass
                if ban_source == "fl" and is_proxy_connection_error(exc):
                    if fl_browser_dead_proxy_fail(
                        proxy_url,
                        reason=f"dead_proxy:{type(exc).__name__}",
                    ):
                        bans_used += 1
                        if session.urls:
                            session.slot = _active_slot.get("fl", session.slot) % len(
                                session.urls
                            )
                        logger.warning(
                            "fetch:fl stage=dead_proxy_rotate httpx proxy=%s err=%s",
                            _hint_from_url(proxy_url),
                            type(exc).__name__,
                        )
                        if max_bans is not None and bans_used >= max_bans:
                            raise requests.RequestException(
                                f"exchange_get:{source}: max_bans={max_bans} reached"
                            ) from exc
                        continue
                if _record_failure(proxy_url, source=ban_source, http_code=None):
                    if session.advance_failover(
                        reason=f"timeout:{type(exc).__name__}",
                        banned_url=proxy_url,
                    ):
                        bans_used += 1
                        if max_bans is not None and bans_used >= max_bans:
                            raise requests.RequestException(
                                f"exchange_get:{source}: max_bans={max_bans} reached"
                            ) from exc
                        logger.warning(
                            "fetch:%s proxy=%s failover after error: %s",
                            source,
                            session.log_hint(),
                            exc,
                        )
                        continue
                else:
                    logger.warning(
                        "fetch:%s proxy=%s retry same slot (%s/%s): %s",
                        source,
                        _hint_from_url(proxy_url),
                        _strike_count.get(_ban_key(proxy_url, source), 0),
                        _STRIKES_TO_BAN,
                        exc,
                    )
                    continue
                raise
            ms = int((time.monotonic() - t0) * 1000)
            if resp.status_code in _FAILOVER_HTTP:
                ban_slot = _record_failure(
                    proxy_url, source=ban_source, http_code=resp.status_code
                )
                try:
                    from exchange_trace import log_exchange_trace

                    log_exchange_trace(
                        source,
                        stage="html",
                        ms=ms,
                        proxy=_hint_from_url(proxy_url),
                        http=resp.status_code,
                        ban=int(_BAN_TTL_SEC) if ban_slot else 0,
                        err=f"http_{resp.status_code}",
                    )
                except Exception:
                    pass
                if session.advance_failover(
                    reason=f"http_{resp.status_code}",
                    banned_url=proxy_url if ban_slot else None,
                ):
                    if ban_slot:
                        bans_used += 1
                        if max_bans is not None and bans_used >= max_bans:
                            return resp
                    logger.warning(
                        "fetch:%s proxy=%s failover after HTTP %s ban=%s",
                        source,
                        session.log_hint(),
                        resp.status_code,
                        ban_slot,
                    )
                    continue
                return resp
            _record_success(proxy_url, ban_source)
            try:
                from exchange_trace import log_exchange_trace

                log_exchange_trace(
                    source,
                    stage="html",
                    ms=ms,
                    proxy=_hint_from_url(proxy_url),
                    http=resp.status_code,
                )
            except Exception:
                pass
            return resp
        raise requests.RequestException(
            f"exchange_get:{source}: proxy cascade exhausted ({max_attempts} attempts)"
        )
    finally:
        if own_session:
            exchange_fetch_end(source)


def _exchange_ui_group(
    *,
    group_id: str,
    title: str,
    pool_key: str,
    source: str,
    urls: list[str],
) -> dict[str, Any]:
    from proxy_ops import mask, slot_status_label

    _ensure_loaded()
    if not urls:
        return {
            "id": group_id,
            "title": title,
            "active_slot": 0,
            "slots": [],
        }
    slot_idx = _slot_index(pool_key, urls, source)
    slots: list[dict[str, Any]] = []
    for i, url in enumerate(urls):
        banned = _is_banned(url, source)
        key = _ban_key(url, source)
        strikes_n = _strike_count.get(key, 0)
        if banned:
            status = "bad"
        elif strikes_n > 0:
            status = "warn"
        else:
            status = "ok"
        until_ts = _banned_until.get(key) if banned else None
        banned_until = None
        if until_ts and until_ts > time.time():
            banned_until = datetime.fromtimestamp(until_ts, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        meta = _ban_meta.get(key) or {}
        reason_raw = meta.get("reason") if banned else None
        slots.append(
            {
                "slot": i + 1,
                "mask": mask(url),
                "status": status,
                "status_label": slot_status_label(
                    status=status,
                    banned_until=banned_until,
                    reason_raw=str(reason_raw) if reason_raw else None,
                ),
                "active": i == slot_idx,
                "banned_until": banned_until,
                "reason": _reason_human(str(reason_raw)) if reason_raw else None,
                "strikes": f"{strikes_n}/{_STRIKES_TO_BAN}",
                "_url": url,
            }
        )
    return {
        "id": group_id,
        "title": title,
        "active_slot": slot_idx + 1,
        "slots": slots,
    }


def list_ui_groups() -> list[dict[str, Any]]:
    """Exchange proxy groups for /ops/."""
    fl_urls = _fl_dc_pool()
    kw_urls = _parse_proxy_list("KWORK_PROXY_URLS", "KWORK_PROXY_URL") or _primary_exchange_pool()
    youdo_dc = _youdo_dc_pool()
    youdo_group = _exchange_ui_group(
        group_id="exchange-pool",
        title="YouDo DC",
        pool_key=_YOUDO_POOL_KEY,
        source="youdo",
        urls=youdo_dc,
    )
    ru_alive, ru_total = _pool_counts(_youdo_ru_pool(), "youdo")
    youdo_group["ru_alive"] = ru_alive
    youdo_group["ru_total"] = ru_total
    fl_group = _exchange_ui_group(
        group_id="exchange-fl",
        title="FL",
        pool_key="fl",
        source="fl",
        urls=fl_urls,
    )
    if fl_on_residential_tier():
        alive, total = fl_residential_counts()
        fl_group["residential_active"] = True
        fl_group["res_alive"] = alive
        fl_group["res_total"] = total
    return [
        fl_group,
        _exchange_ui_group(
            group_id="exchange-kwork",
            title="Kwork",
            pool_key="kwork",
            source="kwork",
            urls=kw_urls,
        ),
        youdo_group,
    ]


def set_active_slot_manual(group_id: str, slot_1based: int) -> tuple[bool, str]:
    """Manual switch for exchange pools (1-based), без restart radar."""
    mapping = {
        "exchange-fl": ("fl", "fl", _fl_dc_pool()),
        "exchange-kwork": (
            "kwork",
            "kwork",
            _parse_proxy_list("KWORK_PROXY_URLS", "KWORK_PROXY_URL") or _primary_exchange_pool(),
        ),
        "exchange-pool": ("youdo", "youdo", _youdo_dc_pool()),
    }
    entry = mapping.get((group_id or "").strip().lower())
    if not entry:
        return False, f"Неизвестная группа: {group_id}"
    pool_key, source, urls = entry
    if not urls:
        return False, "Пул пуст"
    idx = int(slot_1based) - 1
    if idx < 0 or idx >= len(urls):
        return False, f"Слот {slot_1based} не существует"
    if _is_banned(urls[idx], source):
        return False, f"Слот {slot_1based} забанен"
    old_idx = _active_slot.get(pool_key, 0) % len(urls)
    _apply_active_slot(
        pool_key,
        urls,
        idx,
        old_idx=old_idx,
        reason="manual_ops",
        notify=False,
    )
    return True, f"Активен слот {slot_1based} ({_hint_from_url(urls[idx])})"


def clear_all_bans() -> int:
    """Clear exchange proxy bans/strikes in SQLite (ops /ops/ clear-bans)."""
    _ensure_loaded()
    n = len(_banned_until) + len(_strike_count)
    _banned_until.clear()
    _ban_meta.clear()
    _strike_count.clear()
    _persist_bans()
    return n


def reset_cascade_state_for_tests() -> None:
    _sessions.clear()
    _banned_until.clear()
    _ban_meta.clear()
    _strike_count.clear()
    _active_slot.clear()
    global _last_owner_alert_at, _last_pool_exhausted_alert_at, _persistence_loaded
    _last_owner_alert_at = 0.0
    _last_pool_exhausted_alert_at = 0.0
    _persistence_loaded = False
