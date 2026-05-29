"""Сводка для кнопки «Статус» в Telegram-боте (общая SQLite для main и tg_main)."""

from __future__ import annotations

import csv
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from config import (
    Config,
    TgMonitorAccountConfig,
    legacy_neon_consumer_enabled,
    load_tg_join_config,
    load_tg_monitor_config,
    radar_exchanges_enabled,
    radar_tg_enabled,
    radar_timestamp,
)
from health_check import (
    _TG_MONITOR_PULSE_KEY,
    _TG_MONITOR_PULSE_MAX_AGE_SEC,
    is_tg_monitor_active,
    tg_monitor_warmup_remaining_sec,
)
from radar_cycle_log import (
    SOURCE_LABELS,
    CycleSummary,
    SourceCycleStats,
    load_cycle_summary,
    load_site_rollup_line,
    parse_site_rollup_metrics,
)
from storage import ProjectStorage
from tg_bot_start import is_bot_started

_STATUS_FL_CYCLE_AT = "status_fl_cycle_at"
_STATUS_FL = (
    "status_fl_cards_fl",
    "status_fl_cards_kwork",
    "status_fl_new",
    "status_fl_notified",
    "status_fl_errors",
)
_STATUS_NEON_CYCLE_AT = "status_neon_cycle_at"
_STATUS_NEON_LAST_SAMPLE = "status_neon_last_sample"
_STATUS_NEON_LAST_NEW = "status_neon_last_new"
_STATUS_NEON_LAST_TO_BOT = "status_neon_last_to_bot"
_STATUS_NEON_SESSION_TO_BOT = "status_neon_session_to_bot"


def _tg_key(account: str, suffix: str) -> str:
    return f"status_tg_{account.strip().lower()}_{suffix}"


def reset_tg_session_stats(storage: ProjectStorage, accounts: tuple[str, ...]) -> None:
    """Новый запуск окна TG — обнулить счётчики сессии."""
    for acc in accounts:
        for suffix in (
            "msgs",
            "new",
            "notified",
            "last_err",
            "chats_listen",
            "chats_file",
            "started_at",
            "ready",
            "phase",
            "last_action",
        ):
            storage.set_setting(_tg_key(acc, suffix), "0" if suffix != "last_err" else "")


def record_tg_monitor_start(
    storage: ProjectStorage,
    account: str,
    *,
    chats_listen: int,
    chats_in_file: int,
) -> None:
    acc = account.strip().lower()
    storage.set_setting(_tg_key(acc, "ready"), "0")
    storage.set_setting(_tg_key(acc, "chats_listen"), str(chats_listen))
    storage.set_setting(_tg_key(acc, "chats_file"), str(chats_in_file))
    storage.set_setting(_tg_key(acc, "started_at"), radar_timestamp())
    record_tg_phase(
        storage,
        acc,
        "старт",
        f"слушаем {chats_listen}/{chats_in_file} чатов",
    )


def record_tg_acc_ready(storage: ProjectStorage, account: str) -> None:
    """Acc готов слушать: handler зарегистрирован, get_me ok."""
    acc = account.strip().lower()
    storage.set_setting(_tg_key(acc, "ready"), "1")
    record_tg_phase(storage, acc, "слушает")


def record_tg_message(
    storage: ProjectStorage,
    account: str,
    *,
    was_new: bool,
    notified: bool,
    error: str | None = None,
) -> None:
    acc = account.strip().lower()
    storage.incr_setting(_tg_key(acc, "msgs"), 1)
    if was_new:
        storage.incr_setting(_tg_key(acc, "new"), 1)
    if notified:
        storage.incr_setting(_tg_key(acc, "notified"), 1)
    if error:
        storage.set_setting(_tg_key(acc, "last_err"), error[:400])
    if notified:
        record_tg_phase(storage, acc, "пересыл", f"новый={int(was_new)}")
    elif was_new:
        record_tg_phase(storage, acc, "новый пост")


