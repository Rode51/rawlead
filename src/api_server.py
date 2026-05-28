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
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID, uuid4

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
from src.public_feed import is_public_feed_source, public_feed_source_sql
from src.jwt_auth import decode_access_token, issue_access_token
from src.feed_social import display_views
from src.rank import (
    final_rank,
    keyword_match,
    normalize_tags,
    open_rank,
    parse_lead_tags,
    tags_as_weights,
)
from src.ai_analyze import (
    AiLiteAnalysis,
    analyze_premium,
    build_cabinet_profile_excerpt,
)
from src.stars_billing import stars_available

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
_FEED_RETENTION_DAYS = 7
_FEED_DELAY_MINUTES = 15
_BOT_FEED_WHERE = "is_visible = TRUE"
_HOT_MAX_AGE_SEC = 300


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


def _feed_where_sql(*, alias: str = "", apply_delay: bool = False) -> tuple[str, list[Any]]:
    base, params = _feed_base_where_sql(alias=alias)
    prefix = f"{alias}." if alias else ""
    sql = base + f" AND {prefix}created_at >= NOW() - make_interval(days => %s)"
    out_params: list[Any] = [*params, _FEED_RETENTION_DAYS]
    if apply_delay:
        sql += f" AND {prefix}created_at <= NOW() - make_interval(mins => %s)"
        out_params.append(_FEED_DELAY_MINUTES)
    return sql, out_params


# ─── helpers ─────────────────────────────────────────────────────────────────


