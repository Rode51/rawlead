"""Сводка для кнопки «Статус» в Telegram-боте (общая SQLite для main и tg_main)."""

from __future__ import annotations

import csv
import json
import os
import time
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
    format_cycle_status_block,
    load_cycle_summary,
    load_site_rollup_line,
)
from storage import ProjectStorage
from tg_bot_start import is_bot_started, resolve_bot_username
from tg_client import resolve_telethon_account

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
    return f"@{resolve_bot_username()}"


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


def _format_ingest_state_line(
    storage: ProjectStorage,
    unit_state: str | None,
) -> str:
    """Явное состояние ingest: работает / пауза / остановлен (systemd)."""
    paused = storage.is_radar_paused()
    us = (unit_state or "").strip().lower()
    if us == "active":
        if paused:
            return (
                "⏸ Ingest: ПАУЗА — процесс жив, новые заказы не качаем"
            )
        return "▶ Ingest: РАБОТАЕТ — биржи и TG-монитор включены"
    if us in ("inactive", "failed", "dead"):
        note = " (флаг паузы в базе)" if paused else ""
        return f"🛑 Ingest: ОСТАНОВЛЕН — unit rawlead-radar выключен{note}"
    if us == "activating":
        return "⏳ Ingest: запускается (systemd activating)…"
    if us:
        return f"⚠ Ingest: systemd={us}"
    if paused:
        return "⏸ Ingest: ПАУЗА — ⚠ systemd: не удалось проверить"
    return "⚠ Ingest: systemd не удалось проверить (флаг паузы снят?)"


def _format_header_lines(
    cfg: Config,
    storage: ProjectStorage,
    *,
    unit_state: str | None = None,
) -> list[str]:
    profile = _profile_label(cfg.radar_profile)
    lines = [
        "📊 Статус радара",
        "",
        _format_ingest_state_line(storage, unit_state),
        "",
        f"Профиль: {profile} · бот {_bot_label(cfg)}",
        f"TELEGRAM_CHAT_ID: {cfg.telegram_chat_id}",
        f"Лог: {_log_file_name(cfg)} · пульт :{_control_port()}",
    ]
    if cfg.radar_profile == "site":
        conv = "вкл" if cfg.radar_conveyor else "выкл"
        lines.append(
            f"Конвейер: {conv} · опрос {cfg.poll_interval_minutes} мин"
        )
    else:
        mode = "Neon consumer" if legacy_neon_consumer_enabled() else "биржи"
        lines.append(
            f"Режим: {mode} · опрос {cfg.poll_interval_minutes} мин"
        )
    bot_ok = _bot_start_ok(cfg)
    if bot_ok is True:
        lines.append(f"Бот /start (acc): да · {_bot_label(cfg)}")
    elif bot_ok is False:
        lines.append(f"Бот /start (acc): нет · напишите /start в {_bot_label(cfg)}")
    return lines


def _format_site_block(cfg: Config, storage: ProjectStorage) -> list[str]:
    lines: list[str] = ["", "── Лента / Neon ──"]
    rollup = load_site_rollup_line(storage)
    if rollup:
        lines.append(f"Сводка 10 мин: {rollup}")
    else:
        lines.append("Сводка 10 мин: ещё не было")
    last_visible = _query_last_visible_at(cfg)
    if last_visible:
        lines.append(f"Последний visible в Neon: {last_visible}")
    backlog = _query_l1_backlog(cfg)
    if backlog is not None and backlog > 0:
        lines.append(f"Очередь без L1: {backlog}")
        if backlog > 100:
            lines.append("  ⚠ backlog > 100 — свежие fl/kwork ждут L1 (конвейер DESC)")
    summary = load_cycle_summary(storage)
    if summary and summary.ts:
        lines.append(f"Последний цикл: {summary.ts}")
        for st in summary.iter_sources():
            bits = [
                f"скачано {st.downloaded}",
                f"новых {st.new_ids}",
                f"neon_insert {summary.neon_insert}",
            ]
            if summary.is_visible:
                bits.append(f"is_visible {summary.is_visible}")
            if st.to_bot:
                bits.append(f"в бот {st.to_bot}")
            lines.append(f"  {st.label}: {' · '.join(bits)}")
    return lines


def _format_legacy_dogfood_block(storage: ProjectStorage) -> list[str]:
    lines: list[str] = ["", "── Dogfood / Neon ──"]
    cycle_at = storage.get_setting(_STATUS_NEON_CYCLE_AT, "").strip()
    session = _int_setting(storage, _STATUS_NEON_SESSION_TO_BOT)
    last_sample = _int_setting(storage, _STATUS_NEON_LAST_SAMPLE)
    last_new = _int_setting(storage, _STATUS_NEON_LAST_NEW)
    last_to_bot = _int_setting(storage, _STATUS_NEON_LAST_TO_BOT)
    if cycle_at:
        lines.append(
            f"Последний цикл consumer: {cycle_at} · выборка {last_sample} · "
            f"новых {last_new} · в бот {last_to_bot}"
        )
    else:
        lines.append("Последний цикл consumer: ещё не было")
    lines.append(f"В бот за сессию: {session}")
    return lines


def _account_label(account: str) -> str:
    try:
        _, session_path, _ = resolve_telethon_account(account)
        name = Path(session_path).name
        if name.endswith("_telethon"):
            name = name[: -len("_telethon")]
        return f"{account} ({name})"
    except SystemExit:
        return account