def record_tg_skip(
    storage: ProjectStorage,
    account: str,
    detail: str,
) -> None:
    acc = account.strip().lower()
    storage.set_setting(_tg_key(acc, "last_err"), detail[:400])
    record_tg_phase(storage, acc, "пропуск", detail)


def record_tg_phase(
    storage: ProjectStorage,
    account: str,
    phase: str,
    detail: str = "",
) -> None:
    acc = account.strip().lower()
    storage.set_setting(_tg_key(acc, "phase"), phase[:80])
    ts = radar_timestamp()
    line = f"{ts} {phase}"
    if detail:
        line += f" — {detail[:200]}"
    storage.set_setting(_tg_key(acc, "last_action"), line[:400])


def record_fl_kwork_cycle(
    storage: ProjectStorage,
    *,
    cards_fl: int,
    cards_kwork: int,
    new_ids: int,
    notifications: int,
    errors: list[str],
) -> None:
    storage.set_setting(_STATUS_FL_CYCLE_AT, radar_timestamp())
    storage.set_setting(_STATUS_FL[0], str(cards_fl))
    storage.set_setting(_STATUS_FL[1], str(cards_kwork))
    storage.set_setting(_STATUS_FL[2], str(new_ids))
    storage.set_setting(_STATUS_FL[3], str(notifications))
    storage.set_setting(
        _STATUS_FL[4],
        json.dumps(errors[:5], ensure_ascii=False) if errors else "[]",
    )


def _int_setting(storage: ProjectStorage, key: str) -> int:
    try:
        return int(storage.get_setting(key, "0").strip() or "0")
    except ValueError:
        return 0


def reset_neon_consumer_session(storage: ProjectStorage) -> None:
    storage.set_setting(_STATUS_NEON_SESSION_TO_BOT, "0")


def record_neon_consumer_cycle(
    storage: ProjectStorage,
    *,
    sample_size: int,
    new_ids: int,
    to_bot: int,
) -> None:
    storage.set_setting(_STATUS_NEON_CYCLE_AT, radar_timestamp())
    storage.set_setting(_STATUS_NEON_LAST_SAMPLE, str(sample_size))
    storage.set_setting(_STATUS_NEON_LAST_NEW, str(new_ids))
    storage.set_setting(_STATUS_NEON_LAST_TO_BOT, str(to_bot))
    session = _int_setting(storage, _STATUS_NEON_SESSION_TO_BOT) + to_bot
    storage.set_setting(_STATUS_NEON_SESSION_TO_BOT, str(session))


def _profile_label(profile: str) -> str:
    return profile.strip().upper() if profile else "LEGACY"


def _bot_label(cfg: Config) -> str:
    if cfg.radar_profile == "site":
        return f"@{_SITE_BOT_USERNAME}"
    return f"@{_LEGACY_BOT_USERNAME}"


_SITE_BOT_USERNAME = "rawlead_bot"
_LEGACY_BOT_USERNAME = "FLPARSINGBOT"
_STATUS_MAX_LEN = 3490
_L1_BACKLOG_OK = 50
_L1_BACKLOG_WARN = 100


def _control_port() -> int:
    raw = os.environ.get("RADAR_CONTROL_PORT", "18765").strip()
    try:
        return int(raw)
    except ValueError:
        return 18765


def _log_file_name(cfg: Config) -> str:
    return Path(cfg.radar_log_path).name


def _bot_start_ok(cfg: Config) -> bool | None:
    if cfg.radar_profile == "site" and radar_tg_enabled():
        try:
            tg_cfg = load_tg_monitor_config()
            listening = [ac for ac in tg_cfg.accounts if ac.chat_ids]
            if not listening:
                return None
            return all(is_bot_started(ac.account) for ac in listening)
        except SystemExit:
            return None
    return None


def _query_last_visible_at(cfg: Config) -> str | None:
    if cfg.radar_profile != "site":
        return None
    try:
        from pg_storage import pg_storage_from_config

        pg = pg_storage_from_config(cfg)
        if pg is None or not pg.enabled:
            return None
        return pg.last_visible_created_at([])
    except Exception:
        return None


