"""Пул прокси для Telegram Bot API (getUpdates, sendMessage) — отдельно от exchange_proxy."""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from config import DIRECT_REQUESTS_PROXIES, normalize_proxy_url, radar_timestamp

logger = logging.getLogger(__name__)

_POOL_SOURCE = "tg_bot"
_PROXY_ALERT_PREFIX = "FLPARSING · TG Bot API прокси"
_PROBE_TARGET = "https://api.telegram.org/"
_TELETHON_POOL_ENV = (
    "TELETHON_PROXY_ACC1",
    "TELETHON_PROXY_ACC2",
    "TELETHON_PROXY_ACC3",
)
_FAILOVER_EXCEPTIONS = (
    requests.ConnectionError,
    ConnectionResetError,
    requests.exceptions.ProxyError,
    requests.ReadTimeout,
    requests.ConnectTimeout,
)

_BAN_TTL_SEC = float(os.getenv("TG_PROXY_BAN_TTL_SEC", "3600"))
_STRIKES_TO_BAN = max(1, int(os.getenv("TG_PROXY_STRIKES", "3")))
_ALERT_COOLDOWN_SEC = float(os.getenv("TG_PROXY_ALERT_COOLDOWN_SEC", "600"))
_CONNECT_TIMEOUT_SEC = float(os.getenv("TG_PROXY_CONNECT_TIMEOUT_SEC", "8"))
_READ_TIMEOUT_SEC = float(os.getenv("TG_PROXY_READ_TIMEOUT_SEC", "20"))

_pool_urls: list[str] = []
_active_slot: int = 0
_banned_until: dict[str, float] = {}
_ban_meta: dict[str, dict[str, Any]] = {}
_strike_count: dict[str, int] = {}
_last_owner_alert_at: float = 0.0
_persistence_loaded: bool = False


def _pool_json_path() -> Path:
    raw = os.getenv("TG_PROXY_POOL_JSON", "data/tg_proxy_pool.json").strip()
    p = Path(raw)
    if not p.is_absolute():
        from config import _PROJECT_ROOT

        p = _PROJECT_ROOT / p
    return p


def _hint_from_url(url: str | None) -> str:
    if not url:
        return "direct"
    try:
        p = urlparse(normalize_proxy_url(url))
        return f"{p.hostname}:{p.port or ''}".rstrip(":")
    except Exception:
        return "proxy"


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


def build_pool_urls() -> list[str]:
    """TG_PROXY_URLS (comma) или TG_PROXY_URL + TELETHON acc1/2/3 (dedupe)."""
    explicit = _parse_proxy_list("TG_PROXY_URLS", "TG_PROXY_URL")
    extras: list[str] = []
    for key in _TELETHON_POOL_ENV:
        raw = os.getenv(key, "").strip()
        if not raw:
            continue
        try:
            extras.append(normalize_proxy_url(raw))
        except ValueError:
            continue
    if explicit and len(explicit) > 1:
        return _dedupe_urls(explicit)
    hints = {_hint_from_url(u) for u in explicit}
    merged = explicit + [u for u in extras if _hint_from_url(u) not in hints]
    return _dedupe_urls(merged)


