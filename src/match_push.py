"""MATCH_PUSH (O30): уведомления подписчикам @rawlead_bot — per-user threshold."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import psycopg
import requests

from config import Config, telegram_requests_proxies
from rank import keyword_match, parse_lead_tags, tags_as_weights

logger = logging.getLogger(__name__)

_LENTA_URL = "https://rawlead.ru/lenta/"
_PUSH_MIN_MATCH_DEFAULT = 60


def upsert_subscriber_chat_id(
    database_url: str,
    *,
    tg_user_id: int,
    tg_chat_id: int,
) -> None:
    """`/start` non-admin: сохранить tg_chat_id (создать user при необходимости)."""
    url = database_url.strip()
    if not url:
        return
    try:
        with psycopg.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM users WHERE tg_user_id = %s",
                    (tg_user_id,),
                )
                row = cur.fetchone()
                if row:
                    cur.execute(
                        """
                        UPDATE users SET tg_chat_id = %s
                        WHERE tg_user_id = %s
                        """,
                        (tg_chat_id, tg_user_id),
                    )
                else:
                    user_id = str(uuid4())
                    cur.execute(
                        """
                        INSERT INTO users (id, tg_user_id, tg_chat_id)
                        VALUES (%s::uuid, %s, %s)
                        """,
                        (user_id, tg_user_id, tg_chat_id),
                    )
                    cur.execute(
                        """
                        INSERT INTO subscriptions (user_id, plan, is_active)
                        VALUES (%s::uuid, 'free', FALSE)
                        ON CONFLICT (user_id) DO NOTHING
                        """,
                        (user_id,),
                    )
                conn.commit()
    except Exception as exc:
        logger.warning("match_push:upsert_chat tg=%s: %s", tg_user_id, exc)


def merge_chat_id_on_login(cur: Any, *, tg_user_id: int, tg_chat_id: int | None) -> None:
    """Login Widget: если tg_chat_id уже известен из /start — merge на того же user."""
    if tg_chat_id is None:
        return
    cur.execute(
        """
        UPDATE users
        SET tg_chat_id = COALESCE(tg_chat_id, %s)
        WHERE tg_user_id = %s
        """,
        (tg_chat_id, tg_user_id),
    )


def _user_push_eligible(plan: str, is_active: bool, paused_until: datetime | None, now: datetime) -> bool:
    if paused_until is not None and paused_until > now:
        return False
    if plan == "owner":
        return True
    if plan in ("agent", "pro") and is_active:
        return True
    return False


def _load_user_tags(cur: Any, user_id: str) -> dict[str, float]:
    cur.execute(
        "SELECT tag, weight FROM user_tags WHERE user_id = %s::uuid",
        (user_id,),
    )
    rows = cur.fetchall()
    return tags_as_weights([str(r[0]) for r in rows])


def _format_push_text(*, title: str, task_summary: str, match_pct: int) -> str:
    head = (title or "Новый заказ").strip()[:120]
    summary = (task_summary or "").strip()
    if len(summary) > 160:
        summary = summary[:157].rstrip() + "…"
    lines = [f"🔔 Match {match_pct}%", head]
    if summary:
        lines.append(summary)
    lines.append(f"→ {_LENTA_URL}")
    return "\n".join(lines)


def _send_push_message(cfg: Config, chat_id: int, text: str) -> bool:
    proxies = telegram_requests_proxies(cfg)
    api_url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/sendMessage"
    markup = json.dumps(
        {
            "inline_keyboard": [[{"text": "Открыть ленту", "url": _LENTA_URL}]],
        },
        ensure_ascii=False,
    )
    try:
        session = requests.Session()
        session.trust_env = False
        resp = session.post(
            api_url,
            data={
                "chat_id": str(chat_id),
                "text": text,
                "reply_markup": markup,
                "disable_web_page_preview": True,
            },
            timeout=20.0,
            proxies=proxies,
        )
        if resp.status_code != 200:
            return False
        body = resp.json()
        return bool(body.get("ok"))
    except requests.RequestException:
        return False


def push_match_for_lead(
    cfg: Config,
    lead_id: int,
    *,
    title: str,
    task_summary: str,
    lead_tags: list[str],
    errors: list[str] | None = None,
) -> int:
    """
    После L1 visible lead: каждому paid/beta с tg_chat_id + push_enabled
    у кого km >= push_min_match → sendMessage.
    Возвращает число успешных push.
    """
    if not cfg.match_push_enabled or not cfg.database_url.strip():
        return 0

    err = errors if errors is not None else []
    now = datetime.now(timezone.utc)
    sent = 0

    try:
        with psycopg.connect(cfg.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT u.id, u.tg_chat_id, s.plan, s.is_active, s.paused_until,
                           COALESCE(u.push_min_match, %s),
                           COALESCE(u.push_enabled, TRUE)
                    FROM users u
                    INNER JOIN subscriptions s ON s.user_id = u.id
                    WHERE u.tg_chat_id IS NOT NULL
                    """,
                    (_PUSH_MIN_MATCH_DEFAULT,),
                )
                for user_id, chat_id, plan, is_active, paused_until, push_min_match, push_enabled in cur.fetchall():
                    if chat_id is None:
                        continue
                    if not bool(push_enabled):
                        continue
                    if not _user_push_eligible(
                        str(plan or "free"),
                        bool(is_active),
                        paused_until,
                        now,
                    ):
                        continue
                    user_tags = _load_user_tags(cur, str(user_id))
                    if not user_tags:
                        continue
                    km = keyword_match(lead_tags, user_tags)
                    if km < int(push_min_match):
                        continue
                    cur.execute(
                        """
                        SELECT 1 FROM match_push_log
                        WHERE user_id = %s::uuid AND lead_id = %s
                        """,
                        (user_id, lead_id),
                    )
                    if cur.fetchone():
                        continue
                    text = _format_push_text(
                        title=title,
                        task_summary=task_summary,
                        match_pct=km,
                    )
                    if not _send_push_message(cfg, chat_id, text):
                        err.append(f"push:match:fail user={user_id[:8]} lead={lead_id}")
                        continue
                    cur.execute(
                        """
                        INSERT INTO match_push_log (user_id, lead_id)
                        VALUES (%s::uuid, %s)
                        ON CONFLICT (user_id, lead_id) DO NOTHING
                        """,
                        (user_id, lead_id),
                    )
                    err.append(f"push:match:user={user_id[:8]} lead={lead_id} km={km} thr={push_min_match}")
                    sent += 1
                conn.commit()
    except Exception as exc:
        logger.warning("push_match_for_lead %d: %s", lead_id, exc)
        err.append(f"push:match:err lead={lead_id}:{exc}")

    return sent


def lead_tags_from_lite(lite: Any) -> list[str]:
    if lite is None:
        return []
    return parse_lead_tags(list(lite.lead_tags))
