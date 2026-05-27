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
from typing import Any
from uuid import UUID, uuid4

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from src.config import load_radar_env

from src.lead_category import (
    build_skills_groups,
    category_for_listing,
    effective_feed_min_score,
    normalize_category,
    parse_category_param,
    passes_score_filter,
    resolve_lead_category,
)
from src.public_feed import is_public_feed_source, public_feed_source_sql
from src.jwt_auth import decode_access_token, issue_access_token
from src.rank import (
    final_rank,
    keyword_match,
    normalize_tags,
    open_rank,
    parse_lead_tags,
    tags_as_weights,
)
from src.telegram_login import login_bot_token, verify_telegram_login

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
_BOT_FEED_WHERE = "is_visible = TRUE"


def _feed_where_sql() -> tuple[str, list[str]]:
    src_sql, src_params = public_feed_source_sql()
    return _BOT_FEED_WHERE + src_sql, src_params


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
    tags = parse_lead_tags(lead_tags)
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
        "ai_reasons": ai_reasons if ai_reasons is not None else [],
        "final_rank": fr,
        "keyword_match": km,
        "category": category,
        "created_at": created_at.isoformat() if created_at else None,
        "tools_required": tools,
        "reply_draft": (reply_draft or "").strip(),
    }


_SELECT_COLS = """
    id, source, title, body, url, budget_text,
    ai_score, ai_verdict, lead_tags, ai_reasons, created_at, category,
    task_summary, tools_required, reply_draft
"""


def _category_sql(categories: list[str]) -> tuple[str, list[Any]]:
    if not categories:
        return "", []
    return " AND category = ANY(%s::text[])", [categories]


def _load_user_tags(cur: Any, user_id: str) -> dict[str, float]:
    cur.execute(
        "SELECT tag, weight FROM user_tags WHERE user_id = %s::uuid ORDER BY tag",
        (user_id,),
    )
    return {row[0]: float(row[1]) for row in cur.fetchall()}


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


def _rank_feed_rows(
    rows: list[tuple[Any, ...]],
    tag_weights: dict[str, float],
    *,
    min_score: int,
    sort: str,
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for row in rows:
        tags = parse_lead_tags(row[8])
        category = resolve_lead_category(row[11], row[2] or "", row[3] or "", tags)
        km = keyword_match(tags, tag_weights) if tag_weights else 0
        fr = final_rank(row[6], km)
        score_for_filter = fr if sort == "match" else (row[6] or 0)
        if not passes_score_filter(int(score_for_filter), min_score, category):
            continue
        ranked.append(_row_to_item(row, keyword_match_val=km, final_rank_val=fr))
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
) -> tuple[list[dict[str, Any]], int]:
    extra, extra_params = _skills_sql(skills)
    cat_sql, cat_params = _category_sql(categories)
    sql_min = min_score
    if min_score >= 70:
        sql_min = effective_feed_min_score(min_score, "text")
    feed_where, feed_params = _feed_where_sql()
    cur.execute(
        f"""
        SELECT {_SELECT_COLS}
        FROM leads
        WHERE {feed_where}
          AND (ai_score IS NULL OR ai_score >= %s)
          {extra}{cat_sql}
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """,
        (*feed_params, sql_min, *extra_params, *cat_params, limit, offset),
    )
    rows = cur.fetchall()
    items: list[dict[str, Any]] = []
    for r in rows:
        tags = parse_lead_tags(r[8])
        category = resolve_lead_category(r[11], r[2] or "", r[3] or "", tags)
        km = keyword_match(tags, tag_weights) if tag_weights else 0
        fr = final_rank(r[6], km)
        score_for_filter = r[6] or 0
        if not passes_score_filter(int(score_for_filter), min_score, category):
            continue
        items.append(_row_to_item(r, keyword_match_val=km, final_rank_val=fr))
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
) -> tuple[list[dict[str, Any]], int]:
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
    ranked = _rank_feed_rows(
        cur.fetchall(),
        tag_weights,
        min_score=min_score,
        sort="match",
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
            tags = parse_lead_tags(row[8])
            category = resolve_lead_category(row[11], row[2] or "", row[3] or "", tags)
            km = keyword_match(tags, user_tags)
            fr = final_rank(row[6], km)
            if not passes_score_filter(row[6], min_score, category):
                continue
            ranked.append(_row_to_item(row, keyword_match_val=km, final_rank_val=fr))
        ranked.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    else:
        ranked = _rank_feed_rows(rows, user_tags, min_score=min_score, sort="match")
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
        INSERT INTO subscriptions (user_id, plan)
        VALUES (%s::uuid, 'free')
        ON CONFLICT (user_id) DO NOTHING
        """,
        (user_id,),
    )
    return user_id


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
    }


# 3c1 ─────────────────────────────────────────────────────────────────────────


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": _VERSION}


# 3c2 ─────────────────────────────────────────────────────────────────────────


@app.get("/v1/skills/catalog")
def skills_catalog(
    limit: int = Query(default=_SKILLS_CATALOG_LIMIT, ge=1, le=100),
    category: str = Query(default=""),
) -> dict[str, Any]:
    """Топ навыков из lead_tags лидов, уже ушедших в бот."""
    category_list = parse_category_param(category)
    try:
        feed_where, feed_params = _feed_where_sql()
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT tag, COUNT(*) AS cnt
                    FROM leads,
                         jsonb_array_elements_text(lead_tags) AS tag
                    WHERE {feed_where}
                    GROUP BY tag
                    ORDER BY cnt DESC, tag ASC
                    LIMIT %s
                    """,
                    (*feed_params, limit),
                )
                rows = cur.fetchall()
                groups, skills = build_skills_groups(rows, categories=category_list)
    except Exception as exc:
        logger.error("skills_catalog: %s", exc)
        raise HTTPException(status_code=500, detail="db error")
    return {"groups": groups, "skills": skills}


@app.get("/v1/feed")
def feed(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    min_score: int = Query(default=0, ge=0, le=100),
    skills: str = Query(default=""),
    category: str = Query(default=""),
    sort: str = Query(default="time"),
) -> dict[str, Any]:
    """Лента: is_visible=true; skills → rank; sort=time|match."""
    if sort not in ("time", "match"):
        raise HTTPException(status_code=400, detail="sort must be time or match")
    skill_list = _parse_skills_param(skills)
    category_list = parse_category_param(category)
    tag_weights = tags_as_weights(skill_list)
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
                tags = [r[0] for r in cur.fetchall()]
    except Exception as exc:
        logger.error("me_tags: %s", exc)
        raise HTTPException(status_code=500, detail="db error")
    return {"tags": tags}


@app.put("/v1/me/tags")
def me_tags_put(
    payload: TagsPayload,
    user_id: str = Depends(_resolve_user_id),
) -> dict[str, Any]:
    tags = normalize_tags(payload.tags)
    try:
        with psycopg.connect(_db_url()) as conn:
            with conn.cursor() as cur:
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
    skills: str = Query(default=""),
    category: str = Query(default=""),
    sort: str = Query(default="match"),
) -> dict[str, Any]:
    """Персональная лента: user_tags, is_visible=true; sort=time|match."""
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
        "skills": skill_list,
        "category": category_list,
    }


@app.get("/v1/me/subscription")
def me_subscription(user_id: str = Depends(_resolve_user_id)) -> dict[str, Any]:
    _ = user_id
    return {"plan": "free", "active_until": None}


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
