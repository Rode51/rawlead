"""Проверка данных Telegram Login Widget (§ P4)."""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Any

_MAX_AUTH_AGE_SEC = 86400


def login_bot_token() -> str:
    """Токен бота для Login Widget (тот же, что у notify-бота, если отдельный не задан)."""
    return (
        os.getenv("TELEGRAM_LOGIN_BOT_TOKEN", "").strip()
        or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    )


def verify_telegram_login(payload: dict[str, Any], *, bot_token: str) -> None:
    """
  Проверка hash по https://core.telegram.org/widgets/login#checking-authorization
  Raises ValueError при неверных данных.
    """
    if not bot_token:
        raise ValueError("telegram bot token not configured")

    data = {k: v for k, v in payload.items() if v is not None and k != "hash"}
    received_hash = str(payload.get("hash", "") or "").strip()
    if not received_hash:
        raise ValueError("missing hash")

    check_parts = [f"{key}={data[key]}" for key in sorted(data.keys())]
    check_string = "\n".join(check_parts)
    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    computed = hmac.new(
        secret_key,
        check_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(computed, received_hash):
        raise ValueError("invalid telegram hash")

    try:
        auth_date = int(data.get("auth_date", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid auth_date") from exc
    if auth_date <= 0:
        raise ValueError("invalid auth_date")
    if time.time() - auth_date > _MAX_AUTH_AGE_SEC:
        raise ValueError("auth data expired")