def tg_proxy_direct_enabled() -> bool:
    raw = os.getenv("TG_PROXY_DIRECT", "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def _proxies_dict(url: str | None) -> dict[str, str | None]:
    if not url:
        return DIRECT_REQUESTS_PROXIES
    return {"http": url, "https": url}


def _prune_expired_bans() -> None:
    now = time.time()
    expired = [k for k, until in _banned_until.items() if until <= now]
    for k in expired:
        _banned_until.pop(k, None)
        _ban_meta.pop(k, None)
        _strike_count.pop(k, None)


def _load_persistence() -> None:
    global _persistence_loaded, _active_slot
    if _persistence_loaded:
        return
    _persistence_loaded = True
    path = _pool_json_path()
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return
        _active_slot = int(data.get("active_slot", 0))
        banned = data.get("banned")
        if isinstance(banned, dict):
            now = time.time()
            for hint, meta in banned.items():
                if not isinstance(meta, dict):
                    continue
                until = float(meta.get("until", 0))
                if until > now:
                    _banned_until[str(hint)] = until
                    _ban_meta[str(hint)] = meta
        strikes = data.get("strikes")
        if isinstance(strikes, dict):
            for hint, n in strikes.items():
                try:
                    _strike_count[str(hint)] = int(n)
                except (TypeError, ValueError):
                    pass
    except Exception as exc:
        logger.warning("tg_proxy_pool load failed: %s", exc)


def _persist() -> None:
    _prune_expired_bans()
    path = _pool_json_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "active_slot": _active_slot,
            "banned": {
                hint: {**meta, "until": _banned_until[hint]}
                for hint, meta in _ban_meta.items()
                if hint in _banned_until
            },
            "strikes": _strike_count,
            "updated_at": radar_timestamp(),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.warning("tg_proxy_pool persist failed: %s", exc)


def _ensure_loaded() -> None:
    global _pool_urls
    _load_persistence()
    if not _pool_urls:
        _pool_urls = build_pool_urls()


def _is_banned(url: str) -> bool:
    _ensure_loaded()
    key = _hint_from_url(url)
    until = _banned_until.get(key, 0.0)
    if until and time.time() >= until:
        _banned_until.pop(key, None)
        _ban_meta.pop(key, None)
        _strike_count.pop(key, None)
        return False
    return time.time() < until


def _alive_urls() -> list[str]:
    _ensure_loaded()
    return [u for u in _pool_urls if not _is_banned(u)]


def _slot_label(idx: int) -> str:
    return f"слот {idx + 1}"


def _reason_human(reason: str) -> str:
    mapping = {
        "connect_timeout": "таймаут подключения",
        "read_timeout": "таймаут чтения",
        "proxy_error": "ошибка прокси",
        "connection_error": "сбой соединения",
        "probe_fail": "HTTPS probe fail",
        "strikes": f"{_STRIKES_TO_BAN} ошибок подряд",
    }
    return mapping.get(reason, reason)


def _send_owner_alert(text: str, *, force: bool = False) -> None:
    global _last_owner_alert_at
    now = time.time()
    if not force and now - _last_owner_alert_at < _ALERT_COOLDOWN_SEC:
        return
    _last_owner_alert_at = now
    try:
        from health_check import send_flparsing_admin_text

        ok, err = send_flparsing_admin_text(text)
        if not ok:
            logger.warning("tg_proxy_pool alert failed: %s", err)
    except Exception as exc:
        logger.warning("tg_proxy_pool alert error: %s", exc)


def _notify_proxy_switch(*, old_idx: int, new_idx: int, reason: str) -> None:
    _ensure_loaded()
    if not _pool_urls:
        return
    old_hint = _hint_from_url(_pool_urls[old_idx % len(_pool_urls)])
    new_hint = _hint_from_url(_pool_urls[new_idx % len(_pool_urls)])
    alive = len(_alive_urls())
    total = len(_pool_urls)
    lines = [
        _PROXY_ALERT_PREFIX,
        "",
        f"Забанен: {_slot_label(old_idx)} ({old_hint})",
        f"Причина: {_reason_human(reason)}",
        "",
        f"Подключились: {_slot_label(new_idx)} ({new_hint})",
        "",
        f"Свободно: {alive} из {total}",
    ]
    if alive <= 1:
        lines.append("")
        lines.append("⚠️ Остался последний TG Bot API прокси.")
    _send_owner_alert("\n".join(lines), force=alive <= 1)


def _ban_url(url: str, *, reason: str, slot_idx: int) -> None:
    key = _hint_from_url(url)
    if not key or key == "direct":
        return
    until = time.time() + _BAN_TTL_SEC
    _banned_until[key] = until
    _ban_meta[key] = {
        "reason": reason,
        "banned_at": radar_timestamp(),
        "slot": slot_idx + 1,
    }
    _strike_count.pop(key, None)
    _persist()


def _record_strike(url: str, *, reason: str, slot_idx: int) -> bool:
    """Возвращает True если слот забанен после strike."""
    key = _hint_from_url(url)
    if not key or key == "direct":
        return False
    n = _strike_count.get(key, 0) + 1
    _strike_count[key] = n
    _persist()
    if n >= _STRIKES_TO_BAN:
        _ban_url(url, reason=reason, slot_idx=slot_idx)
        return True
    return False


def _resolve_active_slot() -> int:
    global _active_slot
    _ensure_loaded()
    if not _pool_urls:
        return 0
    idx = _active_slot % len(_pool_urls)
    if not _is_banned(_pool_urls[idx]):
        return idx
    for off in range(len(_pool_urls)):
        j = (idx + off) % len(_pool_urls)
        if not _is_banned(_pool_urls[j]):
            if j != idx:
                old = _active_slot
                _active_slot = j
                _persist()
                _notify_proxy_switch(old_idx=old, new_idx=j, reason="ban_expired_or_switch")
            return j
    return idx


def get_active_proxy_url() -> str | None:
    """URL активного слота (для probe / status)."""
    _ensure_loaded()
    if not _pool_urls:
        raw = os.getenv("TG_PROXY_URL", "").strip()
        if not raw:
            return None
        try:
            return normalize_proxy_url(raw)
        except ValueError:
            return raw
    idx = _resolve_active_slot()
    return _pool_urls[idx]


def get_active_proxies_dict() -> dict[str, str | None]:
    """Текущий слот для telegram_requests_proxies."""
    _ensure_loaded()
    if not _pool_urls:
        primary = os.getenv("TG_PROXY_URL", "").strip()
        if primary:
            try:
                url = normalize_proxy_url(primary)
                return _proxies_dict(url)  # type: ignore[return-value]
            except ValueError:
                pass
        if tg_proxy_direct_enabled():
            return DIRECT_REQUESTS_PROXIES
        raise ValueError("TG_PROXY_URL не задан и пул пуст")
    idx = _resolve_active_slot()
    url = _pool_urls[idx]
    if _is_banned(url):
        if tg_proxy_direct_enabled():
            return DIRECT_REQUESTS_PROXIES
        raise requests.RequestException("tg_proxy_pool: pool exhausted")
    return _proxies_dict(url)  # type: ignore[return-value]


def _classify_exc(exc: BaseException) -> str:
    if isinstance(exc, requests.ConnectTimeout):
        return "connect_timeout"
    if isinstance(exc, requests.ReadTimeout):
        return "read_timeout"
    if isinstance(exc, requests.exceptions.ProxyError):
        return "proxy_error"
    return "connection_error"


def advance_failover(*, reason: str, failed_url: str | None = None) -> bool:
    """Переключить на следующий живой слот. Возвращает False если пул исчерпан."""
    global _active_slot
    _ensure_loaded()
    if not _pool_urls:
        return tg_proxy_direct_enabled()
    old_idx = _active_slot % len(_pool_urls)

    for off in range(1, len(_pool_urls) + 1):
        idx = (old_idx + off) % len(_pool_urls)
        if _is_banned(_pool_urls[idx]):
            continue
        if idx != old_idx:
            _active_slot = idx
            _persist()
            _notify_proxy_switch(old_idx=old_idx, new_idx=idx, reason=reason)
        return True

    if tg_proxy_direct_enabled():
        _send_owner_alert(
            f"{_PROXY_ALERT_PREFIX}\n\n"
            "Пул исчерпан — fallback direct с VPS (TG_PROXY_DIRECT=1).",
            force=True,
        )
        return True

    _send_owner_alert(
        f"{_PROXY_ALERT_PREFIX}\n\n"
        "🛑 Пул TG Bot API исчерпан — бот не ходит в Telegram до TTL бана.",
        force=True,
    )
    return False


def probe_proxy_https(url: str, *, timeout: float | None = None) -> tuple[bool, str]:
    """HTTPS до api.telegram.org через прокси (не только TCP)."""
    read_t = timeout if timeout is not None else _READ_TIMEOUT_SEC
    try:
        norm = normalize_proxy_url(url.strip())
        proxies = {"http": norm, "https": norm}
        r = requests.get(
            _PROBE_TARGET,
            proxies=proxies,
            timeout=(_CONNECT_TIMEOUT_SEC, read_t),
            headers={"User-Agent": "RawLeadTgProxyProbe/1.0"},
            allow_redirects=True,
        )
        return True, f"HTTP {r.status_code}"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:100]}"