def _account_role_line(
    acfg: TgMonitorAccountConfig,
    *,
    listen: int,
    in_file: int,
    ready: bool,
    join_pending: int,
) -> str:
    if not acfg.chat_ids:
        if join_pending:
            return f"  Роль: только join-очередь ({join_pending} pending)"
        return "  Роль: нет chat_ids в конфиге — ждёт join или сид чатов"
    if listen > 0 and ready:
        return f"  Роль: слушает {listen} чат(ов)"
    if listen > 0:
        return f"  Роль: подключает {listen}/{len(acfg.chat_ids)} чат(ов) из файла"
    if in_file > 0:
        hint = f", join pending {join_pending}" if join_pending else ""
        return f"  Роль: {in_file} чат(ов) в файле, сессия не нашла{hint}"
    if join_pending:
        return f"  Роль: join-очередь ({join_pending}), чаты пока не в сессии"
    return "  Роль: чаты в конфиге, ожидание подключения"


def _msgs_zero_hint(
    *,
    listen: int,
    in_file: int,
    join_pending: int,
    ready: bool,
    bot_ok: bool,
) -> str | None:
    if listen == 0 and in_file == 0 and join_pending == 0:
        return "  Входящих ещё не было — нет чатов в конфиге; добавьте ids или join"
    if listen == 0 and join_pending > 0:
        return (
            "  Входящих ещё не было — join в очереди; после вступления появятся чаты"
        )
    if listen > 0 and not ready:
        return "  Входящих ещё не было — acc ещё не ready (подключение)"
    if listen > 0 and not bot_ok:
        return "  Входящих ещё не было — бот /start не отправлен; forward заблокирован"
    if listen > 0:
        return "  Входящих ещё не было — слушает; ждём пост в группах"
    return None


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
    lines = _format_header_lines(cfg, storage, unit_state=unit_state)

    if cfg.radar_profile == "site":
        lines.extend(_format_site_block(cfg, storage))
    else:
        lines.extend(_format_legacy_dogfood_block(storage))

    ingest_down = bool(
        unit_state and unit_state.strip().lower() not in ("active", "activating")
    )

    if cfg.radar_profile == "site" or radar_tg_enabled():
        lines.append("")
        if ingest_down:
            lines.append(
                "Telegram-монитор: 🔴 не работает (ingest остановлен; ниже — архив прошлой сессии)"
            )
        else:
            tg_ok, tg_detail = _tg_monitor_state(storage)
            icon = "🟢" if tg_ok else "🔴"
            lines.append(f"Telegram-монитор: {icon} {tg_detail}")

        try:
            tg_cfg = load_tg_monitor_config()
            account_rows = {ac.account: ac for ac in tg_cfg.accounts}
            accounts = tuple(ac.account for ac in tg_cfg.accounts)
        except SystemExit:
            account_rows = {}
            accounts = ("acc1",)

        join_pending = _pending_join_by_account(load_tg_join_config().queue_csv)

        for acc in accounts:
            lines.append("")
            lines.append(_account_label(acc))
            acfg = account_rows.get(acc)
            listen = _int_setting(storage, _tg_key(acc, "chats_listen"))
            in_file = _int_setting(storage, _tg_key(acc, "chats_file"))
            ready = _int_setting(storage, _tg_key(acc, "ready")) > 0
            pending = join_pending.get(acc, 0)
            cfg_ids = len(acfg.chat_ids) if acfg else in_file
            if acfg:
                lines.append(
                    _account_role_line(
                        acfg,
                        listen=listen,
                        in_file=in_file or cfg_ids,
                        ready=ready,
                        join_pending=pending,
                    )
                )
            lines.append(f"  ready: {'да' if ready else 'нет'}")
            acc_bot_ok = is_bot_started(acc)
            lines.append(
                f"  Бот /start ({_bot_label(cfg)}): {'да' if acc_bot_ok else 'нет'}"
            )
            if listen or in_file or cfg_ids:
                lines.append(
                    f"  Чатов: слушаем {listen} / в файле {in_file or cfg_ids}"
                )
            started = storage.get_setting(_tg_key(acc, "started_at"), "").strip()
            if started:
                lines.append(f"  Сессия с: {started}")
            msgs = _int_setting(storage, _tg_key(acc, "msgs"))
            lines.append(
                f"  Сообщений: {msgs} · "
                f"новых: {_int_setting(storage, _tg_key(acc, 'new'))} · "
                f"в бот: {_int_setting(storage, _tg_key(acc, 'notified'))}"
            )
            if msgs == 0:
                hint = _msgs_zero_hint(
                    listen=listen,
                    in_file=in_file or cfg_ids,
                    join_pending=pending,
                    ready=ready,
                    bot_ok=acc_bot_ok,
                )
                if hint:
                    lines.append(hint)
            if pending:
                lines.append(f"  Join в очереди: {pending}")
            phase = storage.get_setting(_tg_key(acc, "phase"), "").strip()
            last_action = storage.get_setting(_tg_key(acc, "last_action"), "").strip()
            if phase:
                lines.append(f"  phase: {phase}")
            if last_action:
                lines.append(f"  last: {last_action[:220]}")
            last_err = storage.get_setting(_tg_key(acc, "last_err"), "").strip()
            if last_err:
                lines.append(f"  ⚠ {last_err[:200]}")
    elif cfg.radar_profile == "legacy":
        lines.append("")
        lines.append("Telegram-монитор: выкл (Legacy — только Neon → бот)")

    health_ok = storage.get_setting("health_check_last_ok", "1") == "1"
    if not health_ok:
        lines.append("")
        lines.append("⚠ Последняя проверка Telethon: сбой (см. radar.log)")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:3990] + "\n…"
    return text
