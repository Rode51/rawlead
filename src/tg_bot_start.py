"""Telethon: /start у бота с мониторинговых acc (без телефона)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from config import _PROJECT_ROOT
from lead_pipeline import short_err
from tg_relay_allowlist import register_account_user_id

__all__ = [
    "DEFAULT_BOT_USERNAME",
    "ensure_bot_started",
    "flag_path_for_account",
    "is_bot_started",
    "mark_bot_started",
    "resolve_bot_username",
    "resolve_bot_start_accounts",
]

DEFAULT_BOT_USERNAME = "FLPARSINGBOT"


def resolve_bot_username() -> str:
    raw = os.environ.get("TELEGRAM_BOT_USERNAME", "").strip().lstrip("@")
    return raw or DEFAULT_BOT_USERNAME


def flag_path_for_account(account: str) -> Path:
    acc = account.strip().lower()
    return _PROJECT_ROOT / "data" / f".tg_bot_started_{acc}"


def is_bot_started(account: str) -> bool:
    return flag_path_for_account(account).is_file()


def mark_bot_started(account: str) -> None:
    path = flag_path_for_account(account)
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path.write_text(f"ok {ts}\n", encoding="utf-8")


def resolve_bot_start_accounts(account: str) -> tuple[str, ...]:
    key = account.strip().lower()
    if key == "all":
        return ("acc1", "acc2", "acc3")
    if key in ("acc1", "acc2", "acc3"):
        return (key,)
    raise ValueError(f"Неизвестный account {account!r}. Допустимо: acc1, acc2, acc3, all")


async def ensure_bot_started(
    client,
    account: str,
    *,
    force: bool = False,
    log_fn: Callable[[str], None] | None = None,
) -> bool:
    """
    Отправляет /start боту с acc-сессии, если ещё не было (флаг data/.tg_bot_started_<acc>).
    Возвращает True при успехе или если уже стартовали ранее.
    """
    acc = account.strip().lower()
    bot_username = resolve_bot_username()
    bot_id_raw = os.environ.get("TELEGRAM_BOT_USER_ID", "").strip()
    owner_raw = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    def _log(msg: str) -> None:
        if log_fn is not None:
            log_fn(msg)

    async def _bot_entity():
        if bot_id_raw:
            bid = int(bot_id_raw)
            if owner_raw and bid == int(owner_raw):
                raise ValueError("TELEGRAM_BOT_USER_ID = TELEGRAM_CHAT_ID")
            ent = await client.get_entity(bid)
            if not getattr(ent, "bot", False):
                raise ValueError(f"id {bid} не бот")
            return ent
        ent = await client.get_entity(bot_username)
        if not getattr(ent, "bot", False):
            raise ValueError(f"@{bot_username} не бот")
        return ent

    if is_bot_started(acc) and not force:
        _log(f"тг:бот_start:{acc}:skip (флаг есть)")
        try:
            me = await client.get_me()
            register_account_user_id(acc, int(me.id))
        except Exception:
            pass
        return True

    try:
        entity = await _bot_entity()
        await client.send_message(entity, "/start")
        me = await client.get_me()
        register_account_user_id(acc, int(me.id))
    except Exception as exc:
        _log(f"тг:бот_start:{acc}:ошибка: {short_err(exc)}")
        return False

    mark_bot_started(acc)
    target = f"bot_id={entity.id}" if bot_id_raw else f"@{bot_username}"
    _log(f"тг:бот_start:{acc}:ok {target}")
    return True