def tg_http_request(
    method: str,
    url: str,
    *,
    session: requests.Session | None = None,
    max_attempts: int | None = None,
    **kwargs: Any,
) -> requests.Response:
    """
    HTTP(S) к Bot API с failover по пулу TG-прокси.
    kwargs: data, params, timeout, json, …
    """
    _ensure_loaded()
    sess = session or requests.Session()
    if session is None:
        sess.trust_env = False

    attempts = max_attempts if max_attempts is not None else max(1, len(_pool_urls) or 1)
    attempts = min(attempts, max(3, len(_pool_urls) + (1 if tg_proxy_direct_enabled() else 0)))

    last_exc: BaseException | None = None
    for _ in range(attempts):
        proxies = get_active_proxies_dict()
        current_url = None
        if _pool_urls:
            idx = _resolve_active_slot()
            current_url = _pool_urls[idx]
        try:
            resp = sess.request(method, url, proxies=proxies, **kwargs)
            if current_url and _hint_from_url(current_url) in _strike_count:
                _strike_count.pop(_hint_from_url(current_url), None)
                _persist()
            return resp
        except _FAILOVER_EXCEPTIONS as exc:
            last_exc = exc
            reason = _classify_exc(exc)
            logger.warning(
                "tg_proxy_pool %s fail slot=%s reason=%s: %s",
                method,
                _hint_from_url(current_url),
                reason,
                exc,
            )
            if current_url:
                _record_strike(current_url, reason=reason, slot_idx=_resolve_active_slot())
                if _strike_count.get(_hint_from_url(current_url), 0) >= _STRIKES_TO_BAN:
                    _ban_url(current_url, reason=reason, slot_idx=_resolve_active_slot())
            if not advance_failover(reason=reason, failed_url=current_url):
                break
            time.sleep(0.3)

    if last_exc is not None:
        raise last_exc
    raise requests.RequestException("tg_proxy_pool: request failed")


