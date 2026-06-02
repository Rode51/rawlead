"""O84/O85: Telegram bot deep-link login — shared by API and bot poller (no FastAPI import)."""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

import psycopg

from match_push import merge_chat_id_on_login

logger = logging.getLogger(__name__)

BOT_SESSION_TTL_SEC = 5 * 60
BOT_AUTH_PREFIX = "auth_"


def _db_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return url


def cabinet_base_url() -> str:
    raw = os.environ.get("RAWLEAD_CABINET_URL", "").strip()
    if raw:
        return raw.rstrip("/") + "/"
    return "https://rawlead.ru/cabinet/"


def hash_bot_auth_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def cabinet_return_url(auth_token: str) -> str:
    base = cabinet_base_url()
    sep = "&" if "?" in base else "?"
    return f"{base}{sep}auth={auth_token}"


def merge_chat_id_on_login_standalone(tg_user_id: int, tg_chat_id: int) -> None:
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                merge_chat_id_on_login(cur, tg_user_id=tg_user_id, tg_chat_id=tg_chat_id)
            conn.commit()
    except Exception as exc:
        logger.warning("merge_chat_id_on_login_standalone tg=%s: %s", tg_user_id, exc)


def authorize_bot_auth_session(
    *,
    auth_token: str,
    tg_user_id: int,
    tg_chat_id: int,
    username: str | None = None,
    first_name: str | None = None,
    photo_url: str | None = None,
) -> tuple[bool, str, str]:
    """Bot `/start auth_*`: bind tg_user_id → session. Returns (ok, return_url, error)."""
    token = (auth_token or "").strip()
    if not token:
        return False, "", "empty token"
    token_hash = hash_bot_auth_token(token)
    now = datetime.now(timezone.utc)
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT expires_at, tg_user_id, consumed_at
                    FROM auth_bot_sessions
                    WHERE token_hash = %s
                    """,
                    (token_hash,),
                )
                row = cur.fetchone()
                if not row:
                    return False, "", "session not found"
                expires_at, existing_tg, consumed_at = row
                if consumed_at is not None:
                    return False, "", "session consumed"
                exp = expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if exp <= now:
                    return False, "", "session expired"
                if existing_tg is not None and int(existing_tg) != int(tg_user_id):
                    return False, "", "session bound to another user"
                cur.execute(
                    """
                    UPDATE auth_bot_sessions
                    SET tg_user_id = %s,
                        tg_username = %s,
                        tg_first_name = %s,
                        tg_photo_url = %s,
                        authorized_at = %s
                    WHERE token_hash = %s
                    """,
                    (
                        int(tg_user_id),
                        username,
                        first_name,
                        photo_url,
                        now,
                        token_hash,
                    ),
                )
            conn.commit()
    except Exception as exc:
        logger.error("authorize_bot_auth_session: %s", exc)
        return False, "", "db error"
    merge_chat_id_on_login_standalone(int(tg_user_id), int(tg_chat_id))
    return True, cabinet_return_url(token), ""


def mint_bot_first_login_url(
    *,
    tg_user_id: int,
    tg_chat_id: int,
    username: str | None = None,
    first_name: str | None = None,
    photo_url: str | None = None,
) -> str:
    """Bot `/start login`: mint pre-authorized session → cabinet URL (TTL 5 min)."""
    plain = secrets.token_urlsafe(32)
    token_hash = hash_bot_auth_token(plain)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(seconds=BOT_SESSION_TTL_SEC)
    with psycopg.connect(_db_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO auth_bot_sessions (
                    token_hash, expires_at, tg_user_id, tg_username,
                    tg_first_name, tg_photo_url, authorized_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    token_hash,
                    expires,
                    int(tg_user_id),
                    username,
                    first_name,
                    photo_url,
                    now,
                ),
            )
        conn.commit()
    merge_chat_id_on_login_standalone(int(tg_user_id), int(tg_chat_id))
    return cabinet_return_url(plain)


def create_bot_session() -> tuple[str, str, datetime]:
    """Site step 1: mint token + deep link. Returns (plain_token, deep_link, expires_at)."""
    plain = secrets.token_urlsafe(32)
    token_hash = hash_bot_auth_token(plain)
    expires = datetime.now(timezone.utc) + timedelta(seconds=BOT_SESSION_TTL_SEC)
    bot_user = os.environ.get("TELEGRAM_BOT_USERNAME", "rawlead_bot").strip().lstrip("@") or "rawlead_bot"
    with psycopg.connect(_db_url()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO auth_bot_sessions (token_hash, expires_at)
                VALUES (%s, %s)
                """,
                (token_hash, expires),
            )
        conn.commit()
    deep_link = f"https://t.me/{bot_user}?start={BOT_AUTH_PREFIX}{plain}"
    return plain, deep_link, expires