def _query_l1_backlog(cfg: Config) -> int | None:
    if cfg.radar_profile != "site":
        return None
    try:
        from pg_storage import pg_storage_from_config

        pg = pg_storage_from_config(cfg)
        if pg is None or not pg.enabled:
            return None
        return pg.count_leads_missing_l1([])
    except Exception:
        return None


def _query_l1_backlog_recent(cfg: Config, hours: int = 48) -> int | None:
    """Без L1 за последние N часов — свежий хвост."""
    if cfg.radar_profile != "site":
        return None
    try:
        from pg_storage import pg_storage_from_config

        pg = pg_storage_from_config(cfg)
        if pg is None or not pg.enabled:
            return None
        return pg.count_leads_missing_l1_recent(hours=hours)
    except Exception:
        return None


def build_status_detail(cfg: Config, storage: ProjectStorage) -> dict:
    """JSON-поля для /status и рендера пульта (§ PULT-STATUS-LOGS)."""
    profile = cfg.radar_profile
    paused = storage.is_radar_paused()
    summary = load_cycle_summary(storage)
    rollup = load_site_rollup_line(storage)
    bot_ok = _bot_start_ok(cfg)
    detail: dict = {
        "profile": profile,
        "profile_label": _profile_label(profile),
        "bot_label": _bot_label(cfg),
        "telegram_chat_id": cfg.telegram_chat_id,
        "poll_min": cfg.poll_interval_minutes,
        "conveyor": cfg.radar_conveyor if profile == "site" else False,
        "paused": paused,
        "log_file": _log_file_name(cfg),
        "control_port": _control_port(),
        "exchanges_enabled": radar_exchanges_enabled(),
        "tg_enabled": radar_tg_enabled(),
        "neon_consumer": legacy_neon_consumer_enabled(),
        "bot_start_ok": bot_ok,
        "site_rollup_10m": rollup or None,
        "last_visible_at": _query_last_visible_at(cfg),
        "l1_backlog": _query_l1_backlog(cfg),
    }
    if summary is not None:
        detail["last_cycle"] = summary.to_storage_dict()
    detail["neon_consumer_stats"] = {
        "cycle_at": storage.get_setting(_STATUS_NEON_CYCLE_AT, "").strip() or None,
        "last_sample": _int_setting(storage, _STATUS_NEON_LAST_SAMPLE),
        "last_new": _int_setting(storage, _STATUS_NEON_LAST_NEW),
        "last_to_bot": _int_setting(storage, _STATUS_NEON_LAST_TO_BOT),
        "session_to_bot": _int_setting(storage, _STATUS_NEON_SESSION_TO_BOT),
    }
    tg_ok, tg_detail = _tg_monitor_state(storage)
    detail["tg_monitor"] = {"ok": tg_ok, "detail": tg_detail}
    return detail


def _parse_ts_epoch(ts: str) -> float | None:
    s = ts.strip()
    if not s:
        return None
    is_utc = s.endswith(" UTC") or s.endswith("Z")
    s_clean = s.replace(" UTC", "").replace("Z", "").strip()
    from config import radar_tz

    tz = radar_tz()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(s_clean, fmt)
            if is_utc:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.replace(tzinfo=tz)
            return dt.timestamp()
        except ValueError:
            continue
    return None


def _human_ago(ts: str | None, *, now: float | None = None) -> str | None:
    if not ts:
        return None
    epoch = _parse_ts_epoch(ts)
    if epoch is None:
        return ts[:19] if len(ts) > 19 else ts
    ref = now if now is not None else time.time()
    delta = max(0.0, ref - epoch)
    if delta < 60:
        return f"{int(delta)} сек назад"
    if delta < 3600:
        return f"{int(delta // 60)} мин назад"
    if delta < 86400:
        return f"{int(delta // 3600)} ч назад"
    return f"{int(delta // 86400)} д назад"


def _ru_new(n: int) -> str:
    n_abs = abs(n) % 100
    n1 = n_abs % 10
    if 11 <= n_abs <= 14:
        word = "новых"
    elif n1 == 1:
        word = "новый"
    else:
        word = "новых"
    return f"{n} {word}"


