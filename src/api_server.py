"""RawLead HTTP API — фазы 3c (feed) + 3e (me/cabinet) + 3g (бот-only, навыки).

Запуск:
    uvicorn src.api_server:app --host 0.0.0.0 --port 18766 --reload

Переменные окружения (.env):
    DATABASE_URL      — Neon Postgres connection string
    RAWLEAD_API_KEY   — ключ для /v1/internal/* (радар / бот)
    RANK_WEIGHT_AI    — вес ai_score в итоговом rank (default 0.6)
    RANK_WEIGHT_TAGS  — вес keyword_match в итоговом rank (default 0.4)
"""

from __future__ import annotations

import json
import hashlib
import logging
import os
import secrets
import threading
import time
from contextlib import contextmanager
from urllib.parse import parse_qs
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID, uuid4

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request

try:
    from psycopg_pool import ConnectionPool
except ImportError:
    ConnectionPool = None  # type: ignore[misc, assignment]
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from pydantic import BaseModel, ConfigDict
from src.config import load_config, load_radar_env

from src.lead_category import (
    category_for_listing,
    effective_feed_min_score,
    normalize_category,
    parse_category_param,
    passes_score_filter,
    resolve_lead_category,
)
from src.skills_catalog import (
    _USER_MAX_TAGS,
    build_catalog_groups,
    build_dynamic_catalog_groups,
    lead_tags_for_feed,
    normalize_user_tags,
    user_tags_input_count,
)
from src.public_feed import (
    feed_source_filter_sql,
    feed_visibility_where_sql,
    inbox_replies_where_sql,
    is_public_feed_source,
    parse_feed_source_param,
    public_feed_source_sql,
)
from src.jwt_auth import decode_access_token, issue_access_token
from src.telegram_login import login_bot_token, verify_telegram_login
from src.feed_social import display_replies, display_views
from src.rank import (
    final_rank,
    keyword_match,
    normalize_tags,
    open_rank,
    parse_lead_tags,
    tags_as_weights,
)
from src.ai_analyze import draft_stats_24h, ai_last_error, draft_fail_per_hour
from src.stars_billing import stars_available
from src.draft_async import draft_response_body, poll_draft, submit_draft, submit_warm
from src.draft_limits import draft_rate_limit_detail
from src.bot_auth import (
    BOT_AUTH_PREFIX,
    BOT_SESSION_TTL_SEC,
    authorize_bot_auth_session,
    cabinet_return_url as _cabinet_return_url,
    create_bot_session,
    hash_bot_auth_token as _hash_bot_auth_token,
    merge_chat_id_on_login_standalone,
    mint_bot_first_login_url,
)
from src.match_push import (
    DraftError,
    draft_rate_limit_retry_after,
    merge_chat_id_on_login,
)
from src.reply_draft_strip import strip_reply_draft_price_deadline
from src.tools_catalog import normalize_tools_required, vendor_lock_tools
from src.owner_admin import (
    fetch_dashboard,
    hide_lead,
    is_owner_db_user,
    ops_html,
    ops_login_html,
    record_pageview,
    run_ops_control,
)
from src.ops_log_stream import iter_radar_log_sse
from src.support_tickets import (
    admin_list_tickets,
    admin_reply,
    create_user_ticket,
    get_unread_count,
    get_user_thread,
    normalize_guest_token,
)
from src.trial_subscription import (
    TrialStartError,
    expire_stale_trials,
    fetch_subscription_row,
    notify_trial_started,
    resolve_subscription_status,
    start_trial,
    subscription_extra_fields,
)

# /cabinet/ login and /v1/me/* are site-product endpoints.
# Force site profile to avoid accidental legacy token verification
# when uvicorn inherits RADAR_PROFILE=legacy from another shell.
os.environ["RADAR_PROFILE"] = "site"
load_radar_env()

logger = logging.getLogger(__name__)

_VERSION = "0.4"
_OWNER_USER_ID = "00000000-0000-0000-0000-000000000001"
_ME_FEED_SCAN_LIMIT = 500
_SKILLS_CATALOG_LIMIT = 50
_SKILLS_CATALOG_DAYS = 30
_FEED_DELAY_MINUTES = 15
_HOT_MAX_AGE_SEC = 300
_DRAFT_RETRY_AFTER_SEC = 5
_FEED_PREFS_SORT = frozenset({"time", "match"})
_FEED_PREFS_MIN_MATCH = frozenset({0, 50, 60, 70, 80, 90})


def _lead_is_hot(created_at: Any) -> bool:
    if not isinstance(created_at, datetime):
        return False
    now = datetime.now(timezone.utc)
    dt = created_at
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    age = (now - dt).total_seconds()
    return 0 <= age < _HOT_MAX_AGE_SEC


def _feed_base_where_sql(*, alias: str = "") -> tuple[str, list[Any]]:
    prefix = f"{alias}." if alias else ""
    src_sql, src_params = public_feed_source_sql()
    if prefix:
        src_sql = src_sql.replace(" AND source", f" AND {prefix}source", 1)
    return f"{prefix}is_visible = TRUE" + src_sql, src_params


def _feed_where_with_sources(
    *,
    alias: str = "",
    apply_delay: bool = False,
    source_keys: list[str] | None = None,
) -> tuple[str, list[Any]]:
    feed_where, feed_params = _feed_where_sql(alias=alias, apply_delay=apply_delay)
    src_sql, src_params = feed_source_filter_sql(source_keys or [], alias=alias)
    return feed_where + src_sql, feed_params + src_params


def _feed_where_sql(*, alias: str = "", apply_delay: bool = False) -> tuple[str, list[Any]]:
    delay = _FEED_DELAY_MINUTES if apply_delay else None
    return feed_visibility_where_sql(
        alias=alias,
        apply_delay_minutes=delay,
        delay_minutes=_FEED_DELAY_MINUTES,
    )


# ─── helpers ─────────────────────────────────────────────────────────────────


def _db_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return url


def _db_connection_mode() -> str:
    """O131: pooler vs direct — for startup log only (no secrets)."""
    url = os.getenv("DATABASE_URL", "").strip().lower()
    if not url:
        return "unset"
    if "pooler" in url or ":6543" in url:
        return "pooler"
    return "direct"


_DB_POOL: Any = None


@contextmanager
def _db_conn():
    """O168: reuse TCP sessions on hot read paths (load@50)."""
    if _DB_POOL is not None:
        with _DB_POOL.connection() as conn:
            yield conn
    else:
        with psycopg.connect(_db_url()) as conn:
            yield conn


def _bot_login_username() -> str:
    raw = os.environ.get("TELEGRAM_BOT_USERNAME", "rawlead_bot").strip().lstrip("@")
    return raw or "rawlead_bot"


def _api_key() -> str:
    return os.getenv("RAWLEAD_API_KEY", "").strip()


def _row_to_item(
    row: tuple[Any, ...],
    *,
    keyword_match_val: int | None = None,
    final_rank_val: int | None = None,
    feed_delayed: bool = False,
) -> dict[str, Any]:
    (
        lead_id,
        source,
        title,
        body,
        url,
        budget_text,
        ai_score,
        ai_verdict,
        lead_tags,
        ai_reasons,
        created_at,
        stored_category,
        task_summary,
        tools_required,
        reply_draft,
    ) = row
    from ai_reasons import (
        difficulty_from_ai_reasons,
        parse_ai_reasons_raw,
        parse_tz_attachment_from_raw,
    )

    tags, tag_labels = lead_tags_for_feed(lead_tags)
    reasons_list, _ = parse_ai_reasons_raw(ai_reasons)
    difficulty = difficulty_from_ai_reasons(ai_reasons)
    tz_attachment = parse_tz_attachment_from_raw(ai_reasons)
    km = keyword_match_val
    fr = final_rank_val
    if fr is None:
        fr = open_rank(ai_score)
    category = resolve_lead_category(stored_category, title or "", body or "", tags)
    tools: list[str] = []
    if isinstance(tools_required, list):
        tools = list(normalize_tools_required(tools_required))
    rd = strip_reply_draft_price_deadline((reply_draft or "").strip())
    dv = display_views(lead_id, created_at, feed_delayed=feed_delayed)
    return {
        "id": lead_id,
        "source": source,
        "title": title,
        "body": body or "",
        "task_summary": (task_summary or "").strip(),
        "url": url,
        "budget_text": budget_text,
        "ai_score": ai_score,
        "ai_verdict": ai_verdict,
        "lead_tags": tags,
        "lead_tag_labels": tag_labels,
        "ai_reasons": reasons_list,
        "difficulty": difficulty,
        "final_rank": fr,
        "keyword_match": km,
        "category": category,
        "created_at": created_at.isoformat() if created_at else None,
        "is_hot": _lead_is_hot(created_at),
        "tools_required": tools,
        "reply_draft": rd,
        "tz_attachment": tz_attachment,
        "display_views": dv,
        "display_replies": display_replies(lead_id, dv),
    }


def _strip_shared_reply_drafts(items: list[dict[str, Any]]) -> None:
    """O60a: never expose shared leads.reply_draft in public feed JSON."""
    for it in items:
        it["reply_draft"] = ""


def _attach_personal_replies(cur: Any, user_id: str, items: list[dict[str, Any]]) -> None:
    """O60a: badge/draft only from user_lead_replies for this user."""
    ids = [int(it["id"]) for it in items if it.get("id") is not None]
    if not ids:
        return
    cur.execute(
        """
        SELECT lead_id, reply_draft
        FROM user_lead_replies
        WHERE user_id = %s::uuid
          AND lead_id = ANY(%s)
          AND deleted_at IS NULL
        """,
        (user_id, ids),
    )
    by_lead = {
        int(row[0]): strip_reply_draft_price_deadline((row[1] or "").strip())
        for row in cur.fetchall()
    }
    for it in items:
        lid = int(it["id"])
        it["reply_draft"] = by_lead.get(lid, "")


def _strip_tools_for_anon(items: list[dict[str, Any]]) -> None:
    """O83: anon /v1/feed must not expose L2 tools_required."""
    for it in items:
        it["tools_required"] = []


def _finalize_feed_items(
    cur: Any,
    items: list[dict[str, Any]],
    *,
    user_id: str | None,
) -> None:
    _strip_shared_reply_drafts(items)
    if user_id:
        _attach_personal_replies(cur, user_id, items)
    else:
        _strip_tools_for_anon(items)


_SELECT_COLS = """
    id, source, title, body, url, budget_text,
    ai_score, ai_verdict, lead_tags, ai_reasons, created_at, category,
    task_summary, tools_required, reply_draft
"""

