"""Пересылка оригинала TG-поста владельцу (Telethon → TELEGRAM_CHAT_ID)."""

from __future__ import annotations

from telethon.errors import FloodWaitError
from telethon.tl.custom.message import Message

from config import Config
from lead_pipeline import short_err

__all__ = ["format_tg_acc_label", "forward_listing_to_owner"]


def format_tg_acc_label(account: str, chat_title: str = "") -> str:
    """Метка источника в боте, напр. acc2 · ПОМОГАТОР."""
    acc = account.strip().lower()
    title = (chat_title or "").strip()
    if title:
        return f"{acc} · {title}"
    return acc


async def forward_listing_to_owner(
    client,
    message: Message,
    cfg: Config,
    *,
    errors: list[str],
    account: str = "",
    chat_title: str = "",
) -> bool:
    """Пересылает сообщение в личку владельца (тот же chat_id, что у Bot API)."""
    raw = str(cfg.telegram_chat_id or "").strip()
    try:
        dest = int(raw)
    except ValueError:
        errors.append("tg:forward:TELEGRAM_CHAT_ID не число")
        return False

    try:
        label = format_tg_acc_label(account, chat_title) if account else ""
        if label:
            await client.send_message(dest, label)
        await client.forward_messages(dest, message)
        return True
    except FloodWaitError as exc:
        errors.append(f"tg:forward:FloodWait {exc.seconds}s")
        return False
    except Exception as exc:
        errors.append(f"tg:forward:{short_err(exc)}")
        return False
