"""O104: реестр здоровья бирж — SQLite settings, /status, /ops/, алерты FLPARSING."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from config import radar_timestamp
from radar_cycle_log import SOURCE_LABELS

if TYPE_CHECKING:
    from storage import ProjectStorage

GREEN_MAX_MIN = 15
YELLOW_MAX_MIN = 45
ALERT_COOLDOWN_SEC = 1800
_ERROR_SHORT_MAX = 80

KIND_LABELS: dict[str, str] = {
    "ok": "Работает",
    "antibot": "Антибот / блок IP",
    "403": "403 запрещено",
    "browser": "Браузер не открыл страницу",
    "parse": "Страница открылась, разбор не смог",
    "proxy": "Прокси кончились / в бане",
    "timeout": "Таймаут",
    "unknown": "Неизвестная ошибка",
}

STATUS_LABELS_RU: dict[str, str] = {
    "green": "🟢 Работает",
    "yellow": "🟡 Давно не видели",
    "red": "🔴 Сломалось",
}

_O104_SOURCES: tuple[str, ...] = (
    "fl",
    "kwork",
    "youdo",
    "freelance_ru",
    "freelancejob",
    "pchyol",
    "tg",
)


def health_source_ids() -> tuple[str, ...]:
    """Источники O104 — пересечение с PUBLIC_FEED_SOURCES + tg."""
    from public_feed import public_feed_sources

    enabled = public_feed_sources()
    out: list[str] = []
    for sid in _O104_SOURCES:
        if sid == "tg":
            out.append(sid)
        elif sid in enabled:
            out.append(sid)
    return tuple(out)


def _settings_key(source: str) -> str:
    return f"exchange_health:{source.strip().lower()}"


def _alert_key(source: str) -> str:
    return f"exchange_health_alert_at:{source.strip().lower()}"


def classify_error(msg: str) -> str:
    s = (msg or "").strip().lower()
    if not s:
        return "unknown"
    if any(x in s for x in ("antibot", "captcha", "cloudflare", "блок ip", "block ip", "ddos-guard")):
        return "antibot"
    if "403" in s or "forbidden" in s or "запрещ" in s:
        return "403"
    if any(x in s for x in ("browser", "playwright", "chromium", "browser_fail")):
        return "browser"
    if any(x in s for x in ("proxy", "прокси", "ban", "pool exhausted", "no alive")):
        return "proxy"
    if any(x in s for x in ("timeout", "timed out", "таймаут", "read timed out")):
        return "timeout"
    if any(x in s for x in ("parse", "разбор", "empty", "no cards", "no tasks", "selector")):
        return "parse"
    return "unknown"


def kind_label(kind: str) -> str:
    return KIND_LABELS.get(kind, KIND_LABELS["unknown"])


def source_display_name(source_id: str) -> str:
    if source_id == "fl":
        return "FL.ru"
    if source_id == "kwork":
        return "Kwork"
    if source_id == "tg":
        return "TG"
    return SOURCE_LABELS.get(source_id, source_id)


def _parse_ts_epoch(ts: str) -> float | None:
    s = (ts or "").strip()
    if not s:
        return None
    is_utc = s.endswith(" UTC") or s.endswith("Z")
    s_clean = s.replace(" UTC", "").replace("Z", "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(s_clean, fmt)
            if is_utc:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                from config import radar_tz

                dt = dt.replace(tzinfo=radar_tz())
            return dt.timestamp()
        except ValueError:
            continue
    return None


def _empty_record() -> dict[str, Any]:
    return {
        "last_fetch_at": "",
        "last_ok_at": "",
        "last_error_at": "",
        "last_error_kind": "ok",
        "last_error_short": "",
        "last_downloaded": 0,
        "last_new_ids": 0,
    }


def load_health(storage: ProjectStorage, source: str) -> dict[str, Any]:
    raw = storage.get_setting(_settings_key(source), "").strip()
    if not raw:
        return _empty_record()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return _empty_record()
    if not isinstance(data, dict):
        return _empty_record()
    out = _empty_record()
    out.update({k: data.get(k, out[k]) for k in out})
    out["last_downloaded"] = int(data.get("last_downloaded", 0) or 0)
    out["last_new_ids"] = int(data.get("last_new_ids", 0) or 0)
    out["last_error_kind"] = str(data.get("last_error_kind", "ok") or "ok")
    out["last_error_short"] = str(data.get("last_error_short", "") or "")[: _ERROR_SHORT_MAX]
    return out


def load_all_health(storage: ProjectStorage) -> dict[str, dict[str, Any]]:
    return {sid: load_health(storage, sid) for sid in health_source_ids()}


def save_health(storage: ProjectStorage, source: str, record: dict[str, Any]) -> None:
    storage.set_setting(_settings_key(source), json.dumps(record, ensure_ascii=False))


def silence_minutes(health: dict[str, Any], *, now: float | None = None) -> int | None:
    ref = now if now is not None else time.time()
    ok_ts = str(health.get("last_ok_at") or "").strip()
    if not ok_ts:
        return None
    epoch = _parse_ts_epoch(ok_ts)
    if epoch is None:
        return None
    return max(0, int((ref - epoch) // 60))


def status_level(
    health: dict[str, Any],
    *,
    fetch_failed: bool = False,
    now: float | None = None,
) -> str:
    """green | yellow | red."""
    if fetch_failed or str(health.get("last_error_kind", "ok")) not in ("", "ok"):
        err_at = str(health.get("last_error_at") or "").strip()
        fetch_at = str(health.get("last_fetch_at") or "").strip()
        if fetch_failed or (err_at and err_at == fetch_at):
            return "red"
    mins = silence_minutes(health, now=now)
    if mins is None:
        return "red"
    if mins < GREEN_MAX_MIN:
        return "green"
    if mins <= YELLOW_MAX_MIN:
        return "yellow"
    return "red"


def status_label_ru(level: str) -> str:
    return STATUS_LABELS_RU.get(level, STATUS_LABELS_RU["red"])


def record_fetch(
    storage: ProjectStorage,
    source: str,
    *,
    ok: bool,
    error_msg: str = "",
    downloaded: int = 0,
    new_ids: int = 0,
    ts: str | None = None,
) -> dict[str, Any]:
    """После fetch в run_cycle — обновить реестр."""
    stamp = ts or radar_timestamp()
    rec = load_health(storage, source)
    rec["last_fetch_at"] = stamp
    rec["last_downloaded"] = int(downloaded)
    rec["last_new_ids"] = int(new_ids)
    if ok:
        rec["last_ok_at"] = stamp
        rec["last_error_kind"] = "ok"
        rec["last_error_short"] = ""
    else:
        kind = classify_error(error_msg)
        rec["last_error_at"] = stamp
        rec["last_error_kind"] = kind
        short = (error_msg or kind_label(kind)).strip()[:_ERROR_SHORT_MAX]
        rec["last_error_short"] = short
    save_health(storage, source, rec)
    return rec


def record_ok_ping(storage: ProjectStorage, source: str, *, ts: str | None = None) -> dict[str, Any]:
    """Neon insert / TG pulse — без fetch."""
    stamp = ts or radar_timestamp()
    rec = load_health(storage, source)
    rec["last_ok_at"] = stamp
    rec["last_error_kind"] = "ok"
    rec["last_error_short"] = ""
    save_health(storage, source, rec)
    return rec


def format_health_log_line(
    source: str,
    health: dict[str, Any],
    *,
    fetch_ok: bool,
    ingest_lag_p50_min: int | None = None,
) -> str:
    if fetch_ok and str(health.get("last_error_kind", "ok")) in ("", "ok"):
        parts = [
            f"health:{source}",
            "status=ok",
            f"downloaded={int(health.get('last_downloaded', 0))}",
            f"new={int(health.get('last_new_ids', 0))}",
        ]
        if ingest_lag_p50_min is not None:
            parts.append(f"lag_p50={ingest_lag_p50_min}m")
        return " ".join(parts)
    kind = str(health.get("last_error_kind") or "unknown")
    return f"health:{source} status=fail kind={kind}"


def append_health_log(log_path: os.PathLike[str] | str | None, line: str) -> None:
    if log_path is None:
        return
    from pathlib import Path

    try:
        p = Path(log_path)
        if str(p.parent) not in ("", "."):
            p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(f"{radar_timestamp()} {line.rstrip()}\n")
    except OSError:
        pass


def _last_ok_short(health: dict[str, Any]) -> str:
    ok_ts = str(health.get("last_ok_at") or "").strip()
    if not ok_ts:
        return "—"
    s = ok_ts.replace(" UTC", "")
    if len(s) >= 16:
        return s[11:16] + " UTC"
    return ok_ts[:19]


def format_alert_text(source: str, health: dict[str, Any], *, now: float | None = None) -> str:
    label = source_display_name(source)
    mins = silence_minutes(health, now=now)
    silence = f"тишина {mins} мин" if mins is not None else "тишина ?"
    kind = str(health.get("last_error_kind") or "unknown")
    reason = kind_label(kind) if kind != "ok" else "нет данных"
    err_short = str(health.get("last_error_short") or "").strip()
    if err_short and kind != "ok":
        reason = err_short[:_ERROR_SHORT_MAX]
    last_ok = _last_ok_short(health)
    return f"🔴 {label} · {silence} · {reason} · последний OK {last_ok}"


def _alert_cooldown_ok(storage: ProjectStorage, source: str, cooldown_sec: int) -> bool:
    raw = storage.get_setting(_alert_key(source), "0").strip()
    try:
        last = float(raw)
    except ValueError:
        last = 0.0
    return (time.time() - last) >= cooldown_sec


def _mark_alert_sent(storage: ProjectStorage, source: str) -> None:
    storage.set_setting(_alert_key(source), str(int(time.time())))


def maybe_send_red_alert(
    storage: ProjectStorage,
    source: str,
    health: dict[str, Any],
    *,
    fetch_failed: bool = False,
    cooldown_sec: int = ALERT_COOLDOWN_SEC,
) -> bool:
    """Push в @FLPARSINGBOT при 🔴; cooldown на источник."""
    level = status_level(health, fetch_failed=fetch_failed)
    if level != "red":
        return False
    if not _alert_cooldown_ok(storage, source, cooldown_sec):
        return False
    try:
        from health_check import send_flparsing_admin_text

        text = format_alert_text(source, health)
        ok, _err = send_flparsing_admin_text(text)
        if ok:
            _mark_alert_sent(storage, source)
        return ok
    except Exception:
        return False


def format_exchange_status_line(
    source_id: str,
    health: dict[str, Any],
    *,
    fetch_failed: bool = False,
    downloaded: int | None = None,
    new_ids: int | None = None,
    now: float | None = None,
) -> str:
    """Строка для блока «Биржи» в /status."""
    label = source_display_name(source_id).ljust(7)
    level = status_level(health, fetch_failed=fetch_failed, now=now)
    icon = {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(level, "🔴")
    mins = silence_minutes(health, now=now)
    dl = downloaded if downloaded is not None else int(health.get("last_downloaded", 0))
    nw = new_ids if new_ids is not None else int(health.get("last_new_ids", 0))
    kind = str(health.get("last_error_kind") or "ok")
    err = str(health.get("last_error_short") or "").strip()

    if level == "red" and (fetch_failed or kind not in ("", "ok")):
        reason = err[:50] if err else kind_label(kind)
        silence = f" · тишина {mins} мин" if mins is not None else ""
        return f"{label} {icon}{silence} · {reason[:50]}"

    parts: list[str] = []
    if dl:
        parts.append(f"{dl} скачано")
    if nw:
        parts.append(f"{nw} новых" if nw != 1 else "1 новый")
    if mins is not None and level != "green":
        parts.append(f"тишина {mins} мин")
    elif not parts:
        parts.append(kind_label("ok"))
    return f"{label} {icon} {' · '.join(parts)}"


def build_ops_exchange_row(
    source_id: str,
    health: dict[str, Any],
    ingest: dict[str, int | float | str] | None,
    *,
    fetch_failed: bool = False,
    now: float | None = None,
) -> dict[str, Any]:
    """Строка для /ops/ «Биржи и скорость»."""
    level = status_level(health, fetch_failed=fetch_failed, now=now)
    ing = ingest or {}
    gap_sec = int(ing.get("last_insert_gap_sec", 0) or 0)
    gap_min = gap_sec // 60
    last_insert = str(ing.get("last_insert_at") or "").strip()
    ingest_p50 = float(ing.get("ingest_p50_sec", 0.0) or 0.0)
    feed_p50 = float(ing.get("feed_p50_sec", 0.0) or 0.0)
    within = int(ing.get("feed_within_5m", 0) or 0)
    measurable = int(ing.get("feed_measurable_24h", 0) or 0)
    within_pct = int(within * 100 / measurable) if measurable else None
    err = str(health.get("last_error_short") or "").strip()
    kind = str(health.get("last_error_kind") or "ok")
    what = err if err else ("—" if kind in ("", "ok") else kind_label(kind))
    return {
        "source_id": source_id,
        "name": source_display_name(source_id),
        "level": level,
        "status_label": status_label_ru(level),
        "last_insert_at": last_insert,
        "last_insert_ago_min": gap_min,
        "ingest_p50_min": int(ingest_p50 // 60) if ingest_p50 else None,
        "feed_p50_min": int(feed_p50 // 60) if feed_p50 else None,
        "feed_within_5m": within if measurable else None,
        "feed_within_5m_pct": within_pct,
        "what_happened": what[:_ERROR_SHORT_MAX],
    }
