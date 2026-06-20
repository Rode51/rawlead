"""O202: TG spam corpus — owner marks TG ads in feed for filter tuning."""

from __future__ import annotations

import logging
from typing import Any

import psycopg

logger = logging.getLogger(__name__)

_TG_SPAM_CATEGORIES = frozenset({"ad_services", "cv", "partner", "other"})


def ensure_tg_spam_corpus_table(conn: Any) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tg_spam_corpus (
                id BIGSERIAL PRIMARY KEY,
                lead_id BIGINT NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                body TEXT NOT NULL DEFAULT '',
                chat_id BIGINT,
                marked_by UUID NOT NULL,
                marked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                category TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tg_spam_corpus_marked_at
            ON tg_spam_corpus (marked_at DESC)
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tg_spam_corpus_lead_id
            ON tg_spam_corpus (lead_id)
            """
        )
    conn.commit()


def chat_id_from_tg_source(source: str) -> int | None:
    s = (source or "").strip()
    if not s.startswith("tg:"):
        return None
    rest = s[3:].strip()
    if not rest or not rest.lstrip("-").isdigit():
        return None
    try:
        return int(rest)
    except ValueError:
        return None


def _normalize_category(category: str | None) -> str | None:
    if category is None:
        return None
    cat = category.strip().lower()
    if not cat:
        return None
    if cat not in _TG_SPAM_CATEGORIES:
        raise ValueError(f"invalid category: {category}")
    return cat


def mark_tg_lead_spam(
    database_url: str,
    lead_id: int,
    marked_by: str,
    *,
    category: str | None = None,
    delist_reason: str = "owner_tg_spam",
) -> dict[str, Any]:
    """Snapshot TG lead into corpus and hide it. Raises LookupError / ValueError."""
    url = database_url.strip()
    if not url:
        raise RuntimeError("database url missing")
    lid = int(lead_id)
    if lid <= 0:
        raise ValueError("invalid lead id")
    cat = _normalize_category(category)

    with psycopg.connect(url) as conn:
        ensure_tg_spam_corpus_table(conn)
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT source, title, body, is_visible
                FROM leads
                WHERE id = %s
                """,
                (lid,),
            )
            row = cur.fetchone()
            if not row:
                raise LookupError("lead not found")
            source, title, body, is_visible = row
            src = (source or "").strip()
            if not src.lower().startswith("tg:"):
                raise ValueError("not a TG lead")
            if not is_visible:
                raise LookupError("lead not found or already hidden")

            chat_id = chat_id_from_tg_source(src)
            cur.execute(
                """
                INSERT INTO tg_spam_corpus (
                    lead_id, source, title, body, chat_id, marked_by, category
                )
                VALUES (%s, %s, %s, %s, %s, %s::uuid, %s)
                """,
                (lid, src, title or "", body or "", chat_id, marked_by, cat),
            )
            cur.execute(
                """
                UPDATE leads
                SET is_visible = FALSE,
                    delist_reason = %s
                WHERE id = %s AND is_visible = TRUE
                """,
                (delist_reason, lid),
            )
            if cur.rowcount != 1:
                raise LookupError("lead not found or already hidden")
        conn.commit()

    logger.info("tg_spam_corpus: marked lead_id=%s source=%s by=%s", lid, src, marked_by)
    return {"ok": True, "lead_id": lid}


def fetch_corpus_summary(database_url: str, *, limit: int = 20) -> dict[str, Any]:
    url = database_url.strip()
    if not url:
        return {"count": 0, "recent": []}
    lim = max(1, min(int(limit), 100))
    with psycopg.connect(url) as conn:
        ensure_tg_spam_corpus_table(conn)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*)::int FROM tg_spam_corpus")
            count_row = cur.fetchone()
            total = int(count_row[0]) if count_row else 0
            cur.execute(
                """
                SELECT lead_id, source, title, chat_id, category, marked_at
                FROM tg_spam_corpus
                ORDER BY marked_at DESC
                LIMIT %s
                """,
                (lim,),
            )
            recent = [
                {
                    "lead_id": int(r[0]),
                    "source": r[1] or "",
                    "title": (r[2] or "")[:120],
                    "chat_id": int(r[3]) if r[3] is not None else None,
                    "category": r[4],
                    "marked_at": r[5].isoformat() if r[5] is not None else None,
                }
                for r in cur.fetchall()
            ]
    return {"count": total, "recent": recent}
