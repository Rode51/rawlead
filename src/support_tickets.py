"""O116-W4: support tickets — Neon threads + TG notify owner."""

from __future__ import annotations

import logging
import re
from typing import Any

from src.config import Config, load_config
from src.telegram_control import TelegramControlError, _send_to_chat

logger = logging.getLogger(__name__)

_SUPPORT_SOURCES = frozenset({"fab", "contact"})
_GUEST_TOKEN_RE = re.compile(r"^[a-zA-Z0-9_-]{8,64}$")
_BODY_MAX = 4000
_BODY_MIN = 3
_PREVIEW_MAX = 280
_SUPPORT_NOTICE_RE = re.compile(
    r"^(?:Тикет от пользователя|Новое сообщение в тикете)\s+(\d+)",
    re.IGNORECASE,
)
_SUPPORT_FALLBACK_HASH_RE = re.compile(r"^#(\d+)\s+(.+)", re.DOTALL)
_SUPPORT_FALLBACK_T_RE = re.compile(r"^[тt](\d+):\s*(.+)", re.IGNORECASE | re.DOTALL)


def parse_ticket_id_from_notice(text: str) -> int | None:
    """Extract ticket id from owner TG notice header."""
    m = _SUPPORT_NOTICE_RE.match((text or "").strip())
    if not m:
        return None
    return int(m.group(1))


def parse_admin_fallback_reply(text: str) -> tuple[int, str] | None:
    """`#42 текст` or `т42: текст` — owner fallback without reply."""
    s = (text or "").strip()
    if not s:
        return None
    m = _SUPPORT_FALLBACK_HASH_RE.match(s)
    if m:
        return int(m.group(1)), m.group(2).strip()
    m = _SUPPORT_FALLBACK_T_RE.match(s)
    if m:
        return int(m.group(1)), m.group(2).strip()
    return None


def normalize_guest_token(value: str) -> str | None:
    token = (value or "").strip()
    if not token or not _GUEST_TOKEN_RE.fullmatch(token):
        return None
    return token


def normalize_source(value: str) -> str:
    src = (value or "fab").strip().lower()
    return src if src in _SUPPORT_SOURCES else "fab"


def normalize_body(value: str) -> str:
    body = (value or "").strip()
    if len(body) < _BODY_MIN:
        raise ValueError("message too short")
    if len(body) > _BODY_MAX:
        body = body[:_BODY_MAX]
    return body


