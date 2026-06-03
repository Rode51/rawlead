"""Sticky cascade прокси для fetch бирж (FL/Kwork и др., не TG).

Primary pool (FL/Kwork): EXCHANGE_PROXY_URLS — баны per-source (fl / kwork).
Secondary (YouDo, Пчёл, …): EXCHANGE_PROXY_URLS_SECONDARY или primary + TELETHON acc2/3.
403/429 → бан только для этого source; connect — 3 подряд.
"""

from __future__ import annotations

import json
import logging
import os
import time
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
_CONNECT_TIMEOUT_SEC = float(os.getenv("EXCHANGE_PROXY_CONNECT_TIMEOUT_SEC", "5"))
_READ_TIMEOUT_SEC = float(os.getenv("EXCHANGE_PROXY_READ_TIMEOUT_SEC", "20"))
_ALERT_COOLDOWN_SEC = float(os.getenv("EXCHANGE_PROXY_ALERT_COOLDOWN_SEC", "600"))
_ALERT_LOW_POOL_SEC = float(os.getenv("EXCHANGE_PROXY_LOW_POOL_COOLDOWN_SEC", "300"))

_BANS_STORAGE_KEY = "exchange_proxy_bans_v2"
_BANS_STORAGE_KEY_LEGACY = "exchange_proxy_bans_v1"
_ACTIVE_SLOT_KEY = "exchange_proxy_active_slot_v1"
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


def _urls_for_source(source: str) -> tuple[str, list[str]]:
    src = (source or "").strip() or "exchange"
    if src == "fl":
        urls = _parse_proxy_list("FL_PROXY_URLS", "FL_PROXY_URL")
        return src, urls or _primary_exchange_pool()
    if src == "kwork":
        urls = _parse_proxy_list("KWORK_PROXY_URLS", "KWORK_PROXY_URL")
        return src, urls or _primary_exchange_pool()
    if src == "youdo":
        urls = _parse_proxy_list("YOUDO_PROXY_URLS", "YOUDO_PROXY_URL")
        return src, urls or _secondary_exchange_pool()
    if src == "freelance_ru":
        urls = _parse_proxy_list("FREELANCE_RU_PROXY_URLS", "FREELANCE_RU_PROXY_URL")
        return src, urls or _secondary_exchange_pool()
    if src == "freelancejob":
        urls = _parse_proxy_list("FREELANCEJOB_PROXY_URLS", "FREELANCEJOB_PROXY_URL")
        return src, urls or _secondary_exchange_pool()
    if src == "pchyol":
        urls = _parse_proxy_list("PCHYOL_PROXY_URLS", "PCHYOL_PROXY_URL")
        return src, urls or _secondary_exchange_pool()
    if src in _PRIMARY_SOURCES:
        return src, _primary_exchange_pool()
    return src, _secondary_exchange_pool()


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
    expired = [k for k, until in _banned_until.items() if until <= now]
    for k in expired:
        _banned_until.pop(k, None)
        _ban_meta.pop(k, None)


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
) -> None:
    if not url:
        return
    key = _ban_key(url, source)
    until = time.time() + _BAN_TTL_SEC
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
        _BAN_TTL_SEC,
    )


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
        return n >= _HTTP_STRIKES_TO_BAN
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
    _key, urls = _urls_for_source(source)
    return _pool_counts(urls, source)


