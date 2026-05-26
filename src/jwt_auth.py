"""JWT для кабинета (§ P4): access_token TTL 7 дней."""

from __future__ import annotations

import os
import time
from typing import Any
from uuid import UUID

import jwt

_ALGORITHM = "HS256"
_TTL_SEC = 7 * 24 * 3600


def _secret() -> str:
    secret = (
        os.getenv("RAWLEAD_JWT_SECRET", "").strip()
        or os.getenv("RAWLEAD_API_KEY", "").strip()
    )
    if not secret:
        raise RuntimeError("RAWLEAD_JWT_SECRET or RAWLEAD_API_KEY required for JWT")
    return secret


def issue_access_token(user_id: str, *, tg_user_id: int) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "tg_id": int(tg_user_id),
        "iat": now,
        "exp": now + _TTL_SEC,
    }
    return jwt.encode(payload, _secret(), algorithm=_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        data = jwt.decode(
            token,
            _secret(),
            algorithms=[_ALGORITHM],
            options={"require": ["sub", "exp"]},
        )
    except jwt.PyJWTError as exc:
        raise ValueError("invalid token") from exc
    sub = str(data.get("sub", "")).strip()
    try:
        UUID(sub)
    except ValueError as exc:
        raise ValueError("invalid token subject") from exc
    return data