def _neon_status_label(cfg: Config) -> str:
    try:
        from pg_storage import pg_storage_from_config

        pg = pg_storage_from_config(cfg)
        if pg is None or not pg.enabled:
            return "Neon выкл"
        return "Neon OK"
    except Exception:
        return "Neon ?"


def _ingest_headline(
    cfg: Config,
    storage: ProjectStorage,
    unit_state: str | None,
    problems: list[str],
) -> str:
    poll = cfg.poll_interval_minutes
    neon = _neon_status_label(cfg)
    paused = storage.is_radar_paused()
    us = (unit_state or "").strip().lower()
    if us in ("inactive", "failed", "dead"):
        problems.append(f"systemd rawlead-radar: {us}")
        return f"🛑 Остановлен · poll {poll} мин · {neon}"
    if paused:
        if us == "active":
            problems.append("Ingest на паузе (флаг в SQLite)")
        return f"⏸ Пауза · poll {poll} мин · {neon}"
    if us == "active":
        return f"▶ Работает · poll {poll} мин · {neon}"
    if us == "activating":
        return f"⏳ Запуск · poll {poll} мин · {neon}"
    if not us:
        problems.append("systemd: не удалось проверить unit rawlead-radar")
        return f"▶ Работает? · poll {poll} мин · {neon}"
    problems.append(f"systemd rawlead-radar: {us}")
    return f"⚠ systemd={us} · poll {poll} мин · {neon}"


def _source_row_label(source_id: str) -> str:
    if source_id == "fl":
        return "FL.ru"
    if source_id == "kwork":
        return "Kwork"
    return SOURCE_LABELS.get(source_id, source_id)


def _format_exchange_line(st: SourceCycleStats, *, neon_insert: int) -> str:
    label = _source_row_label(st.source_id).ljust(7)
    if st.fetch_error:
        return (
            f"{label} 🔴 {st.downloaded} скачано · "
            f"ошибка: {st.fetch_error[:50]}"
        )
    parts = [f"{st.downloaded} скачано", _ru_new(st.new_ids)]
    if st.new_ids > 0 and neon_insert > 0:
        parts.append(f"{min(st.new_ids, neon_insert)} в Neon")
    elif st.new_ids == 0:
        parts.append("fetch OK")
    return f"{label} 🟢 {' · '.join(parts)}"


def _tg_pulse_short(detail: str) -> str:
    d = detail.strip()
    if d.startswith("работает (пульс"):
        return d.replace("работает (", "").rstrip(")")
    return d


def _query_last_visible_feed(cfg: Config) -> tuple[str | None, str | None]:
    if cfg.radar_profile != "site":
        return None, None
    try:
        from pg_storage import pg_storage_from_config

        pg = pg_storage_from_config(cfg)
        if pg is None or not pg.enabled:
            return None, None
        with pg.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT created_at, source
                    FROM leads
                    WHERE is_visible = TRUE
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                )
                row = cur.fetchone()
                if not row or row[0] is None:
                    return None, None
                ts = row[0]
                source = str(row[1] or "").strip()
                if isinstance(ts, datetime):
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    ts_str = ts.astimezone(timezone.utc).strftime(
                        "%Y-%m-%d %H:%M:%S UTC"
                    )
                else:
                    ts_str = str(ts)
                src_short = source.split(":")[0] if source else ""
                return _human_ago(ts_str), src_short or None
    except Exception:
        return None, None


def _l1_backlog_label(backlog: int) -> str:
    if backlog <= _L1_BACKLOG_OK:
        return f"{backlog} (норма)"
    if backlog <= _L1_BACKLOG_WARN:
        return f"{backlog} (повышена)"
    return f"{backlog} (высокая)"