_INBOX_SELECT_COLS = """
    l.id, l.source, l.title, l.body, l.url, l.budget_text,
    l.ai_score, l.ai_verdict, l.lead_tags, l.ai_reasons, l.created_at, l.category,
    l.task_summary, l.tools_required, ulr.reply_draft
"""


def _category_sql(categories: list[str]) -> tuple[str, list[Any]]:
    """Legacy SQL filter — O126: category фильтруется по resolve_lead_category в Python."""
    return "", []


def _row_resolved_category(row: tuple[Any, ...]) -> str:
    tags = _canonical_lead_tags(row[8])
    return resolve_lead_category(row[11], row[2] or "", row[3] or "", tags)


def _passes_category_filter(row: tuple[Any, ...], categories: list[str]) -> bool:
    if not categories:
        return True
    return _row_resolved_category(row) in categories


def _load_user_tags(cur: Any, user_id: str) -> dict[str, float]:
    cur.execute(
        "SELECT tag FROM user_tags WHERE user_id = %s::uuid ORDER BY tag",
        (user_id,),
    )
    tags = normalize_user_tags([row[0] for row in cur.fetchall()])
    return {tag: 1.0 for tag in tags}


def _rewrite_user_tags(cur: Any, user_id: str, tags: list[str]) -> None:
    cur.execute(
        "DELETE FROM user_tags WHERE user_id = %s::uuid",
        (user_id,),
    )
    for tag in tags:
        cur.execute(
            """
            INSERT INTO user_tags (user_id, tag, weight)
            VALUES (%s::uuid, %s, 1.0)
            ON CONFLICT (user_id, tag) DO UPDATE SET weight = 1.0
            """,
            (user_id, tag),
        )


def _parse_skills_param(skills: str) -> list[str]:
    if not skills.strip():
        return []
    return normalize_tags(skills.split(","))


def _skills_sql(skills: list[str]) -> tuple[str, list[Any]]:
    if not skills:
        return "", []
    return (
        " AND EXISTS ("
        " SELECT 1 FROM jsonb_array_elements_text(COALESCE(lead_tags, '[]'::jsonb)) AS _lt(tag)"
        " WHERE _lt.tag = ANY(%s::text[])"
        ")",
        [skills],
    )


def _feed_scan_limit(
    *,
    limit: int,
    offset: int,
    categories: list[str],
    skills: list[str],
    sort: str,
    rank_filter: bool = False,
) -> int:
    """O131: wide scan when post-SQL ranking/filter needs a window."""
    if categories:
        return _ME_FEED_SCAN_LIMIT
    if sort == "match" or rank_filter:
        return _ME_FEED_SCAN_LIMIT
    return limit + offset + 20


def _feed_today_subquery_sql(
    *,
    skills: list[str],
    apply_delay: bool,
) -> tuple[str, tuple[Any, ...]]:
    feed_where, feed_params = _feed_where_sql(apply_delay=apply_delay)
    skills_sql, skills_params = _skills_sql(skills)
    today_sql = (
        " AND (created_at AT TIME ZONE 'Europe/Moscow')::date"
        " = (NOW() AT TIME ZONE 'Europe/Moscow')::date"
    )
    subquery = f"""(
        SELECT COUNT(*)::int
        FROM leads
        WHERE {feed_where}
          {skills_sql}
          {today_sql}
    )"""
    return subquery, tuple(feed_params) + tuple(skills_params)


def _feed_today_count_standalone(
    cur: Any,
    *,
    skills: list[str],
    apply_delay: bool,
) -> int:
    subquery, params = _feed_today_subquery_sql(skills=skills, apply_delay=apply_delay)
    cur.execute(f"SELECT {subquery}", params)
    row = cur.fetchone()
    return int(row[0] or 0) if row else 0


def _canonical_lead_tags(raw: Any) -> list[str]:
    slugs, _ = lead_tags_for_feed(raw)
    return slugs


def _passes_min_match(km: int, min_match: int) -> bool:
    """Personal feed: hide keyword_match=0; min_match=0 → any overlap > 0."""
    if km <= 0:
        return False
    if min_match > 0:
        return km >= min_match
    return True


