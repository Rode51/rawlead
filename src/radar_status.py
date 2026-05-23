"""Сводка для кнопки «Статус» в Telegram-боте (общая SQLite для main и tg_main)."""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path

from config import Config, load_tg_join_config, load_tg_monitor_config, radar_timestamp
from health_check import (
    _TG_MONITOR_PULSE_KEY,
    _TG_MONITOR_PULSE_MAX_AGE_SEC,
    is_tg_monitor_active,
)
from storage import ProjectStorage
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
        for suffix in ("msgs", "new", "notified", "last_err"):
            storage.set_setting(_tg_key(acc, suffix), "0" if suffix != "last_err" else "")


def record_tg_monitor_start(
    storage: ProjectStorage,
    account: str,
    *,
    chats_listen: int,
    chats_in_file: int,
) -> None:
    acc = account.strip().lower()
    storage.set_setting(_tg_key(acc, "chats_listen"), str(chats_listen))
    storage.set_setting(_tg_key(acc, "chats_file"), str(chats_in_file))
    storage.set_setting(_tg_key(acc, "started_at"), radar_timestamp())


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


def record_tg_skip(
    storage: ProjectStorage,
    account: str,
    detail: str,
) -> None:
    storage.set_setting(_tg_key(account.strip().lower(), "last_err"), detail[:400])


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
    if last_pulse <= 0:
        return True, "старт, пульс ещё не был"
    age = int(time.time() - last_pulse)
    if age <= _TG_MONITOR_PULSE_MAX_AGE_SEC:
        return True, f"работает (пульс {age}с назад)"
    return False, f"завис? ({age}с без пульса)"


def format_status_message(cfg: Config, storage: ProjectStorage) -> str:
    lines: list[str] = []
    paused = storage.is_radar_paused()
    lines.append("📊 Статус радара")
    lines.append("")
    lines.append(
        f"Биржи FL/Kwork: {'⏸ на паузе' if paused else '▶ активен'} · "
        f"опрос {cfg.poll_interval_minutes} мин"
    )

    cycle_at = storage.get_setting(_STATUS_FL_CYCLE_AT, "").strip()
    if cycle_at:
        lines.append(f"Последний цикл: {cycle_at}")
        lines.append(
            f"  Карточки: FL {_int_setting(storage, _STATUS_FL[0])}, "
            f"Kwork {_int_setting(storage, _STATUS_FL[1])}"
        )
        lines.append(
            f"  Новых: {_int_setting(storage, _STATUS_FL[2])} · "
            f"в бот: {_int_setting(storage, _STATUS_FL[3])}"
        )
        err_raw = storage.get_setting(_STATUS_FL[4], "[]")
        try:
            fl_errors = json.loads(err_raw)
        except json.JSONDecodeError:
            fl_errors = []
        if fl_errors:
            lines.append("  Ошибки цикла:")
            for e in fl_errors[:3]:
                lines.append(f"    · {str(e)[:120]}")
    else:
        lines.append("Последний цикл: ещё не было")

    lines.append("")
    tg_ok, tg_detail = _tg_monitor_state(storage)
    icon = "🟢" if tg_ok else "🔴"
    lines.append(f"Telegram-монитор: {icon} {tg_detail}")

    try:
        tg_cfg = load_tg_monitor_config()
        accounts = tuple(ac.account for ac in tg_cfg.accounts)
    except SystemExit:
        accounts = ("acc1",)

    join_pending = _pending_join_by_account(load_tg_join_config().queue_csv)

    for acc in accounts:
        lines.append("")
        lines.append(_account_label(acc))
        listen = _int_setting(storage, _tg_key(acc, "chats_listen"))
        in_file = _int_setting(storage, _tg_key(acc, "chats_file"))
        if listen or in_file:
            lines.append(f"  Чатов: слушаем {listen} / в файле {in_file}")
        started = storage.get_setting(_tg_key(acc, "started_at"), "").strip()
        if started:
            lines.append(f"  Сессия с: {started}")
        lines.append(
            f"  Сообщений: {_int_setting(storage, _tg_key(acc, 'msgs'))} · "
            f"новых: {_int_setting(storage, _tg_key(acc, 'new'))} · "
            f"в бот: {_int_setting(storage, _tg_key(acc, 'notified'))}"
        )
        pending = join_pending.get(acc, 0)
        if pending:
            lines.append(f"  Join в очереди: {pending}")
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