def _format_cycle_block_v2(
    summary: CycleSummary | None,
    rollup: str | None,
) -> list[str]:
    lines = ["", "── Цикл ──"]
    if summary is None or not summary.ts:
        lines.append("ещё не было цикла")
        return lines
    parts: list[str] = []
    if summary.cycle_sec > 0:
        parts.append(f"{summary.cycle_sec:.0f} с")
    if summary.neon_dup_skip:
        parts.append(f"neon_dup_skip={summary.neon_dup_skip}")
    if summary.dup_fast_skip:
        parts.append(f"dup_fast_skip={summary.dup_fast_skip}")
    if parts:
        lines.append(" · ".join(parts))
    if rollup:
        l1, _l2, visible = parse_site_rollup_metrics(rollup)
        lines.append(f"За 10 мин: L1={l1} · visible={visible}")
    elif summary.cycle_sec <= 0 and not summary.neon_dup_skip:
        lines.append(f"завершён {_human_ago(summary.ts) or summary.ts}")
    return lines


def _format_site_status_v2(
    cfg: Config,
    storage: ProjectStorage,
    problems: list[str],
    *,
    unit_state: str | None,
) -> list[str]:
    lines = ["", "── Биржи (последний цикл) ──"]
    summary = load_cycle_summary(storage)
    neon_ins = summary.neon_insert if summary else 0

    if summary and summary.ts:
        had_sources = False
        for st in summary.iter_sources():
            if st.source_id not in ("fl", "kwork"):
                continue
            had_sources = True
            if st.fetch_error:
                problems.append(f"{st.label}: {st.fetch_error[:80]}")
            lines.append(_format_exchange_line(st, neon_insert=neon_ins))
        if not had_sources:
            lines.append("биржи выкл в конфиге")
        if summary.misc_errors:
            problems.extend(str(e)[:80] for e in summary.misc_errors[:3])
    else:
        lines.append("ещё не было цикла")

    if radar_tg_enabled():
        ingest_down = bool(
            unit_state
            and unit_state.strip().lower() not in ("active", "activating")
        )
        if ingest_down:
            lines.append("TG      🔴 ingest остановлен")
        else:
            tg_ok, tg_detail = _tg_monitor_state(storage)
            icon = "🟢" if tg_ok else "🔴"
            if not tg_ok:
                problems.append(f"TG-монитор: {tg_detail}")
            lines.append(f"TG      {icon} {_tg_pulse_short(tg_detail)}")

    rollup = load_site_rollup_line(storage)
    lines.extend(_format_cycle_block_v2(summary, rollup))

    lines.append("")
    lines.append("── Лента ──")

    ago, src = _query_last_visible_feed(cfg)
    if ago:
        src_part = f" ({src})" if src else ""
        lines.append(f"Последний заказ на сайте: {ago}{src_part}")
    else:
        lines.append("Последний заказ на сайте: ещё не было")

    backlog_total = _query_l1_backlog(cfg)
    backlog_recent = _query_l1_backlog_recent(cfg, hours=48)
    drain_on = cfg.l1_backlog_drain
    if backlog_total is not None and backlog_recent is not None:
        backlog_hist = max(0, backlog_total - backlog_recent)
        lines.append(f"Без L1 (48 ч): {backlog_recent}")
        lines.append(f"Хвост исторический: {backlog_hist}")
        if backlog_recent > 0 and not drain_on:
            problems.append(
                f"Без L1 (48 ч)={backlog_recent} — свежие заказы ждут ИИ"
            )
        elif drain_on and backlog_total > _L1_BACKLOG_WARN:
            problems.append(
                f"Очередь L1={backlog_total} — drain on, но очередь велика"
            )
    elif backlog_total is not None:
        lines.append(f"Без L1 (48 ч): ?")
        lines.append(f"Всего без L1: {backlog_total}")
        if backlog_total > _L1_BACKLOG_WARN and drain_on:
            problems.append(
                f"Очередь L1={backlog_total} — drain on, но очередь велика"
            )

    return lines


