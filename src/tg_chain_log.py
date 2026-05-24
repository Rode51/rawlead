"""Trace-логи цепочки acc → бот → владелец (строки в radar.log через errors)."""

from __future__ import annotations

import os

from config import Config

__all__ = [
    "chain_log",
    "log_config_ids",
    "log_relay_api_call",
    "log_relay_poll_batch",
    "log_telethon_forward_start",
    "log_telethon_forward_ok",
]


def chain_log(errors: list[str], msg: str) -> None:
    """Одна строка; попадает в «ош=» у «тг:сообщ»."""
    errors.append(f"tg:цепь:{msg}")


def log_config_ids(cfg: Config, errors: list[str], *, version: str = "") -> None:
    """Сводка id из .env при старте tg_main."""
    try:
        owner_id = int(cfg.telegram_chat_id.strip())
    except ValueError:
        owner_id = "?"
    bot_raw = os.environ.get("TELEGRAM_BOT_USER_ID", "").strip()
    bot_id = bot_raw or "getMe"
    ver = f" ver={version}" if version else ""
    chain_log(
        errors,
        f"ids owner(TELEGRAM_CHAT_ID)={owner_id} bot(TELEGRAM_BOT_USER_ID)={bot_id}{ver}",
    )


def log_telethon_forward_start(
    errors: list[str],
    *,
    acc: str,
    acc_uid: int,
    bot_id: int,
    owner_id: int,
    src_chat_id: int,
    src_msg_id: int,
    version: str,
) -> None:
    chain_log(
        errors,
        f"1/3 старт acc={acc} acc_uid={acc_uid} bot_id={bot_id} owner_id={owner_id} "
        f"src_chat={src_chat_id} src_msg={src_msg_id} {version}",
    )


def log_telethon_forward_ok(errors: list[str], *, bot_id: int, owner_id: int) -> None:
    chain_log(
        errors,
        f"2/3 telethon→бот ok dest_bot_id={bot_id} (не owner_id={owner_id})",
    )


def log_relay_poll_batch(
    errors: list[str],
    *,
    attempt: int,
    inbox_n: int,
    acc_uid: int,
    owner_id: int,
) -> None:
    chain_log(
        errors,
        f"3/3 poll#{attempt} inbox={inbox_n} ищем from_user_id={acc_uid} owner_id={owner_id}",
    )


def log_relay_api_call(
    errors: list[str],
    *,
    owner_chat_id: int,
    from_chat_id: int,
    message_id: int,
    account: str = "",
) -> None:
    acc = account.strip()
    prefix = f"acc={acc} " if acc else ""
    chain_log(
        errors,
        f"{prefix}BotAPI forwardMessage →chat_id={owner_chat_id} "
        f"from_chat_id={from_chat_id} msg_id={message_id}",
    )
