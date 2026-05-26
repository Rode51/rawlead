"""Сводка для кнопки «Статус» в Telegram-боте (общая SQLite для main и tg_main)."""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

from config import (
    Config,
    TgMonitorAccountConfig,
    load_tg_join_config,
    load_tg_monitor_config,
    radar_timestamp,
)
from health_check import (
    _TG_MONITOR_PULSE_KEY,
    _TG_MONITOR_PULSE_MAX_AGE_SEC,
    is_tg_monitor_active,
    tg_monitor_warmup_remaining_sec,
)
from radar_cycle_log import format_cycle_status_block, load_cycle_summary
from storage import ProjectStorage
from tg_bot_start import is_bot_started
from tg_client import resolve_telethon_account

_STATUS_FL_CYCLE_AT = "status_fl_cycle_at"
_STATUS_FL = (
    "status_fl_cards_fl",
    "status_fl_cards_kwork",
    "status_fl_new",
    "status_fl_notified",
    "status_fl_errors",
)


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


def format_status_message(cfg: Config, storage: ProjectStorage) -> str:
    lines: list[str] = []
    paused = storage.is_radar_paused()
    lines.append("📊 Статус радара")
    lines.append("")
    lines.append(
        f"Биржи FL/Kwork: {'⏸ на паузе' if paused else '▶ активен'} · "
        f"опрос {cfg.poll_interval_minutes} мин"
    )

    lines.extend(format_cycle_status_block(storage))

    lines.append("")
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
        bot_ok = is_bot_started(acc)
        lines.append(f"  Бот /start: {'да' if bot_ok else 'нет'}")
        if listen or in_file or cfg_ids:
            lines.append(f"  Чатов: слушаем {listen} / в файле {in_file or cfg_ids}")
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
                bot_ok=bot_ok,
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

    health_ok = storage.get_setting("health_check_last_ok", "1") == "1"
    if not health_ok:
        lines.append("")
        lines.append("⚠ Последняя проверка Telethon: сбой (см. radar.log)")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:3990] + "\n…"
    return text