def preview_text(body: str, *, limit: int = _PREVIEW_MAX) -> str:
    text = " ".join((body or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def send_owner_support_notice(
    cfg: Config,
    *,
    ticket_id: int,
    tg_username: str | None,
    tg_user_id: int | None,
    user_id: str | None,
    preview: str,
    is_new_ticket: bool,
) -> bool:
    """Bot API sendMessage → TELEGRAM_CHAT_ID (владелец)."""
    chat_id = (cfg.telegram_chat_id or "").strip()
    token = (cfg.telegram_bot_token or "").strip()
    if not chat_id or not token:
        logger.warning("support_tg: missing bot token or chat id")
        return False

    uname = (tg_username or "").strip().lstrip("@")
    uname_part = f"@{uname}" if uname else "—"
    uid_part = str(tg_user_id) if tg_user_id else "—"
    db_part = (user_id or "guest")[:36]
    prev = preview_text(preview)

    if is_new_ticket:
        header = f"Тикет от пользователя {ticket_id}"
    else:
        header = f"Новое сообщение в тикете {ticket_id}"

    text = (
        f"{header}\n"
        f"TG: {uname_part} · id {uid_part}\n"
        f"user_id: {db_part}\n"
        f"\n{prev}\n"
        f"\nОтветь на это сообщение"
    )
    try:
        _send_to_chat(
            cfg,
            chat_id,
            text,
            with_admin_keyboard=False,
            timeout_sec=20.0,
        )
        return True
    except TelegramControlError as exc:
        logger.warning("support_tg: %s", exc)
        return False


def _user_row(cur: Any, user_id: str) -> tuple[str | None, int | None]:
    cur.execute(
        "SELECT tg_username, tg_user_id FROM users WHERE id = %s::uuid",
        (user_id,),
    )
    row = cur.fetchone()
    if not row:
        return None, None
    uname = row[0] if row[0] else None
    tg_uid = int(row[1]) if row[1] is not None else None
    return uname, tg_uid


def get_or_create_ticket(
    cur: Any,
    *,
    user_id: str | None,
    guest_token: str | None,
    source: str,
    page_url: str,
) -> tuple[int, bool]:
    """Return (ticket_id, is_new_ticket)."""
    existing = ticket_for_actor(cur, user_id=user_id, guest_token=guest_token)
    if existing is not None:
        if user_id:
            cur.execute(
                """
                UPDATE support_tickets
                SET user_id = %s::uuid
                WHERE id = %s AND user_id IS NULL
                """,
                (user_id, existing),
            )
        return existing, False

    cur.execute(
        """
        INSERT INTO support_tickets (user_id, guest_token, source, page_url)
        VALUES (%s::uuid, %s, %s, %s)
        RETURNING id
        """,
        (user_id, guest_token, source, (page_url or "")[:500]),
    )
    new_row = cur.fetchone()
    if not new_row:
        raise RuntimeError("support ticket insert failed")
    return int(new_row[0]), True


def append_user_message(
    cur: Any,
    *,
    ticket_id: int,
    body: str,
) -> int:
    cur.execute(
        """
        INSERT INTO support_messages (ticket_id, from_role, body)
        VALUES (%s, 'user', %s)
        RETURNING id
        """,
        (ticket_id, body),
    )
    row = cur.fetchone()
    cur.execute(
        "UPDATE support_tickets SET updated_at = NOW() WHERE id = %s",
        (ticket_id,),
    )
    return int(row[0]) if row else 0


def append_owner_reply(cur: Any, *, ticket_id: int, body: str) -> int:
    cur.execute(
        """
        INSERT INTO support_messages (ticket_id, from_role, body)
        VALUES (%s, 'owner', %s)
        RETURNING id
        """,
        (ticket_id, body),
    )
    row = cur.fetchone()
    cur.execute(
        "UPDATE support_tickets SET updated_at = NOW() WHERE id = %s",
        (ticket_id,),
    )
    return int(row[0]) if row else 0


def ticket_for_actor(
    cur: Any,
    *,
    user_id: str | None,
    guest_token: str | None,
) -> int | None:
    clauses: list[str] = []
    params: list[Any] = []
    if user_id:
        clauses.append("user_id = %s::uuid")
        params.append(user_id)
    if guest_token:
        clauses.append("guest_token = %s")
        params.append(guest_token)
    if not clauses:
        return None
    where = " OR ".join(clauses)
    cur.execute(
        f"""
        SELECT id FROM support_tickets
        WHERE {where}
        ORDER BY updated_at DESC, id DESC
        LIMIT 1
        """,
        tuple(params),
    )
    row = cur.fetchone()
    return int(row[0]) if row else None


def fetch_thread_messages(cur: Any, ticket_id: int) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT id, from_role, body, read_at, created_at
        FROM support_messages
        WHERE ticket_id = %s
        ORDER BY created_at ASC, id ASC
        """,
        (ticket_id,),
    )
    out: list[dict[str, Any]] = []
    for mid, role, body, read_at, created_at in cur.fetchall():
        out.append(
            {
                "id": int(mid),
                "from": role,
                "body": body,
                "read": read_at is not None,
                "created_at": created_at.isoformat() if created_at else None,
            }
        )
    return out


def count_unread_owner_messages(cur: Any, ticket_id: int) -> int:
    cur.execute(
        """
        SELECT COUNT(*) FROM support_messages
        WHERE ticket_id = %s AND from_role = 'owner' AND read_at IS NULL
        """,
        (ticket_id,),
    )
    row = cur.fetchone()
    return int(row[0]) if row else 0


def mark_owner_messages_read(cur: Any, ticket_id: int) -> None:
    cur.execute(
        """
        UPDATE support_messages
        SET read_at = NOW()
        WHERE ticket_id = %s AND from_role = 'owner' AND read_at IS NULL
        """,
        (ticket_id,),
    )


def list_tickets_admin(cur: Any, *, limit: int = 30) -> list[dict[str, Any]]:
    lim = max(1, min(int(limit), 100))
    cur.execute(
        f"""
        SELECT t.id, t.user_id, t.guest_token, t.source, t.page_url, t.updated_at,
               u.tg_username, u.tg_user_id,
               (
                   SELECT body FROM support_messages m
                   WHERE m.ticket_id = t.id
                   ORDER BY m.created_at DESC, m.id DESC
                   LIMIT 1
               ) AS last_body,
               (
                   SELECT from_role FROM support_messages m
                   WHERE m.ticket_id = t.id
                   ORDER BY m.created_at DESC, m.id DESC
                   LIMIT 1
               ) AS last_role
        FROM support_tickets t
        LEFT JOIN users u ON u.id = t.user_id
        ORDER BY t.updated_at DESC
        LIMIT {lim}
        """
    )
    rows: list[dict[str, Any]] = []
    for row in cur.fetchall():
        tid, uid, guest, source, page_url, updated_at, uname, tg_uid, last_body, last_role = row
        rows.append(
            {
                "id": int(tid),
                "user_id": str(uid) if uid else None,
                "guest_token": guest,
                "source": source,
                "page_url": page_url or "",
                "updated_at": updated_at.isoformat() if updated_at else None,
                "tg_username": uname,
                "tg_user_id": int(tg_uid) if tg_uid is not None else None,
                "last_preview": preview_text(last_body or "", limit=120),
                "last_from": last_role,
            }
        )
    return rows


def create_user_ticket(
    db_url: str,
    *,
    user_id: str | None,
    guest_token: str | None,
    source: str,
    page_url: str,
    body: str,
    contact_name: str = "",
) -> dict[str, Any]:
    import psycopg

    normalized_body = normalize_body(body)
    name = (contact_name or "").strip()
    if name:
        normalized_body = f"Имя: {name}\n\n{normalized_body}"

    cfg = load_config()
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            ticket_id, is_new = get_or_create_ticket(
                cur,
                user_id=user_id,
                guest_token=guest_token,
                source=normalize_source(source),
                page_url=page_url,
            )
            append_user_message(cur, ticket_id=ticket_id, body=normalized_body)
            uname, tg_uid = (None, None)
            if user_id:
                uname, tg_uid = _user_row(cur, user_id)
            conn.commit()

    tg_ok = send_owner_support_notice(
        cfg,
        ticket_id=ticket_id,
        tg_username=uname,
        tg_user_id=tg_uid,
        user_id=user_id,
        preview=normalized_body,
        is_new_ticket=is_new,
    )
    return {
        "ok": True,
        "ticket_id": ticket_id,
        "is_new_ticket": is_new,
        "owner_notified": tg_ok,
    }


def get_user_thread(db_url: str, *, user_id: str | None, guest_token: str | None) -> dict[str, Any]:
    import psycopg

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            ticket_id = ticket_for_actor(cur, user_id=user_id, guest_token=guest_token)
            if ticket_id is None:
                return {"ticket_id": None, "messages": [], "unread": 0}
            messages = fetch_thread_messages(cur, ticket_id)
            unread = count_unread_owner_messages(cur, ticket_id)
            mark_owner_messages_read(cur, ticket_id)
            conn.commit()
    return {"ticket_id": ticket_id, "messages": messages, "unread": unread}


def get_unread_count(db_url: str, *, user_id: str | None, guest_token: str | None) -> int:
    import psycopg

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            ticket_id = ticket_for_actor(cur, user_id=user_id, guest_token=guest_token)
            if ticket_id is None:
                return 0
            return count_unread_owner_messages(cur, ticket_id)


def admin_reply(db_url: str, *, ticket_id: int, body: str) -> dict[str, Any]:
    import psycopg

    normalized = normalize_body(body)
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM support_tickets WHERE id = %s", (ticket_id,))
            if not cur.fetchone():
                raise ValueError("ticket not found")
            msg_id = append_owner_reply(cur, ticket_id=ticket_id, body=normalized)
            conn.commit()
    return {"ok": True, "ticket_id": ticket_id, "message_id": msg_id}


def admin_list_tickets(db_url: str, *, limit: int = 30) -> list[dict[str, Any]]:
    import psycopg

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            return list_tickets_admin(cur, limit=limit)