def status_summary() -> dict[str, Any]:
    _ensure_loaded()
    alive_list = _alive_urls()
    total = len(_pool_urls)
    alive = len(alive_list)
    slot = _resolve_active_slot() if _pool_urls else 0
    active_hint = _hint_from_url(_pool_urls[slot]) if _pool_urls else "?"
    banned = [
        {
            "slot": i + 1,
            "host": _hint_from_url(u),
            "reason": (_ban_meta.get(_hint_from_url(u)) or {}).get("reason"),
        }
        for i, u in enumerate(_pool_urls)
        if _is_banned(u)
    ]
    return {
        "pool_size": total,
        "active_slot": slot + 1 if _pool_urls else 0,
        "active_host": active_hint,
        "alive": alive,
        "total": total,
        "banned": banned,
        "direct_fallback": tg_proxy_direct_enabled(),
    }


def _slot_ui_entry(url: str, idx: int, active_idx: int) -> dict[str, Any]:
    from proxy_ops import mask, slot_status_label

    hint = _hint_from_url(url)
    banned = _is_banned(url)
    strikes_n = _strike_count.get(hint, 0)
    if banned:
        status = "bad"
    elif strikes_n > 0:
        status = "warn"
    else:
        status = "ok"
    until_ts = _banned_until.get(hint) if banned else None
    banned_until = None
    if until_ts and until_ts > time.time():
        banned_until = datetime.fromtimestamp(until_ts, tz=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    meta = _ban_meta.get(hint) or {}
    reason_raw = meta.get("reason") if banned else None
    return {
        "slot": idx + 1,
        "mask": mask(url),
        "status": status,
        "status_label": slot_status_label(
            status=status,
            banned_until=banned_until,
            reason_raw=str(reason_raw) if reason_raw else None,
        ),
        "active": idx == active_idx,
        "banned_until": banned_until,
        "reason": _reason_human(str(reason_raw)) if reason_raw else None,
        "strikes": f"{strikes_n}/{_STRIKES_TO_BAN}",
        "_url": url,
    }


def list_ui_group() -> dict[str, Any]:
    """TG Bot API pool for /ops/ proxies."""
    _ensure_loaded()
    active_idx = _resolve_active_slot() if _pool_urls else 0
    slots = [
        _slot_ui_entry(url, i, active_idx)
        for i, url in enumerate(_pool_urls)
    ]
    if not slots:
        raw = os.getenv("TG_PROXY_URL", "").strip()
        if raw:
            try:
                url = normalize_proxy_url(raw)
                slots = [_slot_ui_entry(url, 0, 0)]
            except ValueError:
                pass
    return {
        "id": "tg-bot",
        "title": "TG Bot API",
        "active_slot": active_idx + 1 if slots else 0,
        "slots": slots,
    }


def list_telethon_ui_group() -> dict[str, Any]:
    """Telethon acc1–3 — env-only, probe/switch not persisted here."""
    from proxy_ops import mask, slot_status_label

    labels = (
        ("telethon-acc1", "Telethon acc1", "TELETHON_PROXY_ACC1"),
        ("telethon-acc2", "Telethon acc2", "TELETHON_PROXY_ACC2"),
        ("telethon-acc3", "Telethon acc3", "TELETHON_PROXY_ACC3"),
    )
    slots: list[dict[str, Any]] = []
    active_slot = 0
    for i, (_gid, _title, env_key) in enumerate(labels):
        raw = os.getenv(env_key, "").strip()
        if not raw:
            slots.append(
                {
                    "slot": i + 1,
                    "mask": "—",
                    "status": "warn",
                    "status_label": "Не настроен на сервере",
                    "active": False,
                    "banned_until": None,
                    "reason": "не задан в env",
                    "strikes": "—",
                    "_url": "",
                }
            )
            continue
        try:
            url = normalize_proxy_url(raw)
        except ValueError:
            slots.append(
                {
                    "slot": i + 1,
                    "mask": "invalid",
                    "status": "bad",
                    "status_label": slot_status_label(status="bad", banned_until=None),
                    "active": False,
                    "banned_until": None,
                    "reason": "некорректный URL",
                    "strikes": "—",
                    "_url": "",
                }
            )
            continue
        if not active_slot:
            active_slot = i + 1
        slots.append(
            {
                "slot": i + 1,
                "mask": mask(url),
                "status": "ok",
                "status_label": slot_status_label(status="ok", banned_until=None),
                "active": True,
                "banned_until": None,
                "reason": None,
                "strikes": "—",
                "_url": url,
            }
        )
    return {
        "id": "telethon",
        "title": "Telethon acc1–3",
        "active_slot": active_slot,
        "slots": slots,
    }


def set_active_slot(slot_1based: int) -> tuple[bool, str]:
    """Manual switch (1-based), без restart radar."""
    global _active_slot
    _ensure_loaded()
    if not _pool_urls:
        raw = os.getenv("TG_PROXY_URL", "").strip()
        if not raw or slot_1based != 1:
            return False, "Пул TG Bot API пуст"
        return True, "Активен единственный TG_PROXY_URL"
    idx = int(slot_1based) - 1
    if idx < 0 or idx >= len(_pool_urls):
        return False, f"Слот {slot_1based} не существует"
    url = _pool_urls[idx]
    if _is_banned(url):
        return False, f"Слот {slot_1based} забанен"
    old = _active_slot
    _active_slot = idx
    _persist()
    if old != idx:
        logger.info("tg_proxy_pool manual switch slot %s→%s", old + 1, slot_1based)
    return True, f"Активен слот {slot_1based} ({_hint_from_url(url)})"


def clear_all_bans() -> int:
    """Clear TG Bot API bans/strikes (ops /ops/ clear-bans)."""
    global _banned_until, _ban_meta, _strike_count
    _ensure_loaded()
    n = len(_banned_until) + len(_strike_count)
    _banned_until.clear()
    _ban_meta.clear()
    _strike_count.clear()
    _persist()
    return n


def reset_pool_for_tests() -> None:
    """Только для unit-тестов."""
    global _pool_urls, _active_slot, _banned_until, _ban_meta, _strike_count
    global _persistence_loaded, _last_owner_alert_at
    _pool_urls = []
    _active_slot = 0
    _banned_until = {}
    _ban_meta = {}
    _strike_count = {}
    _persistence_loaded = False
    _last_owner_alert_at = 0.0