def _format_legacy_status_v2(storage: ProjectStorage) -> list[str]:
    lines = ["", "── Neon consumer ──"]
    cycle_at = storage.get_setting(_STATUS_NEON_CYCLE_AT, "").strip()
    session = _int_setting(storage, _STATUS_NEON_SESSION_TO_BOT)
    last_sample = _int_setting(storage, _STATUS_NEON_LAST_SAMPLE)
    last_new = _int_setting(storage, _STATUS_NEON_LAST_NEW)
    last_to_bot = _int_setting(storage, _STATUS_NEON_LAST_TO_BOT)
    if cycle_at:
        ago = _human_ago(cycle_at) or cycle_at
        lines.append(
            f"Последний цикл: {ago} · выборка {last_sample} · "
            f"новых {last_new} · в бот {last_to_bot}"
        )
    else:
        lines.append("Последний цикл: ещё не было")
    lines.append(f"В бот за сессию: {session}")
    return lines


def _format_acc_compact(
    acc: str,
    acfg: TgMonitorAccountConfig | None,
    *,
    listen: int,
    in_file: int,
    ready: bool,
    pending: int,
    msgs: int,
    storage: ProjectStorage,
    cfg: Config,
) -> tuple[str, list[str]]:
    probs: list[str] = []
    chats = listen or in_file or (len(acfg.chat_ids) if acfg else 0)
    last_err = storage.get_setting(_tg_key(acc, "last_err"), "").strip()

    if not acfg or not acfg.chat_ids:
        if pending:
            return f"{acc} 🟡 нет chat_ids (join {pending})", probs
        return f"{acc} 🟡 нет chat_ids (только join)", probs

    if not ready:
        return f"{acc} 🟡 подключение · {chats} чатов", probs

    icon = "🔴" if last_err else "🟢"
    if last_err:
        probs.append(f"{acc}: {last_err[:80]}")
    if not is_bot_started(acc):
        probs.append(f"{acc}: нет /start в {_bot_label(cfg)}")
        icon = "🟡"
    msg_part = f" · +{msgs} msg" if msgs else ""
    return f"{acc} {icon} ready · {chats} чатов{msg_part}", probs


def _format_tg_accounts_v2(
    cfg: Config,
    storage: ProjectStorage,
    unit_state: str | None,
    problems: list[str],
) -> list[str]:
    ingest_down = bool(
        unit_state
        and unit_state.strip().lower() not in ("active", "activating")
    )
    if ingest_down:
        problems.append("Ingest остановлен — TG ниже из прошлой сессии")

    lines = ["── Telegram acc ──"]
    try:
        tg_cfg = load_tg_monitor_config()
        account_rows = {ac.account: ac for ac in tg_cfg.accounts}
        accounts = tuple(ac.account for ac in tg_cfg.accounts)
    except SystemExit:
        account_rows = {}
        accounts = ("acc1",)

    join_pending = _pending_join_by_account(load_tg_join_config().queue_csv)

    for acc in accounts:
        acfg = account_rows.get(acc)
        listen = _int_setting(storage, _tg_key(acc, "chats_listen"))
        in_file = _int_setting(storage, _tg_key(acc, "chats_file"))
        ready = _int_setting(storage, _tg_key(acc, "ready")) > 0
        pending = join_pending.get(acc, 0)
        cfg_ids = len(acfg.chat_ids) if acfg else in_file
        line, acc_probs = _format_acc_compact(
            acc,
            acfg,
            listen=listen,
            in_file=in_file or cfg_ids,
            ready=ready,
            pending=pending,
            msgs=_int_setting(storage, _tg_key(acc, "msgs")),
            storage=storage,
            cfg=cfg,
        )
        lines.append(line)
        problems.extend(acc_probs)

    return lines


def _collect_extra_problems(
    cfg: Config,
    storage: ProjectStorage,
    problems: list[str],
) -> None:
    bot_ok = _bot_start_ok(cfg)
    if bot_ok is False:
        problems.append(f"Acc не отправили /start в {_bot_label(cfg)}")
    if storage.get_setting("health_check_last_ok", "1") != "1":
        problems.append("Telethon health check: сбой (см. radar.log)")


def _pending_join_by_account(queue_csv: Path) -> dict[str, int]:
    out: dict[str, int] = {a: 0 for a in ("acc1", "acc2", "acc3")}
    if not queue_csv.is_file():
        return out
    with queue_csv.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("status", "").strip().lower() != "pending":
                continue
            acc = row.get("account", "").strip().lower()
            if acc in out:
                out[acc] += 1
    return out