def exchange_alive_proxy_urls(source: str) -> list[str]:
    """Живые слоты прокси для source (browser retry, O63 YouDo)."""
    _ensure_loaded()
    _key, urls = _urls_for_source(source)
    if not urls:
        return []
    alive = _alive_urls(urls, source)
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
    """Для /status и watchdog: primary (fl) + secondary (youdo)."""
    primary_urls = _primary_exchange_pool()
    secondary_urls = _secondary_exchange_pool()
    fl = _pool_status_slice(primary_urls, "fl", "fl")
    sec = _pool_status_slice(secondary_urls, "youdo", "youdo")
    return {
        **fl,
        "primary": fl,
        "secondary": sec,
        "secondary_total": len(secondary_urls),
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
    pool_key, urls = _urls_for_source(source)
    if not urls:
        session = ExchangeFetchSession(pool_key=pool_key, source=source, urls=[])
        _sessions[source] = session
        logger.info("fetch:%s proxy=direct", source)
        return session
    slot = _slot_index(pool_key, urls, source)
    session = ExchangeFetchSession(pool_key=pool_key, source=source, urls=urls, slot=slot)
    alive, total = _pool_counts(urls, source)
    if alive == 0:
        logger.error(
            "fetch:%s proxy pool exhausted (0/%s alive) pool=%s",
            source,
            total,
            pool_key,
        )
        _send_owner_proxy_alert(
            f"{_PROXY_ALERT_PREFIX}\n\n"
            f"🛑 Для {source}: 0/{total} прокси (баны только у этого источника).\n"
            f"Ждём TTL {_BAN_TTL_SEC / 60:.0f} мин или clear-vps-proxy-bans.py",
            pool_exhausted=True,
        )
    else:
        logger.info(
            "fetch:%s proxy=%s cascade slot=%s/%s alive=%s/%s",
            source,
            _hint_from_url(session.current_url),
            slot + 1,
            total,
            alive,
            total,
        )
    _sessions[source] = session
    return session


def exchange_fetch_end(source: str) -> None:
    _sessions.pop(source, None)


def _active_session(source: str) -> ExchangeFetchSession | None:
    return _sessions.get(source)


def exchange_primary_proxy_url(source: str) -> str:
    pool_key, urls = _urls_for_source(source)
    if not urls:
        return ""
    slot = _slot_index(pool_key, urls, source)
    u = urls[slot % len(urls)]
    alive = _alive_urls(urls, source)
    return u if not _is_banned(u, source) else (alive[0] if alive else "")


def requests_proxies_for(source: str) -> dict[str, str | None]:
    session = _active_session(source)
    if session:
        return session.current_proxies()
    pool_key, urls = _urls_for_source(source)
    if not urls:
        return DIRECT_REQUESTS_PROXIES
    alive = _alive_urls(urls, source)
    if not alive:
        return DIRECT_REQUESTS_PROXIES
    slot = _slot_index(pool_key, urls, source)
    u = urls[slot % len(urls)]
    if _is_banned(u, source):
        u = alive[0]
    return _proxies_dict(u)


def proxy_log_hint(source: str) -> str:
    session = _active_session(source)
    if session:
        return session.log_hint()
    pool_key, urls = _urls_for_source(source)
    if not urls:
        return "direct"
    slot = _slot_index(pool_key, urls, source)
    alive, total = _pool_counts(urls, source)
    u = urls[slot % len(urls)]
    alive_list = _alive_urls(urls, source)
    if _is_banned(u, source) and alive_list:
        u = alive_list[0]
    return f"{_hint_from_url(u)} slot={slot + 1}/{total} alive={alive}/{total}"


def exchange_get(
    source: str,
    url: str,
    *,
    headers: dict[str, str],
    timeout_sec: float | tuple[float, float] | None = None,
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
    attempts = 0
    try:
        while attempts < max_attempts:
            attempts += 1
            proxy_url = session.current_url
            if not proxy_url:
                break
            try:
                resp = requests.get(
                    url,
                    headers=headers,
                    timeout=timeout,
                    proxies=session.current_proxies(),
                )
            except requests.RequestException as exc:
                if _record_failure(proxy_url, source=source, http_code=None):
                    if session.advance_failover(
                        reason=f"timeout:{type(exc).__name__}",
                        banned_url=proxy_url,
                    ):
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
            if resp.status_code in _FAILOVER_HTTP:
                ban_slot = _record_failure(
                    proxy_url, source=source, http_code=resp.status_code
                )
                if session.advance_failover(
                    reason=f"http_{resp.status_code}",
                    banned_url=proxy_url if ban_slot else None,
                ):
                    logger.warning(
                        "fetch:%s proxy=%s failover after HTTP %s ban=%s",
                        source,
                        session.log_hint(),
                        resp.status_code,
                        ban_slot,
                    )
                    continue
                return resp
            _record_success(proxy_url, source)
            return resp
        raise requests.RequestException(
            f"exchange_get:{source}: proxy cascade exhausted ({max_attempts} attempts)"
        )
    finally:
        if own_session:
            exchange_fetch_end(source)


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