def _db_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL not set")
    return url


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
    tags, tag_labels = lead_tags_for_feed(lead_tags)
    km = keyword_match_val
    fr = final_rank_val
    if fr is None:
        fr = open_rank(ai_score)
    category = resolve_lead_category(stored_category, title or "", body or "", tags)
    tools: list[str] = []
    if isinstance(tools_required, list):
        tools = [str(t).strip() for t in tools_required if str(t).strip()]
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
        "ai_reasons": ai_reasons if ai_reasons is not None else [],
        "final_rank": fr,
        "keyword_match": km,
        "category": category,
        "created_at": created_at.isoformat() if created_at else None,
        "is_hot": _lead_is_hot(created_at),
        "tools_required": tools,
        "reply_draft": (reply_draft or "").strip(),
        "display_views": display_views(lead_id, created_at, feed_delayed=feed_delayed),
    }


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
    if not categories:
        return "", []
    return " AND category = ANY(%s::text[])", [categories]


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
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for row in rows:
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
) -> tuple[list[dict[str, Any]], int]:
    cat_sql, cat_params = _category_sql(categories)
    sql_min = min_score
    if min_score >= 70:
        sql_min = effective_feed_min_score(min_score, "text")
    feed_where, feed_params = _feed_where_sql(apply_delay=apply_delay)
    cur.execute(
        f"""
        SELECT {_SELECT_COLS}
        FROM leads
        WHERE {feed_where}
          AND (ai_score IS NULL OR ai_score >= %s)
          {cat_sql}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        (*feed_params, sql_min, *cat_params, limit, offset),
    )
    rows = cur.fetchall()
    items: list[dict[str, Any]] = []
    for r in rows:
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
    return items, len(items)


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
) -> tuple[list[dict[str, Any]], int]:
    cat_sql, cat_params = _category_sql(categories)
    feed_where, feed_params = _feed_where_sql(apply_delay=apply_delay)
    cur.execute(
        f"""
        SELECT {_SELECT_COLS}
        FROM leads
        WHERE {feed_where}
          {cat_sql}
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (*feed_params, *cat_params, _ME_FEED_SCAN_LIMIT),
    )
    ranked = _rank_feed_rows(
        cur.fetchall(),
        tag_weights,
        min_score=min_score,
        sort="match",
        feed_delayed=apply_delay,
    )
    page = ranked[offset : offset + limit]
    return page, len(page)


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
) -> tuple[list[dict[str, Any]], int]:
    user_tags = _load_user_tags(cur, user_id)
    extra, extra_params = _skills_sql(skills)
    cat_sql, cat_params = _category_sql(categories)
    feed_where, feed_params = _feed_where_sql()
    cur.execute(
        f"""
        SELECT {_SELECT_COLS}
        FROM leads
        WHERE {feed_where}
          {extra}{cat_sql}
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (*feed_params, *extra_params, *cat_params, _ME_FEED_SCAN_LIMIT),
    )
    rows = cur.fetchall()
    if sort == "time":
        ranked: list[dict[str, Any]] = []
        for row in rows:
            tags = _canonical_lead_tags(row[8])
            km = keyword_match(tags, user_tags)
            if not _passes_min_match(km, min_match):
                continue
            fr = final_rank(row[6], km)
            ranked.append(
                _row_to_item(row, keyword_match_val=km, final_rank_val=fr, feed_delayed=False)
            )
        ranked.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    else:
        ranked = _rank_feed_rows(
            rows,
            user_tags,
            min_score=min_score,
            sort="match",
            min_match=min_match,
            feed_delayed=False,
        )
    page = ranked[offset : offset + limit]
    return page, len(page)


# ─── auth ─────────────────────────────────────────────────────────────────────


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
    plan, is_active, active_until, paused_until = _ensure_subscription(cur, user_id)
    payload = _subscription_payload(plan, is_active, active_until, paused_until)
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


# 3c1 ─────────────────────────────────────────────────────────────────────────


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": _VERSION}


# 3c2 ─────────────────────────────────────────────────────────────────────────


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
        if limit < len(skills):
            skills = skills[:limit]
            allowed = {s["tag"] for s in skills}
            trimmed_groups: list[dict[str, Any]] = []
            for group in groups:
                g_skills = [s for s in group.get("skills", []) if s.get("tag") in allowed]
                if g_skills:
                    trimmed_groups.append({**group, "skills": g_skills})
            groups = trimmed_groups
        return {"groups": groups, "skills": skills}
    base_where, base_params = _feed_base_where_sql()
    catalog_where = base_where.replace("is_visible", "l.is_visible").replace(
        "source =", "l.source =",
    )
    try:
        with psycopg.connect(_db_url()) as conn:
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
        if limit < len(skills):
            skills = skills[:limit]
            allowed = {s["tag"] for s in skills}
            trimmed_groups: list[dict[str, Any]] = []
            for group in groups:
                g_skills = [s for s in group.get("skills", []) if s.get("tag") in allowed]
                if g_skills:
                    trimmed_groups.append({**group, "skills": g_skills})
            groups = trimmed_groups
    except Exception as exc:
        logger.error("skills_catalog: %s", exc)
        raise HTTPException(status_code=500, detail="catalog error")
    return {"groups": groups, "skills": skills}


@app.get("/v1/feed")
def feed(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    min_score: int = Query(default=0, ge=0, le=100),
    skills: str = Query(default=""),
    category: str = Query(default=""),
    sort: str = Query(default="time"),
    authorization: str = Header(default="", alias="Authorization"),
) -> dict[str, Any]:
    """Лента: is_visible=true; anon/free → delay 15m; paid JWT → instant."""
    if sort not in ("time", "match"):
        raise HTTPException(status_code=400, detail="sort must be time or match")
    skill_list = _parse_skills_param(skills)
    category_list = parse_category_param(category)
    tag_weights = tags_as_weights(skill_list)
    apply_delay = True
    user_id = _try_user_from_bearer(authorization)
    if user_id:
        try:
            with psycopg.connect(_db_url()) as conn:
                with conn.cursor() as cur:
                    if _user_effective_access(cur, user_id):
                        apply_delay = False
        except Exception as exc:
            logger.warning("feed: effective_access check failed: %s", exc)
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                if sort == "match":
                    items, count = _feed_page_match(
                        cur,
                        limit=limit,
                        offset=offset,
                        min_score=min_score,
                        skills=skill_list,
                        categories=category_list,
                        tag_weights=tag_weights,
                        apply_delay=apply_delay,
                    )
                else:
                    items, count = _feed_page_time(
                        cur,
                        limit=limit,
                        offset=offset,
                        min_score=min_score,
                        skills=skill_list,
                        categories=category_list,
                        tag_weights=tag_weights,
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
        "sort": sort,
        "skills": skill_list,
        "category": category_list,
        "feed_delayed": apply_delay,
    }


# 3c3 ─────────────────────────────────────────────────────────────────────────


@app.get("/v1/leads/{lead_id}")
def get_lead(lead_id: int) -> dict[str, Any]:
    """Одна карточка лида по id."""
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT {_SELECT_COLS} FROM leads WHERE id = %s",
                    (lead_id,),
                )
                row = cur.fetchone()
    except Exception as exc:
        logger.error("get_lead %d: %s", lead_id, exc)
        raise HTTPException(status_code=500, detail="db error")
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    return _row_to_item(row)


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


@app.get("/v1/me/feed")
def me_feed(
    user_id: str = Depends(_resolve_user_id),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    min_score: int = Query(default=0, ge=0, le=100),
    min_match: int = Query(default=0, ge=0, le=100),
    skills: str = Query(default=""),
    category: str = Query(default=""),
    sort: str = Query(default="match"),
) -> dict[str, Any]:
    """Персональная лента: user_tags, is_visible=true; sort=time|match; min_match on keyword_match."""
    if sort not in ("time", "match"):
        raise HTTPException(status_code=400, detail="sort must be time or match")
    skill_list = _parse_skills_param(skills)
    category_list = parse_category_param(category)
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                items, count = _personal_feed_page(
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
    }


def _fetch_visible_lead(cur: Any, lead_id: int) -> tuple[Any, ...] | None:
    feed_where, feed_params = _feed_where_sql()
    cur.execute(
        f"SELECT {_SELECT_COLS} FROM leads WHERE id = %s AND {feed_where}",
        (lead_id, *feed_params),
    )
    return cur.fetchone()


def _parse_ai_reasons(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    return []


@app.post("/v1/me/leads/{lead_id}/draft")
def me_lead_draft(
    lead_id: int,
    user_id: str = Depends(_resolve_user_id),
) -> dict[str, Any]:
    """O23: on-demand L2 на /lenta/ → INSERT inbox (paid only)."""
    cfg = load_config()
    if not cfg.ai_active:
        raise HTTPException(status_code=503, detail="ai unavailable")

    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                if not _user_effective_access(cur, user_id):
                    raise HTTPException(status_code=403, detail="paid subscription required")

                row = _fetch_visible_lead(cur, lead_id)
                if row is None:
                    raise HTTPException(status_code=404, detail="not found")
                user_tags = _load_user_tags(cur, user_id)
                tags = _canonical_lead_tags(row[8])
                km = keyword_match(tags, user_tags)
                if km <= 0:
                    raise HTTPException(status_code=403, detail="no skill overlap")

                lite = AiLiteAnalysis(
                    verdict=(row[7] or "Сомнительно").strip(),
                    task_summary=(row[12] or "").strip() or (row[3] or "")[:400],
                    lead_tags=tuple(tags),
                    ai_reasons=tuple(_parse_ai_reasons(row[9])),
                )
                profile = build_cabinet_profile_excerpt(user_tags)
                premium = analyze_premium(
                    cfg,
                    title=row[2] or "",
                    budget_text=row[5] or "",
                    description=row[3] or "",
                    url=row[4] or "",
                    lite=lite,
                    profile_excerpt=profile,
                    log_prefix=f"lenta:draft:{lead_id}:",
                )
                if premium is None or not (premium.reply_draft or "").strip():
                    raise HTTPException(status_code=503, detail="draft generation failed")

                reply = premium.reply_draft.strip()
                tools = [str(t).strip() for t in premium.tools_required if str(t).strip()]
                tools_json = json.dumps(tools, ensure_ascii=False)
                cur.execute(
                    """
                    UPDATE leads
                    SET tools_required = %s::jsonb,
                        reply_draft = COALESCE(NULLIF(%s, ''), reply_draft)
                    WHERE id = %s
                    """,
                    (tools_json, reply, lead_id),
                )
                cur.execute(
                    """
                    INSERT INTO user_lead_replies (user_id, lead_id, reply_draft, deleted_at)
                    VALUES (%s::uuid, %s, %s, NULL)
                    ON CONFLICT (user_id, lead_id) DO UPDATE
                    SET reply_draft = EXCLUDED.reply_draft,
                        created_at = NOW(),
                        deleted_at = NULL
                    """,
                    (user_id, lead_id, reply),
                )
                conn.commit()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("me_lead_draft %d: %s", lead_id, exc)
        raise HTTPException(status_code=500, detail="db error") from exc

    return {
        "id": lead_id,
        "reply_draft": reply,
        "tools_required": tools,
        "keyword_match": km,
    }


@app.get("/v1/me/replies")
def me_replies(
    user_id: str = Depends(_resolve_user_id),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """Inbox откликов для /cabinet/ (без soft-deleted)."""
    feed_where, feed_params = _feed_where_sql(alias="l")
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
                      AND ulr.deleted_at IS NULL
                      AND {feed_where}
                    ORDER BY ulr.created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    (user_id, *feed_params, limit, offset),
                )
                rows = cur.fetchall()
                cur.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM user_lead_replies ulr
                    INNER JOIN leads l ON l.id = ulr.lead_id
                    WHERE ulr.user_id = %s::uuid
                      AND ulr.deleted_at IS NULL
                      AND {feed_where}
                    """,
                    (user_id, *feed_params),
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


def _ensure_subscription(cur: Any, user_id: str) -> tuple[str, bool, datetime | None, datetime | None]:
    cur.execute(
        """
        SELECT plan, is_active, active_until, paused_until
        FROM subscriptions
        WHERE user_id = %s::uuid
        """,
        (user_id,),
    )
    row = cur.fetchone()
    if row:
        return row[0], bool(row[1]), _as_utc(row[2]), _as_utc(row[3])

    cur.execute(
        """
        INSERT INTO subscriptions (user_id, plan, is_active)
        VALUES (%s::uuid, 'free', FALSE)
        ON CONFLICT (user_id) DO NOTHING
        RETURNING plan, is_active, active_until, paused_until
        """,
        (user_id,),
    )
    inserted = cur.fetchone()
    if inserted:
        return inserted[0], bool(inserted[1]), _as_utc(inserted[2]), _as_utc(inserted[3])

    cur.execute(
        """
        SELECT plan, is_active, active_until, paused_until
        FROM subscriptions
        WHERE user_id = %s::uuid
        """,
        (user_id,),
    )
    row = cur.fetchone()
    if not row:
        return "free", False, None, None
    return row[0], bool(row[1]), _as_utc(row[2]), _as_utc(row[3])


def _subscription_payload(
    plan: str,
    is_active: bool,
    active_until: datetime | None,
    paused_until: datetime | None,
) -> dict[str, Any]:
    now = _utc_now()
    paused = paused_until is not None and paused_until > now
    if paused_until is not None and paused_until <= now:
        paused_until = None

    paid_plan = plan not in ("free", "", "owner")
    expired = (
        paid_plan
        and is_active
        and active_until is not None
        and active_until <= now
    )

    if plan == "owner":
        status: Literal["free", "active", "paused", "expired", "beta"] = "beta"
    elif paused:
        status = "paused"
    elif expired:
        status = "expired"
    elif is_active:
        status = "active"
    else:
        status = "free"

    effective_access = status in ("active", "beta") and not paused

    plan_labels = {
        "owner": "ИИ-агент (владелец)",
        "agent": "ИИ-агент",
        "pro": "ИИ-агент",
        "free": "ИИ-агент",
    }

    return {
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


@app.get("/v1/me/subscription")
def me_subscription(user_id: str = Depends(_resolve_user_id)) -> dict[str, Any]:
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                plan, is_active, active_until, paused_until = _ensure_subscription(cur, user_id)
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
                return _subscription_payload(plan, is_active, active_until, paused_until)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("me_subscription: %s", exc)
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
                plan, is_active, active_until, paused_until = _ensure_subscription(cur, user_id)
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
                    return _subscription_payload(plan, is_active, active_until, None)

                if not is_active or plan in ("free", ""):
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
                return _subscription_payload(plan, is_active, active_until, until)
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