def _tg_monitor_state(storage: ProjectStorage) -> tuple[bool, str]:
    if not is_tg_monitor_active():
        return False, "окно TG не запущено"
    raw = storage.get_setting(_TG_MONITOR_PULSE_KEY, "0").strip()
    try:
        last_pulse = float(raw)
    except ValueError:
        last_pulse = 0.0
    warmup = tg_monitor_warmup_remaining_sec(storage)
    if last_pulse <= 0:
        if warmup > 0:
            return True, f"прогрев (~{warmup}с)"
        return True, "старт, пульс ещё не был"
    age = int(time.time() - last_pulse)
    if age <= _TG_MONITOR_PULSE_MAX_AGE_SEC:
        return True, f"работает (пульс {age}с назад)"
    if warmup > 0:
        return True, f"прогрев (~{warmup}с, старый пульс {age}с)"
    return False, f"завис? ({age}с без пульса)"


def _tg_pulse_fresh(storage: ProjectStorage) -> bool:
    raw = storage.get_setting(_TG_MONITOR_PULSE_KEY, "0").strip()
    try:
        last_pulse = float(raw)
    except ValueError:
        last_pulse = 0.0
    if last_pulse <= 0:
        return tg_monitor_warmup_remaining_sec(storage) > 0
    return (time.time() - last_pulse) <= _TG_MONITOR_PULSE_MAX_AGE_SEC


def tg_pult_lamp_state(
    storage: ProjectStorage,
    *,
    process_alive: bool,
) -> tuple[str, str]:
    """
    Лампа TG на пульте: idle | warn (оранж) | ok | error.
    ok — все acc ready=1 и свежий пульс tg_main.
    """
    if not process_alive:
        return "idle", ""

    if not is_tg_monitor_active():
        return "warn", "запуск…"

    try:
        tg_cfg = load_tg_monitor_config()
        listening = tuple(ac for ac in tg_cfg.accounts if ac.chat_ids)
    except SystemExit:
        listening = ()

    if not listening:
        return "error", "нет чатов"

    total = len(listening)
    ready = sum(
        1
        for ac in listening
        if _int_setting(storage, _tg_key(ac.account, "ready")) > 0
    )

    if ready >= total and _tg_pulse_fresh(storage):
        return "ok", "слушает"

    warmup = tg_monitor_warmup_remaining_sec(storage)
    if warmup > 0:
        return "warn", f"прогрев (~{warmup}с)"
    if ready > 0:
        return "warn", f"подключение {ready}/{total}"
    return "warn", "подключение…"


def format_status_message(
    cfg: Config,
    storage: ProjectStorage,
    *,
    unit_state: str | None = None,
) -> str:
    profile_label = _profile_label(cfg.radar_profile)
    problems: list[str] = []

    lines = [
        f"📡 RawLead {profile_label} · {_bot_label(cfg)}",
        _ingest_headline(cfg, storage, unit_state, problems),
    ]

    if cfg.radar_profile == "site":
        lines.extend(
            _format_site_status_v2(
                cfg, storage, problems, unit_state=unit_state
            )
        )
    else:
        lines.extend(_format_legacy_status_v2(storage))

    if cfg.radar_profile == "site" or radar_tg_enabled():
        lines.append("")
        lines.extend(
            _format_tg_accounts_v2(cfg, storage, unit_state, problems)
        )

    _collect_extra_problems(cfg, storage, problems)

    if problems:
        seen: set[str] = set()
        unique: list[str] = []
        for p in problems:
            if p not in seen:
                seen.add(p)
                unique.append(p)
        lines.append("")
        lines.append("── Проблемы ──")
        for p in unique[:8]:
            lines.append(f"· {p}")
        if len(unique) > 8:
            lines.append(f"· … ещё {len(unique) - 8}")

    text = "\n".join(lines)
    if len(text) > _STATUS_MAX_LEN:
        text = text[: _STATUS_MAX_LEN - 1] + "…"
    return text
