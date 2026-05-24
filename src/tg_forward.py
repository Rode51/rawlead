"""Пересылка оригинала TG-поста: acc (Telethon) → @FLPARSINGBOT → владелец (Bot API)."""

from __future__ import annotations

import asyncio
import os

from telethon.errors import FloodWaitError
from telethon.tl.custom.message import Message

from config import Config
from lead_pipeline import short_err
from tg_bot_start import is_bot_started, resolve_bot_username
from tg_chain_log import log_telethon_forward_ok, log_telethon_forward_start
from telegram_control import relay_message_to_owner_chat

__all__ = ["format_tg_acc_label", "forward_listing_to_owner"]

_RELAY_VERSION = "acc-to-bot-v6"
_RELAY_SYNC_RETRIES = 3
_RELAY_SYNC_PAUSE_SEC = 0.75


def format_tg_acc_label(account: str, chat_title: str = "") -> str:
    """Метка источника в боте, напр. acc2 · ПОМОГАТОР."""
    acc = account.strip().lower()
    title = (chat_title or "").strip()
    if title:
        return f"{acc} · {title}"
    return acc


async def _resolve_bot_entity(client):
    bot_username = resolve_bot_username()
    bot_id_raw = os.environ.get("TELEGRAM_BOT_USER_ID", "").strip()
    owner_raw = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
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


async def forward_listing_to_owner(
    client,
    message: Message,
    cfg: Config,
    *,
    errors: list[str],
    account: str = "",
    chat_title: str = "",
) -> bool:
    """Acc → @FLPARSINGBOT (Telethon), затем бот → TELEGRAM_CHAT_ID (Bot API)."""
    del chat_title  # метка только в карточке ИИ (tg_acc_label)

    acc = account.strip().lower()
    if acc and not is_bot_started(acc):
        errors.append(
            f"tg:forward:acc {acc} не стартовал бота — "
            f"scripts/tg_bot_start.py --account {acc}"
        )
        return False

    try:
        owner_id = int(cfg.telegram_chat_id.strip())
    except ValueError:
        errors.append("tg:forward:TELEGRAM_CHAT_ID не число")
        return False

    try:
        bot_entity = await _resolve_bot_entity(client)
        bot_id = int(bot_entity.id)
    except Exception as exc:
        errors.append(f"tg:forward:bot:{short_err(exc)}")
        return False

    if bot_id == owner_id:
        errors.append("tg:forward:bot_id=owner_id — проверь TELEGRAM_BOT_USER_ID")
        return False

    try:
        me = await client.get_me()
        acc_uid = int(me.id)
    except Exception as exc:
        errors.append(f"tg:forward:acc_me:{short_err(exc)}")
        return False

    src_chat_id = int(message.chat_id or 0)
    src_msg_id = int(message.id)
    log_telethon_forward_start(
        errors,
        acc=acc or "?",
        acc_uid=acc_uid,
        bot_id=bot_id,
        owner_id=owner_id,
        src_chat_id=src_chat_id,
        src_msg_id=src_msg_id,
        version=_RELAY_VERSION,
    )

    try:
        forwarded = await client.forward_messages(bot_entity, message)
    except FloodWaitError as exc:
        errors.append(f"tg:forward:FloodWait {exc.seconds}s")
        return False
    except Exception as exc:
        errors.append(f"tg:forward:{short_err(exc)}")
        return False

    log_telethon_forward_ok(errors, bot_id=bot_id, owner_id=owner_id)

    if isinstance(forwarded, list):
        fwd_msg = forwarded[0] if forwarded else None
    else:
        fwd_msg = forwarded
    if fwd_msg is None:
        errors.append("tg:forward:empty_result")
        return False

    fwd_msg_id = int(fwd_msg.id)
    relay_ok = False
    for attempt in range(_RELAY_SYNC_RETRIES):
        relay_ok = relay_message_to_owner_chat(
            cfg,
            from_chat_id=acc_uid,
            message_id=fwd_msg_id,
            account=acc,
            errors=errors,
        )
        if relay_ok:
            errors.append(f"тг:relay:{acc or '?'}:msg={fwd_msg_id}")
            break
        if attempt + 1 < _RELAY_SYNC_RETRIES:
            await asyncio.sleep(_RELAY_SYNC_PAUSE_SEC)

    if not relay_ok:
        # Telethon id часто ≠ Bot API; poll (getUpdates) догонит пересыл.
        errors.append(f"тг:relay:{acc or '?'}:defer msg={fwd_msg_id}")

    return True