def _rank_feed_rows(
    rows: list[tuple[Any, ...]],
    tag_weights: dict[str, float],
    *,
    min_score: int,
    sort: str,
    min_match: int | None = None,
    feed_delayed: bool = False,
    categories: list[str] | None = None,
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    cat_filter = categories or []
    for row in rows:
        if cat_filter and not _passes_category_filter(row, cat_filter):
            continue
        tags = _canonical_lead_tags(row[8])
        category = resolve_lead_category(row[11], row[2] or "", row[3] or "", tags)
        km = keyword_match(tags, tag_weights) if tag_weights else 0
        fr = final_rank(row[6], km)
        if min_match is not None:
            if not _passes_min_match(km, min_match):
                continue
        else:
            score_for_filter = fr if sort == "match" else (row[6] or 0)
            if not passes_score_filter(int(score_for_filter), min_score, category):
                continue
        ranked.append(
            _row_to_item(
                row,
                keyword_match_val=km,
                final_rank_val=fr,
                feed_delayed=feed_delayed,
            )
        )
    if sort == "match":
        ranked.sort(
            key=lambda x: (x["final_rank"], x.get("created_at") or ""),
            reverse=True,
        )
    return ranked


_FEED_TODAY_COUNT_CACHE: dict[tuple[Any, ...], tuple[float, int]] = {}
_FEED_TODAY_COUNT_TTL_SEC = 180.0
_FEED_TODAY_COUNT_LOCK = threading.Lock()
_SKILLS_CATALOG_CACHE: dict[tuple[Any, ...], tuple[float, dict[str, Any]]] = {}
_SKILLS_CATALOG_TTL_SEC = 120.0
_SKILLS_CATALOG_LOCK = threading.Lock()


def _feed_today_count(
    cur: Any,
    *,
    skills: list[str],
    categories: list[str],
    apply_delay: bool = False,
) -> int:
    """Leads created today (Europe/Moscow) with same visibility/category/skills/delay as feed."""
    feed_where, feed_params = _feed_where_sql(apply_delay=apply_delay)
    skills_sql, skills_params = _skills_sql(skills)
    today_sql = (
        " AND (created_at AT TIME ZONE 'Europe/Moscow')::date"
        " = (NOW() AT TIME ZONE 'Europe/Moscow')::date"
    )
    if not categories:
        cur.execute(
            f"""
            SELECT COUNT(*)::int
            FROM leads
            WHERE {feed_where}
              {skills_sql}
              {today_sql}
            """,
            (*feed_params, *skills_params),
        )
        row = cur.fetchone()
        return int(row[0] or 0) if row else 0

    cur.execute(
        f"""
        SELECT title, body, lead_tags, category
        FROM leads
        WHERE {feed_where}
          {skills_sql}
          {today_sql}
        """,
        (*feed_params, *skills_params),
    )
    count = 0
    for title, body, lead_tags, stored_category in cur.fetchall():
        tags = _canonical_lead_tags(lead_tags)
        resolved = resolve_lead_category(stored_category, title or "", body or "", tags)
        if resolved in categories:
            count += 1
    return count


def _feed_today_count_cached(
    cur: Any,
    *,
    skills: list[str],
    categories: list[str],
    apply_delay: bool = False,
) -> int:
    """O168: TTL cache — load@50 hammers today_count on every /v1/feed."""
    key = (tuple(skills), tuple(categories), apply_delay)
    now = time.monotonic()
    hit = _FEED_TODAY_COUNT_CACHE.get(key)
    if hit and now - hit[0] < _FEED_TODAY_COUNT_TTL_SEC:
        return hit[1]
    with _FEED_TODAY_COUNT_LOCK:
        hit = _FEED_TODAY_COUNT_CACHE.get(key)
        if hit and now - hit[0] < _FEED_TODAY_COUNT_TTL_SEC:
            return hit[1]
        val = _feed_today_count(
            cur, skills=skills, categories=categories, apply_delay=apply_delay
        )
        _FEED_TODAY_COUNT_CACHE[key] = (now, val)
        return val


def _feed_today_count_standalone_cached(
    cur: Any,
    *,
    skills: list[str],
    apply_delay: bool,
) -> int:
    key = ("standalone", tuple(skills), apply_delay)
    now = time.monotonic()
    hit = _FEED_TODAY_COUNT_CACHE.get(key)
    if hit and now - hit[0] < _FEED_TODAY_COUNT_TTL_SEC:
        return hit[1]
    with _FEED_TODAY_COUNT_LOCK:
        hit = _FEED_TODAY_COUNT_CACHE.get(key)
        if hit and now - hit[0] < _FEED_TODAY_COUNT_TTL_SEC:
            return hit[1]
        val = _feed_today_count_standalone(cur, skills=skills, apply_delay=apply_delay)
        _FEED_TODAY_COUNT_CACHE[key] = (now, val)
        return val


def _feed_score_sql(min_score: int) -> tuple[str, list[Any]]:
    if min_score <= 0:
        return "", []
    sql_min = min_score
    if min_score >= 70:
        sql_min = effective_feed_min_score(min_score, "text")
    return " AND (ai_score IS NULL OR ai_score >= %s)", [sql_min]


def _feed_page_time(
    cur: Any,
    *,
    limit: int,
    offset: int,
    min_score: int,
    skills: list[str],
    categories: list[str],
    tag_weights: dict[str, float],
    apply_delay: bool = False,
    user_id: str | None = None,
    min_match: int | None = None,
    source_keys: list[str] | None = None,
) -> tuple[list[dict[str, Any]], int, int | None]:
    cat_sql, cat_params = _category_sql(categories)
    score_sql, score_params = _feed_score_sql(min_score)
    feed_where, feed_params = _feed_where_with_sources(
        apply_delay=apply_delay,
        source_keys=source_keys,
    )
    if min_match and tag_weights:
        scan_limit = _feed_scan_limit(
            limit=limit,
            offset=offset,
            categories=categories,
            skills=skills,
            sort="time",
            rank_filter=True,
        )
        today_sub, today_params = _feed_today_subquery_sql(
            skills=skills, apply_delay=apply_delay
        )
        today_select = f", {today_sub} AS _today_count" if not categories else ""
        cur.execute(
            f"""
            SELECT {_SELECT_COLS}{today_select}
            FROM leads
            WHERE {feed_where}
              {score_sql}{cat_sql}
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (
                *((today_params) if not categories else ()),
                *feed_params,
                *score_params,
                *cat_params,
                scan_limit,
            ),
        )
        rows = cur.fetchall()
        today_count: int | None = None
        if not categories:
            if rows:
                today_count = int(rows[0][-1] or 0)
                rows = [r[:-1] for r in rows]
            else:
                today_count = _feed_today_count_standalone_cached(
                    cur, skills=skills, apply_delay=apply_delay
                )
        ranked = _rank_feed_rows(
            rows,
            tag_weights,
            min_score=min_score,
            sort="time",
            min_match=min_match,
            feed_delayed=apply_delay,
            categories=categories,
        ),
        ranked.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        page = ranked[offset : offset + limit]
        _finalize_feed_items(cur, page, user_id=user_id)
        return page, len(page), today_count

    if categories:
        scan_limit = _feed_scan_limit(
            limit=limit,
            offset=offset,
            categories=categories,
            skills=skills,
            sort="time",
            rank_filter=True,
        )
        today_sub, today_params = _feed_today_subquery_sql(
            skills=skills, apply_delay=apply_delay
        )
        today_select = f", {today_sub} AS _today_count" if not categories else ""
        cur.execute(
            f"""
            SELECT {_SELECT_COLS}{today_select}
            FROM leads
            WHERE {feed_where}
              {score_sql}{cat_sql}
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (
                *((today_params) if not categories else ()),
                *feed_params,
                *score_params,
                *cat_params,
                scan_limit,
            ),
        )
        rows = cur.fetchall()
        today_count = None
    else:
        cur.execute(
            f"""
            SELECT {_SELECT_COLS}
            FROM leads
            WHERE {feed_where}
              {score_sql}{cat_sql}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (
                *feed_params,
                *score_params,
                *cat_params,
                limit,
                offset,
            ),
        )
        rows = cur.fetchall()
        today_count = _feed_today_count_cached(
            cur, skills=skills, categories=categories, apply_delay=apply_delay
        )

    if categories:
        pass
    items: list[dict[str, Any]] = []
    for r in rows:
        if categories and not _passes_category_filter(r, categories):
            continue
        tags = _canonical_lead_tags(r[8])
        category = resolve_lead_category(r[11], r[2] or "", r[3] or "", tags)
        km = keyword_match(tags, tag_weights) if tag_weights else 0
        fr = final_rank(r[6], km)
        score_for_filter = r[6] or 0
        if not passes_score_filter(int(score_for_filter), min_score, category):
            continue
        items.append(
            _row_to_item(
                r,
                keyword_match_val=km,
                final_rank_val=fr,
                feed_delayed=apply_delay,
            )
        )
    if categories:
        page = items[offset : offset + limit]
    else:
        page = items
    _finalize_feed_items(cur, page, user_id=user_id)
    return page, len(page), today_count


def _feed_page_match(
    cur: Any,
    *,
    limit: int,
    offset: int,
    min_score: int,
    skills: list[str],
    categories: list[str],
    tag_weights: dict[str, float],
    apply_delay: bool = False,
    user_id: str | None = None,
    min_match: int | None = None,
    source_keys: list[str] | None = None,
) -> tuple[list[dict[str, Any]], int, int | None]:
    cat_sql, cat_params = _category_sql(categories)
    feed_where, feed_params = _feed_where_with_sources(
        apply_delay=apply_delay,
        source_keys=source_keys,
    )
    scan_limit = _feed_scan_limit(
        limit=limit,
        offset=offset,
        categories=categories,
        skills=skills,
        sort="match",
    )
    today_sub, today_params = _feed_today_subquery_sql(
        skills=skills, apply_delay=apply_delay
    )
    today_select = f", {today_sub} AS _today_count" if not categories else ""
    cur.execute(
        f"""
        SELECT {_SELECT_COLS}{today_select}
        FROM leads
        WHERE {feed_where}
          {cat_sql}
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (
            *((today_params) if not categories else ()),
            *feed_params,
            *cat_params,
            scan_limit,
        ),
    )
    raw_rows = cur.fetchall()
    today_count: int | None = None
    if not categories:
        if raw_rows:
            today_count = int(raw_rows[0][-1] or 0)
            raw_rows = [r[:-1] for r in raw_rows]
        else:
            today_count = _feed_today_count_standalone_cached(
                cur, skills=skills, apply_delay=apply_delay
            )
    ranked = _rank_feed_rows(
        raw_rows,
        tag_weights,
        min_score=min_score,
        sort="match",
        min_match=min_match,
        feed_delayed=apply_delay,
        categories=categories,
    )
    page = ranked[offset : offset + limit]
    _finalize_feed_items(cur, page, user_id=user_id)
    return page, len(page), today_count


def _personal_feed_page(
    cur: Any,
    user_id: str,
    *,
    limit: int,
    offset: int,
    min_score: int,
    min_match: int,
    skills: list[str],
    categories: list[str],
    sort: str,
    source_keys: list[str] | None = None,
) -> tuple[list[dict[str, Any]], int, int | None]:
    user_tags = _load_user_tags(cur, user_id)
    has_profile = bool(user_tags)
    if not has_profile:
        sort = "time"
    extra, extra_params = _skills_sql(skills)
    cat_sql, cat_params = _category_sql(categories)
    feed_where, feed_params = _feed_where_with_sources(source_keys=source_keys)
    today_sub, today_params = _feed_today_subquery_sql(skills=skills, apply_delay=False)
    today_select = f", {today_sub} AS _today_count" if not categories else ""

    if sort == "time":
        if categories:
            scan_limit = _feed_scan_limit(
                limit=limit,
                offset=offset,
                categories=categories,
                skills=skills,
                sort="time",
                rank_filter=True,
            )
            cur.execute(
                f"""
                SELECT {_SELECT_COLS}{today_select}
                FROM leads
                WHERE {feed_where}
                  {extra}{cat_sql}
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (
                    *feed_params,
                    *extra_params,
                    *cat_params,
                    scan_limit,
                ),
            )
            raw_rows = cur.fetchall()
            today_count = None
        else:
            cur.execute(
                f"""
                SELECT {_SELECT_COLS}{today_select}
                FROM leads
                WHERE {feed_where}
                  {extra}{cat_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (
                    *today_params,
                    *feed_params,
                    *extra_params,
                    *cat_params,
                    limit,
                    offset,
                ),
            )
            raw_rows = cur.fetchall()
            today_count = None
            if raw_rows:
                today_count = int(raw_rows[0][-1] or 0)
                raw_rows = [r[:-1] for r in raw_rows]
            else:
                today_count = _feed_today_count_standalone_cached(
                    cur, skills=skills, apply_delay=False
                )
        ranked: list[dict[str, Any]] = []
        for row in raw_rows:
            if categories and not _passes_category_filter(row, categories):
                continue
            tags = _canonical_lead_tags(row[8])
            km = keyword_match(tags, user_tags) if has_profile else 0
            fr = final_rank(row[6], km)
            ranked.append(
                _row_to_item(row, keyword_match_val=km, final_rank_val=fr, feed_delayed=False)
            )
        page = ranked[offset : offset + limit] if categories else ranked
    else:
        scan_limit = _feed_scan_limit(
            limit=limit,
            offset=offset,
            categories=categories,
            skills=skills,
            sort="match",
            rank_filter=True,
        )
        cur.execute(
            f"""
            SELECT {_SELECT_COLS}{today_select}
            FROM leads
            WHERE {feed_where}
              {extra}{cat_sql}
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (
                *((today_params) if not categories else ()),
                *feed_params,
                *extra_params,
                *cat_params,
                scan_limit,
            ),
        )
        raw_rows = cur.fetchall()
        today_count = None
        if not categories:
            if raw_rows:
                today_count = int(raw_rows[0][-1] or 0)
                raw_rows = [r[:-1] for r in raw_rows]
            else:
                today_count = _feed_today_count_standalone_cached(
                    cur, skills=skills, apply_delay=False
                )
        ranked = _rank_feed_rows(
            raw_rows,
            user_tags,
            min_score=min_score,
            sort="match",
            min_match=min_match,
            feed_delayed=False,
            categories=categories,
        )
        page = ranked[offset : offset + limit]
    _finalize_feed_items(cur, page, user_id=user_id)
    return page, len(page), today_count


def _require_api_key(x_api_key: str = Header(default="")) -> None:
    key = _api_key()
    if not key or x_api_key != key:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _upsert_telegram_user(
    cur: Any,
    *,
    tg_user_id: int,
    username: str | None,
    first_name: str | None,
    photo_url: str | None,
) -> str:
    cur.execute(
        "SELECT id FROM users WHERE tg_user_id = %s",
        (tg_user_id,),
    )
    row = cur.fetchone()
    if row:
        user_id = str(row[0])
        cur.execute(
            """
            UPDATE users
            SET tg_username = %s, tg_first_name = %s, tg_photo_url = %s
            WHERE id = %s::uuid
            """,
            (username, first_name, photo_url, user_id),
        )
        _grant_owner_beta_if_match(cur, user_id, tg_user_id)
        return user_id

    user_id = str(uuid4())
    cur.execute(
        """
        INSERT INTO users (id, tg_user_id, tg_username, tg_first_name, tg_photo_url)
        VALUES (%s::uuid, %s, %s, %s, %s)
        """,
        (user_id, tg_user_id, username, first_name, photo_url),
    )
    cur.execute(
        """
        INSERT INTO subscriptions (user_id, plan, is_active)
        VALUES (%s::uuid, 'free', FALSE)
        ON CONFLICT (user_id) DO NOTHING
        """,
        (user_id,),
    )
    _grant_owner_beta_if_match(cur, user_id, tg_user_id)
    return user_id


def _owner_telegram_id() -> int | None:
    raw = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if raw.isdigit():
        return int(raw)
    return None


def _grant_owner_beta_if_match(cur: Any, user_id: str, tg_user_id: int) -> None:
    """OWNER-BETA-GRANT: владелец (TELEGRAM_CHAT_ID) → plan=owner, is_active."""
    owner_id = _owner_telegram_id()
    if owner_id is None or tg_user_id != owner_id:
        return
    cur.execute(
        """
        UPDATE subscriptions
        SET plan = 'owner', is_active = TRUE
        WHERE user_id = %s::uuid
        """,
        (user_id,),
    )


def _resolve_bearer_user_id(
    authorization: str = Header(default="", alias="Authorization"),
) -> str:
    """Только Bearer JWT — без fallback на MVP owner header."""
    auth = (authorization or "").strip()
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = auth[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        data = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Unauthorized") from exc
    return str(data["sub"])


def _resolve_user_id(
    authorization: str = Header(default="", alias="Authorization"),
    x_rawlead_user_id: str = Header(default="", alias="X-RawLead-User-Id"),
) -> str:
    """Bearer JWT (кабинет) или заголовок owner (#1) для dogfood."""
    auth = (authorization or "").strip()
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized")
        try:
            data = decode_access_token(token)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail="Unauthorized") from exc
        return str(data["sub"])

    uid = (x_rawlead_user_id or "").strip() or _OWNER_USER_ID
    try:
        UUID(uid)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="invalid user id") from exc
    if uid != _OWNER_USER_ID:
        raise HTTPException(status_code=403, detail="use telegram login")
    return uid


def _try_user_from_bearer(authorization: str) -> str | None:
    auth = (authorization or "").strip()
    if not auth.lower().startswith("bearer "):
        return None
    token = auth[7:].strip()
    if not token:
        return None
    try:
        data = decode_access_token(token)
        return str(data["sub"])
    except ValueError:
        return None


def _user_effective_access(cur: Any, user_id: str) -> bool:
    plan, is_active, active_until, paused_until, trial_used_at = _ensure_subscription(
        cur, user_id
    )
    payload = _subscription_payload(
        plan, is_active, active_until, paused_until, trial_used_at
    )
    return bool(payload["effective_access"])


class TelegramAuthPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    first_name: str = ""
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


# ─── app ──────────────────────────────────────────────────────────────────────

app = FastAPI(title="RawLead API", version=_VERSION, docs_url="/docs")


def _cors_origins() -> list[str]:
    raw = os.environ.get("RADAR_CORS_ORIGINS", "").strip()
    if not raw:
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


_cors = _cors_origins()
if _cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
def _log_db_connection_mode() -> None:
    # uvicorn leaves root at WARNING — app logger.info (draft:trace) never reached journal.
    logging.getLogger().setLevel(logging.INFO)
    for name in ("match_push", "draft_async", "draft_trace", "ai_analyze", "config"):
        logging.getLogger(name).setLevel(logging.INFO)

    from config import openrouter_proxy_hint

    global _DB_POOL
    logger.info("db: %s", _db_connection_mode())
    if ConnectionPool is not None:
        _DB_POOL = ConnectionPool(
            _db_url(),
            min_size=4,
            max_size=40,
            timeout=10.0,
            max_waiting=80,
            open=True,
        )
        logger.info("db: app_pool min=4 max=40")
        try:
            with _db_conn() as conn:
                with conn.cursor() as cur:
                    _feed_today_count_cached(
                        cur,
                        skills=[],
                        categories=[],
                        apply_delay=True,
                    )
            _skills_catalog_popular_cached(
                category_list=[],
                days=_SKILLS_CATALOG_DAYS,
                limit=_SKILLS_CATALOG_LIMIT,
            )
            logger.info("db: feed/catalog cache warmed")
        except Exception as exc:
            logger.warning("db: cache warm failed: %s", exc)
    logger.info("openrouter:proxy=%s", openrouter_proxy_hint())


@app.on_event("shutdown")
def _close_db_pool() -> None:
    global _DB_POOL
    if _DB_POOL is not None:
        _DB_POOL.close()
        _DB_POOL = None


@app.post("/v1/auth/telegram")
def auth_telegram(payload: TelegramAuthPayload) -> dict[str, Any]:
    """Login Widget → JWT 7d, upsert users по tg_user_id."""
    check_data: dict[str, Any] = {
        "id": payload.id,
        "auth_date": payload.auth_date,
    }
    if payload.first_name:
        check_data["first_name"] = payload.first_name
    if payload.last_name:
        check_data["last_name"] = payload.last_name
    if payload.username:
        check_data["username"] = payload.username
    if payload.photo_url:
        check_data["photo_url"] = payload.photo_url
    check_data["hash"] = payload.hash

    try:
        verify_telegram_login(check_data, bot_token=login_bot_token())
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    username = (payload.username or "").strip() or None
    first_name = (payload.first_name or "").strip() or None
    photo_url = (payload.photo_url or "").strip() or None

    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                user_id = _upsert_telegram_user(
                    cur,
                    tg_user_id=int(payload.id),
                    username=username,
                    first_name=first_name,
                    photo_url=photo_url,
                )
                _grant_owner_beta_if_match(cur, user_id, int(payload.id))
                merge_chat_id_on_login(cur, tg_user_id=int(payload.id))
            conn.commit()
    except Exception as exc:
        logger.error("auth_telegram: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc

    token = issue_access_token(user_id, tg_user_id=int(payload.id))
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id,
        "tg_user_id": int(payload.id),
        "username": username,
        "first_name": first_name,
        "photo_url": photo_url,
    }


@app.post("/v1/auth/bot-session")
def auth_bot_session() -> dict[str, Any]:
    """Deep-link login step 1: mint one-time token (TTL 5 min)."""
    try:
        plain, deep_link, expires = create_bot_session()
    except Exception as exc:
        logger.error("auth_bot_session: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc
    return {
        "auth_token": plain,
        "deep_link": deep_link,
        "expires_at": expires.isoformat(),
    }


class BotCompletePayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    auth_token: str = ""


def _complete_bot_auth(auth_token: str) -> dict[str, Any]:
    token = (auth_token or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="auth_token required")
    token_hash = _hash_bot_auth_token(token)
    now = datetime.now(timezone.utc)
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT expires_at, tg_user_id, tg_username, tg_first_name,
                           tg_photo_url, authorized_at, consumed_at
                    FROM auth_bot_sessions
                    WHERE token_hash = %s
                    FOR UPDATE
                    """,
                    (token_hash,),
                )
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="session not found")
                (
                    expires_at,
                    tg_user_id,
                    tg_username,
                    tg_first_name,
                    tg_photo_url,
                    authorized_at,
                    consumed_at,
                ) = row
                if consumed_at is not None:
                    raise HTTPException(status_code=410, detail="session consumed")
                exp = expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if exp <= now:
                    raise HTTPException(status_code=410, detail="session expired")
                if tg_user_id is None or authorized_at is None:
                    raise HTTPException(status_code=401, detail="awaiting bot authorization")

                user_id = _upsert_telegram_user(
                    cur,
                    tg_user_id=int(tg_user_id),
                    username=(tg_username or "").strip() or None,
                    first_name=(tg_first_name or "").strip() or None,
                    photo_url=(tg_photo_url or "").strip() or None,
                )
                _grant_owner_beta_if_match(cur, user_id, int(tg_user_id))
                merge_chat_id_on_login(cur, tg_user_id=int(tg_user_id))
                cur.execute(
                    """
                    UPDATE auth_bot_sessions
                    SET consumed_at = %s
                    WHERE token_hash = %s
                    """,
                    (now, token_hash),
                )
            conn.commit()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("auth_bot_complete: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc

    access = issue_access_token(user_id, tg_user_id=int(tg_user_id))
    username = (tg_username or "").strip() or None
    first_name = (tg_first_name or "").strip() or None
    photo_url = (tg_photo_url or "").strip() or None
    return {
        "access_token": access,
        "token_type": "bearer",
        "user_id": user_id,
        "tg_user_id": int(tg_user_id),
        "username": username,
        "first_name": first_name,
        "photo_url": photo_url,
    }


@app.post("/v1/auth/bot-complete")
def auth_bot_complete(payload: BotCompletePayload) -> dict[str, Any]:
    """Deep-link login step 2: exchange authorized token → JWT (one-time)."""
    return _complete_bot_auth(payload.auth_token)


@app.get("/v1/auth/bot-complete")
def auth_bot_complete_get(auth: str = Query(default="")) -> dict[str, Any]:
    """Same as POST — for return URL `?auth=` on /cabinet/."""
    return _complete_bot_auth(auth)


# 3c1 ─────────────────────────────────────────────────────────────────────────


@app.get("/health")
def health() -> dict[str, Any]:
    stats = draft_stats_24h()
    last_err = ai_last_error()
    out: dict[str, Any] = {
        "status": "ok",
        "version": _VERSION,
        **stats,
        "draft_fail_per_hour": draft_fail_per_hour(),
    }
    if last_err:
        out["ai_last_error"] = last_err
    return out


def _public_leads_week_count() -> int:
    """Visible leads ingested in the last 7 days (marketing ticker)."""
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*)::int
                    FROM leads
                    WHERE is_visible = TRUE
                      AND created_at >= NOW() - INTERVAL '7 days'
                    """
                )
                row = cur.fetchone()
                return int(row[0]) if row else 0
    except Exception as exc:
        logger.warning("site-stats: %s", exc)
        return 0


def _leads_week_display(n: int) -> int:
    """Round down to tens for «N+ лидов в неделю» strip."""
    if n < 10:
        return max(n, 0)
    return (n // 10) * 10


@app.get("/v1/public/site-stats")
def public_site_stats() -> dict[str, Any]:
    leads_week = _public_leads_week_count()
    return {
        "radar_online": True,
        "leads_week": leads_week,
        "leads_week_display": _leads_week_display(leads_week),
    }


# 3c2 ─────────────────────────────────────────────────────────────────────────


def _trim_skills_catalog(
    groups: list[dict[str, Any]],
    skills: list[dict[str, Any]],
    *,
    limit: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if limit >= len(skills):
        return groups, skills
    skills = skills[:limit]
    allowed = {s["tag"] for s in skills}
    trimmed_groups: list[dict[str, Any]] = []
    for group in groups:
        g_skills = [s for s in group.get("skills", []) if s.get("tag") in allowed]
        if g_skills:
            trimmed_groups.append({**group, "skills": g_skills})
    return trimmed_groups, skills


def _skills_catalog_popular_cached(
    *,
    category_list: list[str],
    days: int,
    limit: int,
) -> dict[str, Any]:
    """O168: TTL cache — load@50 hammers jsonb unnest on /v1/skills/catalog."""
    key = (tuple(category_list), days, limit)
    now = time.monotonic()
    hit = _SKILLS_CATALOG_CACHE.get(key)
    if hit and now - hit[0] < _SKILLS_CATALOG_TTL_SEC:
        return hit[1]
    with _SKILLS_CATALOG_LOCK:
        hit = _SKILLS_CATALOG_CACHE.get(key)
        if hit and now - hit[0] < _SKILLS_CATALOG_TTL_SEC:
            return hit[1]
        return _skills_catalog_popular_fetch(
            category_list=category_list,
            days=days,
            limit=limit,
            key=key,
            now=now,
        )


def _skills_catalog_popular_fetch(
    *,
    category_list: list[str],
    days: int,
    limit: int,
    key: tuple[Any, ...],
    now: float,
) -> dict[str, Any]:
    base_where, base_params = _feed_base_where_sql()
    catalog_where = base_where.replace("is_visible", "l.is_visible").replace(
        "source =", "l.source =",
    )
    with _db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT tag, COUNT(*)::int AS cnt
                FROM leads l,
                     jsonb_array_elements_text(COALESCE(l.lead_tags, '[]'::jsonb)) AS tag
                WHERE {catalog_where}
                  AND l.created_at >= NOW() - make_interval(days => %s)
                GROUP BY tag
                ORDER BY cnt DESC, tag
                LIMIT %s
                """,
                (*base_params, days, limit * 4),
            )
            rows = cur.fetchall()
    groups, skills = build_dynamic_catalog_groups(
        [(str(t), int(c)) for t, c in rows],
        categories=category_list or None,
    )
    groups, skills = _trim_skills_catalog(groups, skills, limit=limit)
    payload = {"groups": groups, "skills": skills}
    _SKILLS_CATALOG_CACHE[key] = (now, payload)
    return payload


@app.get("/v1/skills/catalog")
def skills_catalog(
    limit: int = Query(default=_SKILLS_CATALOG_LIMIT, ge=1, le=200),
    category: str = Query(default=""),
    days: int = Query(default=_SKILLS_CATALOG_DAYS, ge=1, le=90),
    mode: str = Query(default="popular"),
) -> dict[str, Any]:
    """popular — top lead_tags; full — статический L1 pool (Tier A+B)."""
    if mode not in ("popular", "full"):
        raise HTTPException(status_code=400, detail="mode must be popular or full")
    category_list = parse_category_param(category)
    if mode == "full":
        groups, skills = build_catalog_groups(
            categories=category_list or None,
            ui_only=False,
        )
        groups, skills = _trim_skills_catalog(groups, skills, limit=limit)
        return {"groups": groups, "skills": skills}
    try:
        return _skills_catalog_popular_cached(
            category_list=category_list,
            days=days,
            limit=limit,
        )
    except Exception as exc:
        logger.error("skills_catalog: %s", exc)
        raise HTTPException(status_code=500, detail="catalog error")


@app.get("/v1/feed")
def feed(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    min_score: int = Query(default=0, ge=0, le=100),
    min_match: int = Query(default=0, ge=0, le=100),
    skills: str = Query(default=""),
    category: str = Query(default=""),
    sort: str = Query(default="time"),
    source: str = Query(default=""),
    authorization: str = Header(default="", alias="Authorization"),
) -> dict[str, Any]:
    """Лента: is_visible=true; anon → delay 15m; any valid JWT → instant."""
    if sort not in ("time", "match"):
        raise HTTPException(status_code=400, detail="sort must be time or match")
    if min_match not in _FEED_PREFS_MIN_MATCH:
        raise HTTPException(status_code=400, detail="min_match must be 0, 50, 60, 70, 80, or 90")
    skill_list = _parse_skills_param(skills)
    category_list = parse_category_param(category)
    source_keys = parse_feed_source_param(source)
    tag_weights = tags_as_weights(skill_list)
    apply_delay = True
    user_id = _try_user_from_bearer(authorization)
    feed_user_id: str | None = None
    today_count = 0
    if user_id:
        apply_delay = False
        feed_user_id = user_id
    try:
        with _db_conn() as conn:
            with conn.cursor() as cur:
                if user_id and not skill_list:
                    items, count, today_count = _personal_feed_page(
                        cur,
                        user_id,
                        limit=limit,
                        offset=offset,
                        min_score=min_score,
                        min_match=min_match,
                        skills=skill_list,
                        categories=category_list,
                        sort=sort,
                        source_keys=source_keys,
                    )
                elif sort == "match":
                    items, count, today_count = _feed_page_match(
                        cur,
                        limit=limit,
                        offset=offset,
                        min_score=min_score,
                        skills=skill_list,
                        categories=category_list,
                        tag_weights=tag_weights,
                        apply_delay=apply_delay,
                        user_id=feed_user_id,
                        min_match=min_match if min_match > 0 else None,
                        source_keys=source_keys,
                    )
                else:
                    items, count, today_count = _feed_page_time(
                        cur,
                        limit=limit,
                        offset=offset,
                        min_score=min_score,
                        skills=skill_list,
                        categories=category_list,
                        tag_weights=tag_weights,
                        apply_delay=apply_delay,
                        user_id=feed_user_id,
                        min_match=min_match if min_match > 0 else None,
                        source_keys=source_keys,
                    )
                if today_count is None:
                    today_count = _feed_today_count_cached(
                        cur,
                        skills=skill_list,
                        categories=category_list,
                        apply_delay=apply_delay,
                    )
    except Exception as exc:
        logger.error("feed: %s", exc)
        raise HTTPException(status_code=500, detail="db error")
    return {
        "items": items,
        "limit": limit,
        "offset": offset,
        "count": count,
        "today_count": today_count,
        "sort": sort,
        "min_match": min_match,
        "skills": skill_list,
        "category": category_list,
        "source": source_keys,
        "feed_delayed": apply_delay,
    }


# 3c3 ─────────────────────────────────────────────────────────────────────────


@app.get("/v1/leads/{lead_id}")
def get_lead(
    lead_id: int,
    authorization: str = Header(default="", alias="Authorization"),
) -> dict[str, Any]:
    """Одна карточка лида по id; Bearer → keyword_match для deep link ?lead=."""
    user_id = _try_user_from_bearer(authorization)
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {_SELECT_COLS} FROM leads WHERE id = %s",
                    (lead_id,),
                )
                row = cur.fetchone()
                if row is None:
                    raise HTTPException(status_code=404, detail="not found")
                km: int | None = None
                if user_id:
                    user_tags = _load_user_tags(cur, user_id)
                    tags, _ = lead_tags_for_feed(row[8])
                    km = keyword_match(tags, user_tags) if user_tags else 0
                item = _row_to_item(row, keyword_match_val=km)
                if user_id:
                    _attach_personal_replies(cur, user_id, [item])
                else:
                    item["reply_draft"] = ""
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_lead %d: %s", lead_id, exc)
        raise HTTPException(status_code=500, detail="db error")
    return item


# 3e — me (cabinet) ───────────────────────────────────────────────────────────


class TagsPayload(BaseModel):
    tags: list[str]


@app.get("/v1/me/tags")
def me_tags(user_id: str = Depends(_resolve_user_id)) -> dict[str, Any]:
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT tag FROM user_tags WHERE user_id = %s::uuid ORDER BY tag",
                    (user_id,),
                )
                raw = [r[0] for r in cur.fetchall()]
                tags = normalize_user_tags(raw)
                if set(raw) != set(tags) or len(raw) != len(tags):
                    _rewrite_user_tags(cur, user_id, tags)
            conn.commit()
    except Exception as exc:
        logger.error("me_tags: %s", exc)
        raise HTTPException(status_code=500, detail="db error")
    return {"tags": tags}


@app.put("/v1/me/tags")
def me_tags_put(
    payload: TagsPayload,
    user_id: str = Depends(_resolve_user_id),
) -> dict[str, Any]:
    if user_tags_input_count(payload.tags) > _USER_MAX_TAGS:
        raise HTTPException(
            status_code=400,
            detail=f"max {_USER_MAX_TAGS} skills allowed",
        )
    tags = normalize_user_tags(payload.tags)
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                _rewrite_user_tags(cur, user_id, tags)
            conn.commit()
    except Exception as exc:
        logger.error("me_tags_put: %s", exc)
        raise HTTPException(status_code=500, detail="db error")
    return {"tags": tags}


def _default_feed_prefs() -> dict[str, Any]:
    return {"sort": "time", "min_match": 80, "category": "", "source": "", "updated_at": None}


def _normalize_feed_prefs(raw: Any) -> dict[str, Any]:
    base = _default_feed_prefs()
    if not isinstance(raw, dict):
        return base
    sort = str(raw.get("sort") or "time").strip()
    if sort not in _FEED_PREFS_SORT:
        sort = "time"
    try:
        min_match = int(raw.get("min_match", 80))
    except (TypeError, ValueError):
        min_match = 80
    if min_match not in _FEED_PREFS_MIN_MATCH:
        min_match = 80
    category = str(raw.get("category") or "").strip()
    source = str(raw.get("source") or "").strip()
    if source:
        source = ",".join(parse_feed_source_param(source))
    updated_at = raw.get("updated_at")
    if updated_at is not None:
        updated_at = str(updated_at)
    return {
        "sort": sort,
        "min_match": min_match,
        "category": category,
        "source": source,
        "updated_at": updated_at,
    }


def _load_feed_prefs(cur: Any, user_id: str) -> dict[str, Any]:
    cur.execute(
        "SELECT feed_prefs FROM users WHERE id = %s::uuid",
        (user_id,),
    )
    row = cur.fetchone()
    if not row:
        return _default_feed_prefs()
    return _normalize_feed_prefs(row[0])


def _save_feed_prefs(cur: Any, user_id: str, prefs: dict[str, Any]) -> dict[str, Any]:
    from datetime import datetime, timezone

    normalized = _normalize_feed_prefs(prefs)
    normalized["updated_at"] = datetime.now(timezone.utc).isoformat()
    cur.execute(
        "UPDATE users SET feed_prefs = %s::jsonb WHERE id = %s::uuid",
        (json.dumps(normalized, ensure_ascii=False), user_id),
    )
    return normalized


class FeedPrefsPayload(BaseModel):
    sort: str | None = None
    min_match: int | None = None
    category: str | None = None
    source: str | None = None


@app.get("/v1/me/feed-prefs")
def me_feed_prefs_get(user_id: str = Depends(_resolve_user_id)) -> dict[str, Any]:
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                return _load_feed_prefs(cur, user_id)
    except Exception as exc:
        logger.error("me_feed_prefs_get: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc


@app.put("/v1/me/feed-prefs")
def me_feed_prefs_put(
    payload: FeedPrefsPayload,
    user_id: str = Depends(_resolve_user_id),
) -> dict[str, Any]:
    if payload.min_match is not None and payload.min_match not in _FEED_PREFS_MIN_MATCH:
        raise HTTPException(status_code=400, detail="min_match must be 0, 50, 60, 70, 80, or 90")
    if payload.sort is not None and payload.sort not in _FEED_PREFS_SORT:
        raise HTTPException(status_code=400, detail="sort must be time or match")
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                current = _load_feed_prefs(cur, user_id)
                if payload.sort is not None:
                    current["sort"] = payload.sort
                if payload.min_match is not None:
                    current["min_match"] = payload.min_match
                if payload.category is not None:
                    current["category"] = str(payload.category).strip()
                if payload.source is not None:
                    current["source"] = ",".join(parse_feed_source_param(str(payload.source)))
                saved = _save_feed_prefs(cur, user_id, current)
            conn.commit()
        return saved
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("me_feed_prefs_put: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc


@app.get("/v1/me/feed")
def me_feed(
    user_id: str = Depends(_resolve_user_id),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    min_score: int = Query(default=0, ge=0, le=100),
    min_match: int = Query(default=0, ge=0, le=100),
    skills: str = Query(default=""),
    category: str = Query(default=""),
    sort: str = Query(default="time"),
) -> dict[str, Any]:
    """Персональная лента: user_tags, is_visible=true; sort=time|match; min_match on keyword_match."""
    if sort not in ("time", "match"):
        raise HTTPException(status_code=400, detail="sort must be time or match")
    skill_list = _parse_skills_param(skills)
    category_list = parse_category_param(category)
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                items, count, _today = _personal_feed_page(
                    cur,
                    user_id,
                    limit=limit,
                    offset=offset,
                    min_score=min_score,
                    min_match=min_match,
                    skills=skill_list,
                    categories=category_list,
                    sort=sort,
                )
    except Exception as exc:
        logger.error("me_feed: %s", exc)
        raise HTTPException(status_code=500, detail="db error")
    return {
        "items": items,
        "limit": limit,
        "offset": offset,
        "count": count,
        "sort": sort,
        "min_match": min_match,
        "skills": skill_list,
        "category": category_list,
        "feed_delayed": False,
    }


def _fetch_visible_lead(cur: Any, lead_id: int) -> tuple[Any, ...] | None:
    feed_where, feed_params = _feed_where_sql()
    cur.execute(
        f"SELECT {_SELECT_COLS} FROM leads WHERE id = %s AND {feed_where}",
        (lead_id, *feed_params),
    )
    return cur.fetchone()


def _parse_ai_reasons(raw: Any) -> list[str]:
    from ai_reasons import parse_ai_reasons_raw

    reasons, _ = parse_ai_reasons_raw(raw)
    return reasons


def _draft_http_error(exc: DraftError, *, lead_id: int) -> HTTPException:
    if exc.code == "ai_unavailable":
        from ai_analyze import note_ai_error, note_draft_request

        note_draft_request(False)
        note_ai_error(exc.detail or "ai unavailable")
        return HTTPException(status_code=503, detail="ai unavailable")
    if exc.code == "forbidden":
        return HTTPException(status_code=403, detail=exc.detail)
    if exc.code == "not_found":
        return HTTPException(status_code=404, detail="not found")
    if exc.code == "rate_limit":
        return HTTPException(status_code=429, detail=exc.detail)
    if exc.code == "ai_fail":
        from ai_analyze import note_ai_error, note_draft_request

        note_draft_request(False)
        note_ai_error(exc.detail)
        stats = draft_stats_24h()
        logger.warning("lenta:draft:%d:fail %s", lead_id, exc.detail)
        logger.info(
            "lenta:draft:stats draft_ok=%d draft_fail=%d",
            stats["draft_ok"],
            stats["draft_fail"],
        )
        from src.draft_async import sanitize_draft_error_detail

        user_msg = sanitize_draft_error_detail(exc.detail)
        return HTTPException(
            status_code=503,
            detail={
                "detail": user_msg,
                "error": user_msg,
                "retry_after_sec": _DRAFT_RETRY_AFTER_SEC,
            },
        )
    return HTTPException(status_code=500, detail="db error")


def _me_lead_draft_response(
    resp: Any,
    *,
    lead_id: int,
) -> Any:
    from fastapi.responses import JSONResponse

    body = draft_response_body(resp)
    if resp.status == "ready":
        reply = strip_reply_draft_price_deadline(body.get("reply_draft") or "")
        body["reply_draft"] = reply
        stats = draft_stats_24h()
        logger.info(
            "lenta:draft:%d:ok draft_ok=%d draft_fail=%d",
            lead_id,
            stats["draft_ok"],
            stats["draft_fail"],
        )
        return body
    if resp.status == "failed":
        stats = draft_stats_24h()
        logger.warning("lenta:draft:%d:fail %s", lead_id, body.get("error", ""))
        logger.info(
            "lenta:draft:stats draft_ok=%d draft_fail=%d",
            stats["draft_ok"],
            stats["draft_fail"],
        )
        return body
    return JSONResponse(status_code=202, content=body)


@app.get("/v1/me/leads/{lead_id}/draft")
def me_lead_draft_get(
    lead_id: int,
    user_id: str = Depends(_resolve_user_id),
) -> Any:
    """O56: poll async draft status."""
    cfg = load_config()
    if not cfg.ai_active:
        raise HTTPException(status_code=503, detail="ai unavailable")
    resp = poll_draft(
        cfg,
        user_id=user_id,
        lead_id=lead_id,
        log_prefix=f"lenta:draft:{lead_id}:",
    )
    return _me_lead_draft_response(resp, lead_id=lead_id)


@app.post("/v1/me/leads/{lead_id}/draft")
def me_lead_draft(
    lead_id: int,
    user_id: str = Depends(_resolve_user_id),
) -> Any:
    """O56: on-demand L2 async — 202 pending или 200 ready."""
    cfg = load_config()
    if not cfg.ai_active:
        raise HTTPException(status_code=503, detail="ai unavailable")

    retry_after = draft_rate_limit_retry_after(user_id)
    if retry_after is not None:
        msg = draft_rate_limit_detail() or "draft rate limit"
        raise HTTPException(
            status_code=429,
            detail={
                "detail": msg,
                "retry_after_sec": retry_after,
            },
        )

    try:
        resp = submit_draft(
            cfg,
            user_id=user_id,
            lead_id=lead_id,
            log_prefix=f"lenta:draft:{lead_id}:",
        )
    except DraftError as exc:
        raise _draft_http_error(exc, lead_id=lead_id) from exc
    except Exception as exc:
        logger.error("me_lead_draft %d: %s", lead_id, exc)
        raise HTTPException(status_code=500, detail="db error") from exc

    return _me_lead_draft_response(resp, lead_id=lead_id)


@app.post("/v1/me/leads/{lead_id}/draft/warm")
def me_lead_draft_warm(
    lead_id: int,
    user_id: str = Depends(_resolve_user_id),
) -> Any:
    """O148: pre-warm shared L2 on premium expand — no user_lead_replies."""
    cfg = load_config()
    if not cfg.ai_active:
        raise HTTPException(status_code=503, detail="ai unavailable")

    try:
        resp = submit_warm(
            cfg,
            user_id=user_id,
            lead_id=lead_id,
            log_prefix=f"lenta:draft:warm:{lead_id}:",
        )
    except DraftError as exc:
        if exc.code == "rate_limit":
            raise HTTPException(
                status_code=429,
                detail={"detail": exc.detail or "warm rate limit"},
            ) from exc
        raise _draft_http_error(exc, lead_id=lead_id) from exc
    except Exception as exc:
        logger.error("me_lead_draft_warm %d: %s", lead_id, exc)
        raise HTTPException(status_code=500, detail="db error") from exc

    body = draft_response_body(resp)
    if resp.status == "ready":
        return JSONResponse(status_code=200, content=body)
    return JSONResponse(status_code=202, content=body)


@app.get("/v1/me/replies")
def me_replies(
    user_id: str = Depends(_resolve_user_id),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Inbox откликов для /cabinet/ (без soft-deleted; 7d по replied_at)."""
    inbox_where, inbox_params = inbox_replies_where_sql(alias="ulr")
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                user_tags = _load_user_tags(cur, user_id)
                cur.execute(
                    f"""
                    SELECT {_INBOX_SELECT_COLS}, ulr.created_at AS replied_at
                    FROM user_lead_replies ulr
                    INNER JOIN leads l ON l.id = ulr.lead_id
                    WHERE ulr.user_id = %s::uuid
                      AND {inbox_where}
                    ORDER BY ulr.created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user_id, *inbox_params, limit, offset),
                )
                rows = cur.fetchall()
                cur.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM user_lead_replies ulr
                    INNER JOIN leads l ON l.id = ulr.lead_id
                    WHERE ulr.user_id = %s::uuid
                      AND {inbox_where}
                    """,
                    (user_id, *inbox_params),
                )
                total = int(cur.fetchone()[0])
    except Exception as exc:
        logger.error("me_replies: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc

    items: list[dict[str, Any]] = []
    for row in rows:
        lead_row = row[:15]
        replied_at = row[15]
        tags = _canonical_lead_tags(lead_row[8])
        km = keyword_match(tags, user_tags) if user_tags else None
        item = _row_to_item(lead_row, keyword_match_val=km, feed_delayed=False)
        item["replied_at"] = replied_at.isoformat() if replied_at else None
        items.append(item)

    return {
        "items": items,
        "limit": limit,
        "offset": offset,
        "count": len(items),
        "total": total,
    }


@app.delete("/v1/me/replies/{lead_id}")
def me_reply_delete(
    lead_id: int,
    user_id: str = Depends(_resolve_user_id),
) -> dict[str, Any]:
    """Soft-delete отклика из inbox."""
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE user_lead_replies
                    SET deleted_at = NOW()
                    WHERE user_id = %s::uuid
                      AND lead_id = %s
                      AND deleted_at IS NULL
                    RETURNING lead_id
                    """,
                    (user_id, lead_id),
                )
                deleted = cur.fetchone()
                conn.commit()
    except Exception as exc:
        logger.error("me_reply_delete %d: %s", lead_id, exc)
        raise HTTPException(status_code=500, detail="db error") from exc
    if deleted is None:
        raise HTTPException(status_code=404, detail="not found")
    return {"id": lead_id, "deleted": True}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _ensure_subscription(
    cur: Any, user_id: str
) -> tuple[str, bool, datetime | None, datetime | None, datetime | None]:
    plan, is_active, active_until, paused_until, trial_used_at = fetch_subscription_row(
        cur, user_id
    )
    if plan != "free" or is_active or active_until or paused_until or trial_used_at:
        return plan, is_active, active_until, paused_until, trial_used_at

    cur.execute(
        """
        INSERT INTO subscriptions (user_id, plan, is_active)
        VALUES (%s::uuid, 'free', FALSE)
        ON CONFLICT (user_id) DO NOTHING
        """,
        (user_id,),
    )
    return fetch_subscription_row(cur, user_id)


def _subscription_payload(
    plan: str,
    is_active: bool,
    active_until: datetime | None,
    paused_until: datetime | None,
    trial_used_at: datetime | None = None,
) -> dict[str, Any]:
    now = _utc_now()
    pu = _as_utc(paused_until)
    if pu is not None and pu <= now:
        paused_until = None
        pu = None

    status, effective_access = resolve_subscription_status(
        plan or "free",
        is_active,
        _as_utc(active_until),
        pu,
        now=now,
    )
    paused = status == "paused"

    plan_labels = {
        "owner": "ИИ-агент (владелец)",
        "agent": "ИИ-агент",
        "pro": "ИИ-агент",
        "trial": "Trial Premium",
        "free": "ИИ-агент",
    }

    payload: dict[str, Any] = {
        "plan": plan or "free",
        "plan_label": plan_labels.get(plan, "ИИ-агент"),
        "is_active": is_active,
        "active_until": active_until.isoformat() if active_until else None,
        "paused_until": paused_until.isoformat() if paused_until else None,
        "status": status,
        "effective_access": effective_access,
        "can_pause": is_active and not paused and status == "active",
        "stars_available": stars_available(load_config()),
    }
    payload.update(
        subscription_extra_fields(
            plan or "free",
            is_active,
            _as_utc(active_until),
            _as_utc(trial_used_at),
            now=now,
        )
    )
    return payload


@app.get("/v1/me/subscription")
def me_subscription(user_id: str = Depends(_resolve_user_id)) -> dict[str, Any]:
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                expire_stale_trials(cur)
                plan, is_active, active_until, paused_until, trial_used_at = (
                    _ensure_subscription(cur, user_id)
                )
                if paused_until is not None and paused_until <= _utc_now():
                    cur.execute(
                        """
                        UPDATE subscriptions
                        SET paused_until = NULL
                        WHERE user_id = %s::uuid AND paused_until IS NOT NULL
                          AND paused_until <= NOW()
                        """,
                        (user_id,),
                    )
                    paused_until = None
                conn.commit()
                plan, is_active, active_until, paused_until, trial_used_at = (
                    fetch_subscription_row(cur, user_id)
                )
                return _subscription_payload(
                    plan, is_active, active_until, paused_until, trial_used_at
                )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("me_subscription: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc


@app.post("/v1/me/subscription/trial-start")
def me_subscription_trial_start(
    user_id: str = Depends(_resolve_user_id),
) -> dict[str, Any]:
    try:
        cfg = load_config()
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                expire_stale_trials(cur)
                try:
                    start_trial(cur, user_id)
                except TrialStartError as exc:
                    raise HTTPException(status_code=409, detail=exc.detail) from exc
                notify_trial_started(cfg, cur, user_id)
                conn.commit()
                plan, is_active, active_until, paused_until, trial_used_at = (
                    fetch_subscription_row(cur, user_id)
                )
                return _subscription_payload(
                    plan, is_active, active_until, paused_until, trial_used_at
                )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("me_subscription_trial_start: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc


class SubscriptionPausePayload(BaseModel):
    days: int | None = None
    resume: bool = False


@app.post("/v1/me/subscription/pause")
def me_subscription_pause(
    payload: SubscriptionPausePayload,
    user_id: str = Depends(_resolve_user_id),
) -> dict[str, Any]:
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                plan, is_active, active_until, paused_until, trial_used_at = (
                    _ensure_subscription(cur, user_id)
                )
                if payload.resume:
                    cur.execute(
                        """
                        UPDATE subscriptions
                        SET paused_until = NULL
                        WHERE user_id = %s::uuid
                        """,
                        (user_id,),
                    )
                    conn.commit()
                    return _subscription_payload(
                        plan, is_active, active_until, None, trial_used_at
                    )

                if not is_active or plan in ("free", "", "trial"):
                    raise HTTPException(status_code=403, detail="subscription not active")

                days = payload.days if payload.days is not None else 14
                if days < 1 or days > 90:
                    raise HTTPException(status_code=400, detail="days must be 1..90")

                until = _utc_now() + timedelta(days=days)
                cur.execute(
                    """
                    UPDATE subscriptions
                    SET paused_until = %s
                    WHERE user_id = %s::uuid
                    """,
                    (until, user_id),
                )
                conn.commit()
                return _subscription_payload(
                    plan, is_active, active_until, until, trial_used_at
                )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("me_subscription_pause: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc


@app.get("/v1/me/notification-settings")
def me_notification_settings_get(user_id: str = Depends(_resolve_user_id)) -> dict[str, Any]:
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COALESCE(push_min_match, 60), COALESCE(push_enabled, TRUE)
                    FROM users WHERE id = %s::uuid
                    """,
                    (user_id,),
                )
                row = cur.fetchone()
                if not row:
                    return {"push_min_match": 60, "push_enabled": True}
                return {"push_min_match": row[0], "push_enabled": bool(row[1])}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("me_notification_settings_get: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc


class NotificationSettingsPayload(BaseModel):
    push_min_match: int | None = None
    push_enabled: bool | None = None


@app.patch("/v1/me/notification-settings")
def me_notification_settings_patch(
    payload: NotificationSettingsPayload,
    user_id: str = Depends(_resolve_user_id),
) -> dict[str, Any]:
    if payload.push_min_match is not None and not (30 <= payload.push_min_match <= 100):
        raise HTTPException(status_code=400, detail="push_min_match must be 30..100")
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                if payload.push_min_match is not None and payload.push_enabled is not None:
                    cur.execute(
                        """
                        UPDATE users SET push_min_match = %s, push_enabled = %s
                        WHERE id = %s::uuid
                        """,
                        (payload.push_min_match, payload.push_enabled, user_id),
                    )
                elif payload.push_min_match is not None:
                    cur.execute(
                        "UPDATE users SET push_min_match = %s WHERE id = %s::uuid",
                        (payload.push_min_match, user_id),
                    )
                elif payload.push_enabled is not None:
                    cur.execute(
                        "UPDATE users SET push_enabled = %s WHERE id = %s::uuid",
                        (payload.push_enabled, user_id),
                    )
                conn.commit()
                cur.execute(
                    """
                    SELECT COALESCE(push_min_match, 60), COALESCE(push_enabled, TRUE)
                    FROM users WHERE id = %s::uuid
                    """,
                    (user_id,),
                )
                row = cur.fetchone()
                if not row:
                    return {"push_min_match": 60, "push_enabled": True}
                return {"push_min_match": row[0], "push_enabled": bool(row[1])}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("me_notification_settings_patch: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc


class SupportTicketPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str
    url: str = ""
    source: str = "fab"
    contact_name: str = ""


def _resolve_support_actor(
    authorization: str = Header(default="", alias="Authorization"),
    x_rawlead_guest: str = Header(default="", alias="X-RawLead-Guest-Token"),
) -> tuple[str | None, str | None]:
    user_id = _try_user_from_bearer(authorization)
    if user_id:
        return user_id, None
    guest = normalize_guest_token(x_rawlead_guest)
    if guest:
        return None, guest
    raise HTTPException(
        status_code=400,
        detail="X-RawLead-Guest-Token required when not logged in",
    )


@app.post("/v1/support/ticket")
def support_ticket_create(
    payload: SupportTicketPayload,
    actor: tuple[str | None, str | None] = Depends(_resolve_support_actor),
) -> dict[str, Any]:
    user_id, guest_token = actor
    try:
        return create_user_ticket(
            _db_url(),
            user_id=user_id,
            guest_token=guest_token,
            source=payload.source,
            page_url=(payload.url or "").strip(),
            body=payload.message,
            contact_name=payload.contact_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("support_ticket_create: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc


@app.get("/v1/support/thread")
def support_thread_get(
    actor: tuple[str | None, str | None] = Depends(_resolve_support_actor),
) -> dict[str, Any]:
    user_id, guest_token = actor
    try:
        return get_user_thread(_db_url(), user_id=user_id, guest_token=guest_token)
    except Exception as exc:
        logger.error("support_thread_get: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc


@app.get("/v1/support/unread")
def support_unread_get(
    actor: tuple[str | None, str | None] = Depends(_resolve_support_actor),
) -> dict[str, int]:
    user_id, guest_token = actor
    try:
        count = get_unread_count(_db_url(), user_id=user_id, guest_token=guest_token)
        return {"unread": count}
    except Exception as exc:
        logger.error("support_unread_get: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc


def _require_owner_user(
    user_id: str = Depends(_resolve_bearer_user_id),
) -> str:
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                if not is_owner_db_user(cur, user_id):
                    raise HTTPException(status_code=403, detail="owner only")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("_require_owner_user: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc
    return user_id


def _ops_gate_key() -> str:
    return (os.getenv("RAWLEAD_OPS_KEY") or os.getenv("OPS_PASSWORD") or "").strip()


def _ops_password_match(supplied: str, gate: str) -> bool:
    if not supplied or not gate:
        return False
    if len(supplied) != len(gate):
        return False
    return secrets.compare_digest(supplied, gate)


def _ops_access_granted(request: Request, key: str = "") -> bool:
    gate = _ops_gate_key()
    if not gate:
        return True
    supplied = (key or request.cookies.get("rl_ops_key", "")).strip()
    return _ops_password_match(supplied, gate)


def _ops_cookie_kwargs() -> dict[str, Any]:
    return {
        "httponly": True,
        "secure": True,
        "samesite": "lax",
        "max_age": 86400 * 30,
    }


def _require_ops_access(request: Request) -> None:
    if not _ops_access_granted(request):
        raise HTTPException(status_code=401, detail="ops auth required")


def _ops_jwt_from_request(request: Request) -> str:
    auth = (request.headers.get("authorization") or "").strip()
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        if token:
            return token
    return (request.cookies.get("rl_access") or "").strip()


def _owner_dashboard_data(jwt: str) -> dict[str, Any] | None:
    if not jwt:
        return None
    try:
        user_id = str(decode_access_token(jwt)["sub"])
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                if not is_owner_db_user(cur, user_id):
                    return None
        return fetch_dashboard(_db_url())
    except Exception as exc:
        logger.warning("ops SSR dashboard: %s", exc)
        return None


class OpsControlPayload(BaseModel):
    target: str
    action: str
    group: str | None = None
    slot: int | None = None


class SupportAdminReplyPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str


@app.get("/ops/", response_class=HTMLResponse)
def ops_dashboard_page(
    request: Request,
    key: str = Query(default=""),
) -> HTMLResponse:
    """O45/O78/O161: password cookie → SSR; иначе форма входа."""
    gate = _ops_gate_key()
    if gate and not _ops_access_granted(request, key):
        show_err = request.query_params.get("err") == "1"
        return HTMLResponse(ops_login_html(show_error=show_err))
    data: dict[str, Any] | None = None
    if _ops_access_granted(request, key):
        try:
            data = fetch_dashboard(_db_url())
        except Exception as exc:
            logger.warning("ops SSR dashboard: %s", exc)
    elif not gate:
        jwt = _ops_jwt_from_request(request)
        data = _owner_dashboard_data(jwt)
    api_base = "/ops" if gate else os.getenv("RAWLEAD_OPS_API_BASE", "/wp-json/rawlead/v1").strip()
    resp = HTMLResponse(
        ops_html(api_base=api_base, data=data, ops_authenticated=_ops_access_granted(request, key))
    )
    if gate and key == gate:
        resp.set_cookie("rl_ops_key", gate, **_ops_cookie_kwargs())
    return resp


@app.post("/ops/login")
async def ops_login(request: Request) -> RedirectResponse:
    gate = _ops_gate_key()
    if not gate:
        raise HTTPException(status_code=404, detail="Not found")
    password = ""
    ct = (request.headers.get("content-type") or "").lower()
    if "application/json" in ct:
        try:
            body = await request.json()
            if isinstance(body, dict):
                password = str(body.get("password") or "")
        except Exception:
            password = ""
    else:
        raw = (await request.body()).decode("utf-8", errors="replace")
        password = parse_qs(raw).get("password", [""])[0]
    supplied = (password or "").strip()
    if not _ops_password_match(supplied, gate):
        return RedirectResponse(url="/ops/?err=1", status_code=303)
    resp = RedirectResponse(url="/ops/", status_code=303)
    resp.set_cookie("rl_ops_key", gate, **_ops_cookie_kwargs())
    return resp


@app.get("/ops/logout")
def ops_logout() -> RedirectResponse:
    resp = RedirectResponse(url="/ops/", status_code=303)
    resp.delete_cookie("rl_ops_key")
    return resp


@app.get("/ops/log/stream")
def ops_log_stream(request: Request) -> StreamingResponse:
    """O161: SSE tail radar_site.log — same-origin or rl_ops_key cookie."""
    gate = _ops_gate_key()
    if gate and not _ops_access_granted(request):
        raise HTTPException(status_code=401, detail="ops auth required")
    return StreamingResponse(
        iter_radar_log_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/ops/dashboard")
def ops_dashboard_json(request: Request) -> dict[str, Any]:
    _require_ops_access(request)
    return fetch_dashboard(_db_url())


@app.post("/ops/control")
def ops_control_route(request: Request, payload: OpsControlPayload) -> dict[str, Any]:
    _require_ops_access(request)
    result = run_ops_control(
        target=payload.target,
        action=payload.action,
        group=payload.group or "",
        slot=payload.slot,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("message", "control failed"))
    return result


@app.post("/ops/leads/{lead_id}/hide")
def ops_hide_lead(request: Request, lead_id: int) -> dict[str, Any]:
    _require_ops_access(request)
    if lead_id <= 0:
        raise HTTPException(status_code=400, detail="invalid lead id")
    if not hide_lead(_db_url(), lead_id):
        raise HTTPException(status_code=404, detail="lead not found or already hidden")
    return {"ok": True, "lead_id": lead_id}


@app.get("/ops/support/tickets")
def ops_support_tickets(
    request: Request,
    limit: int = Query(default=30, ge=1, le=100),
) -> dict[str, Any]:
    _require_ops_access(request)
    try:
        return {"tickets": admin_list_tickets(_db_url(), limit=limit)}
    except Exception as exc:
        logger.error("ops_support_tickets: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc


@app.post("/ops/support/tickets/{ticket_id}/reply")
def ops_support_ticket_reply(
    request: Request,
    ticket_id: int,
    payload: SupportAdminReplyPayload,
) -> dict[str, Any]:
    _require_ops_access(request)
    try:
        return admin_reply(_db_url(), ticket_id=ticket_id, body=payload.message)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("ops_support_ticket_reply: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc


@app.get("/v1/admin/dashboard")
def admin_dashboard(_owner: str = Depends(_require_owner_user)) -> dict[str, Any]:
    del _owner
    return fetch_dashboard(_db_url())


@app.post("/v1/admin/leads/{lead_id}/hide")
def admin_hide_lead(
    lead_id: int,
    _owner: str = Depends(_require_owner_user),
) -> dict[str, Any]:
    del _owner
    if lead_id <= 0:
        raise HTTPException(status_code=400, detail="invalid lead id")
    if not hide_lead(_db_url(), lead_id):
        raise HTTPException(status_code=404, detail="lead not found or already hidden")
    return {"ok": True, "lead_id": lead_id}


class PageviewPayload(BaseModel):
    path: str = "/"
    visitor_id: str = ""


@app.post("/v1/admin/pageview", status_code=204)
def admin_pageview_beacon(payload: PageviewPayload, request: Request) -> Response:
    """O45: публичный beacon — только path, агрегат по дням."""
    allowed_prefixes = ("/", "/lenta", "/cabinet", "/pricing", "/how", "/contact")
    path = (payload.path or "/").strip()[:200] or "/"
    if not any(path == p or path.startswith(p + "/") for p in allowed_prefixes):
        raise HTTPException(status_code=400, detail="path not allowed")
    visitor = (payload.visitor_id or "").strip()[:64]
    if not visitor:
        # Fallback when frontend has not yet sent local visitor id.
        host = (request.client.host if request.client else "") or "0.0.0.0"
        ua = (request.headers.get("user-agent") or "")[:200]
        seed = f"{host}|{ua}|{datetime.now(timezone.utc).date().isoformat()}"
        visitor = hashlib.sha1(seed.encode("utf-8", "ignore")).hexdigest()[:40]
    record_pageview(_db_url(), path=path, visitor_id=visitor)
    return Response(status_code=204)


@app.get("/v1/admin/proxies")
def admin_proxies(_owner: str = Depends(_require_owner_user)) -> dict[str, Any]:
    del _owner
    from src.proxy_ops import collect_proxies_payload, strip_internal_urls

    return strip_internal_urls(collect_proxies_payload())


@app.post("/v1/admin/control")
def admin_control(
    payload: OpsControlPayload,
    _owner: str = Depends(_require_owner_user),
) -> dict[str, Any]:
    del _owner
    if (payload.target or "").strip().lower() == "proxy":
        result = run_ops_control(
            target=payload.target,
            action=payload.action,
            group=payload.group or "",
            slot=payload.slot,
        )
        if not result.get("ok"):
            raise HTTPException(status_code=400, detail=result.get("message", "control failed"))
        return result
    result = run_ops_control(
        target=payload.target,
        action=payload.action,
        group=payload.group or "",
        slot=payload.slot,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("message", "control failed"))
    return result


@app.get("/v1/admin/support/tickets")
def admin_support_tickets_list(
    limit: int = Query(default=30, ge=1, le=100),
    _owner: str = Depends(_require_owner_user),
) -> dict[str, Any]:
    del _owner
    try:
        tickets = admin_list_tickets(_db_url(), limit=limit)
        return {"tickets": tickets}
    except Exception as exc:
        logger.error("admin_support_tickets_list: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc


@app.post("/v1/admin/support/tickets/{ticket_id}/reply")
def admin_support_ticket_reply(
    ticket_id: int,
    payload: SupportAdminReplyPayload,
    _owner: str = Depends(_require_owner_user),
) -> dict[str, Any]:
    del _owner
    try:
        return admin_reply(_db_url(), ticket_id=ticket_id, body=payload.message)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("admin_support_ticket_reply: %s", exc)
        raise HTTPException(status_code=500, detail="db error") from exc


# 3c4 ─────────────────────────────────────────────────────────────────────────


class IngestPayload(BaseModel):
    source: str
    external_id: str
    title: str = ""
    body: str = ""
    url: str = ""
    budget_text: str = ""
    ai_score: int | None = None
    ai_verdict: str | None = None
    lead_tags: list[str] = []
    ai_reasons: list[str] = []
    is_visible: bool = False
    content_hash: str | None = None
    category: str | None = None


@app.post(
    "/v1/internal/leads",
    status_code=201,
    dependencies=[Depends(_require_api_key)],
)
def ingest_lead(payload: IngestPayload) -> Any:
    """Ingest лида от радара. ON CONFLICT DO NOTHING — дубль вернёт 200."""
    h = (payload.content_hash or "").strip() or None
    tags_j = json.dumps(payload.lead_tags, ensure_ascii=False)
    reasons_j = json.dumps(payload.ai_reasons, ensure_ascii=False)
    stored_cat = normalize_category(payload.category or "")
    ingest_cat = (
        stored_cat
        if stored_cat and stored_cat != "other"
        else category_for_listing(
            payload.source,
            listing_category=payload.category or "",
            title=payload.title,
            snippet=payload.body,
        )
    )
    ingest_visible = payload.is_visible and is_public_feed_source(payload.source)

    base_cols = (
        "source, external_id, title, body, url, budget_text, "
        "ai_score, ai_verdict, lead_tags, ai_reasons, is_visible, category"
    )
    base_vals = (
        payload.source,
        payload.external_id,
        payload.title,
        payload.body,
        payload.url,
        payload.budget_text,
        payload.ai_score,
        payload.ai_verdict,
        tags_j,
        reasons_j,
        ingest_visible,
        ingest_cat,
    )

    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                if h:
                    cur.execute(
                        f"""
                        INSERT INTO leads ({base_cols}, content_hash)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s)
                        ON CONFLICT (content_hash) DO NOTHING
                        RETURNING id
                        """,
                        (*base_vals, h),
                    )
                else:
                    cur.execute(
                        f"""
                        INSERT INTO leads ({base_cols}, content_hash)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,NULL,%s)
                        ON CONFLICT (source, external_id) DO NOTHING
                        RETURNING id
                        """,
                        base_vals,
                    )
                inserted_row = cur.fetchone()
            conn.commit()
    except Exception as exc:
        logger.error("ingest: %s", exc)
        raise HTTPException(status_code=500, detail="db error")

    if inserted_row:
        return {"id": inserted_row[0], "inserted": True}
    return JSONResponse(
        status_code=200,
        content={"inserted": False, "reason": "duplicate"},
    )
