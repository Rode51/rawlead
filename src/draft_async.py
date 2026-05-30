"""O56a/O57: async on-demand L2 draft — in-process worker + lead_draft_jobs."""

from __future__ import annotations

import logging
import re
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import psycopg

from config import Config
from match_push import (
    DraftError,
    DraftResult,
    generate_and_store_lead_draft,
    materialize_shared_draft_for_user,
)

logger = logging.getLogger(__name__)

_DRAFT_QUICK_WAIT_SEC = 3.0
_DRAFT_JOB_TTL_SEC = 600
_DRAFT_USER_FAIL = "ИИ временно недоступен — повторите"
_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|bearer\s+\S+|sk-[a-z0-9]{8,}|openrouter[_-]?api[_-]?key)\s*[:=]?\s*\S+"
)
_SQL_DIR = Path(__file__).resolve().parent.parent / "sql"

_tables_ready = False
_table_lock = threading.Lock()
_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="draft-job")
_jobs_lock = threading.Lock()
_active_futures: dict[int, Future[None]] = {}

DraftStatus = Literal["ready", "pending", "failed"]


@dataclass(frozen=True)
class DraftPollResponse:
    status: DraftStatus
    lead_id: int
    reply_draft: str = ""
    tools_required: list[str] | None = None
    keyword_match: int | None = None
    error: str = ""


def _ensure_draft_tables(database_url: str) -> None:
    global _tables_ready
    if _tables_ready:
        return
    with _table_lock:
        if _tables_ready:
            return
        for name in ("012_draft_jobs.sql", "013_lead_draft_jobs.sql"):
            sql_path = _SQL_DIR / name
            ddl = sql_path.read_text(encoding="utf-8") if sql_path.is_file() else ""
            if not ddl.strip():
                raise RuntimeError(f"missing sql/{name}")
            with psycopg.connect(database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(ddl)
                conn.commit()
        _tables_ready = True


def _fetch_saved_draft(cur: Any, user_id: str, lead_id: int) -> DraftResult | None:
    cur.execute(
        """
        SELECT ulr.reply_draft, l.tools_required, l.lead_tags
        FROM user_lead_replies ulr
        JOIN leads l ON l.id = ulr.lead_id
        WHERE ulr.user_id = %s::uuid AND ulr.lead_id = %s AND ulr.deleted_at IS NULL
        """,
        (user_id, lead_id),
    )
    row = cur.fetchone()
    if not row:
        return None
    draft = (row[0] or "").strip()
    if not draft:
        return None
    from match_push import _canonical_lead_tags, _load_user_tags, _parse_tools_required
    from rank import keyword_match

    user_tags = _load_user_tags(cur, user_id)
    tags = _canonical_lead_tags(row[2])
    km = keyword_match(tags, user_tags)
    tools = _parse_tools_required(row[1])
    return DraftResult(reply_draft=draft, tools_required=tools, keyword_match=km)


def _draft_to_poll(result: DraftResult, lead_id: int) -> DraftPollResponse:
    return DraftPollResponse(
        status="ready",
        lead_id=lead_id,
        reply_draft=result.reply_draft,
        tools_required=result.tools_required,
        keyword_match=result.keyword_match,
    )


def _try_materialize_shared(
    cfg: Config,
    *,
    user_id: str,
    lead_id: int,
    log_prefix: str,
) -> DraftPollResponse | None:
    result = materialize_shared_draft_for_user(
        cfg,
        user_id=user_id,
        lead_id=lead_id,
        log_prefix=log_prefix,
    )
    if result is None:
        return None
    return _draft_to_poll(result, lead_id)


def _read_lead_job(cur: Any, lead_id: int) -> tuple[str, str] | None:
    cur.execute(
        """
        SELECT status, COALESCE(error_msg, '')
        FROM lead_draft_jobs
        WHERE lead_id = %s
        """,
        (lead_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return str(row[0]), str(row[1] or "")


def _clear_stale_lead_pending(cur: Any, lead_id: int) -> None:
    cur.execute(
        """
        DELETE FROM lead_draft_jobs
        WHERE lead_id = %s
          AND status = 'pending'
          AND updated_at < NOW() - (%s || ' seconds')::interval
        """,
        (lead_id, str(_DRAFT_JOB_TTL_SEC)),
    )


def _set_lead_job_failed(cur: Any, lead_id: int, msg: str) -> None:
    cur.execute(
        """
        INSERT INTO lead_draft_jobs (lead_id, status, error_msg, updated_at)
        VALUES (%s, 'failed', %s, NOW())
        ON CONFLICT (lead_id) DO UPDATE
        SET status = 'failed', error_msg = EXCLUDED.error_msg, updated_at = NOW()
        """,
        (lead_id, msg[:500]),
    )


def _delete_lead_job(cur: Any, lead_id: int) -> None:
    cur.execute("DELETE FROM lead_draft_jobs WHERE lead_id = %s", (lead_id,))


def _insert_lead_pending(cur: Any, lead_id: int) -> bool:
    """Return True if this caller owns a new pending job."""
    cur.execute(
        """
        INSERT INTO lead_draft_jobs (lead_id, status, error_msg)
        VALUES (%s, 'pending', NULL)
        ON CONFLICT (lead_id) DO NOTHING
        RETURNING lead_id
        """,
        (lead_id,),
    )
    return cur.fetchone() is not None


def sanitize_draft_error_detail(raw: str) -> str:
    """O59a: user-visible hint from ai_errors — no secrets, not only generic."""
    s = (raw or "").strip()
    if not s or s == "draft generation failed":
        return _DRAFT_USER_FAIL
    low = s.lower()
    if "timeout" in low or "timed out" in low:
        return "ИИ не успел ответить — повторите"
    if "429" in s or "rate limit" in low or "rate_limit" in low:
        return "ИИ перегружен — повторите через минуту"
    if "json" in low or "parse" in low or "invalid" in low:
        return "ИИ вернул некорректный ответ — повторите"
    if "402" in s or "insufficient" in low or "credit" in low or "balance" in low:
        return "ИИ временно недоступен — повторите"
    first = s.split(";")[0].strip()
    first = _SECRET_RE.sub("[redacted]", first)
    if len(first) > 120:
        first = first[:117] + "…"
    return first if len(first) > 8 else _DRAFT_USER_FAIL


def _user_facing_error(exc: DraftError) -> str:
    if exc.code == "ai_fail":
        return sanitize_draft_error_detail(exc.detail)
    if exc.code == "ai_unavailable":
        return _DRAFT_USER_FAIL
    if exc.code == "rate_limit":
        from src.draft_limits import draft_hourly_limit

        lim = draft_hourly_limit()
        if lim <= 0:
            return _DRAFT_USER_FAIL
        return f"Лимит: не больше {lim} черновиков в час"
    if exc.code == "forbidden":
        return exc.detail or "Нет доступа"
    if exc.code == "not_found":
        return "Заказ не найден"
    return _DRAFT_USER_FAIL


def _poll_error_from_stored(stored: str) -> str:
    return sanitize_draft_error_detail(stored) if stored.strip() else _DRAFT_USER_FAIL


def _run_generation(cfg: Config, user_id: str, lead_id: int, log_prefix: str) -> None:
    try:
        generate_and_store_lead_draft(
            cfg,
            user_id=user_id,
            lead_id=lead_id,
            log_prefix=log_prefix,
            max_retries=4,
            enforce_rate_limit=False,
        )
        with psycopg.connect(cfg.database_url) as conn:
            with conn.cursor() as cur:
                _delete_lead_job(cur, lead_id)
            conn.commit()
    except DraftError as exc:
        raw = exc.detail if exc.code == "ai_fail" else ""
        stored = raw or _user_facing_error(exc)
        from ai_analyze import note_ai_error, note_draft_request

        note_draft_request(False)
        note_ai_error(raw or exc.detail or exc.code)
        logger.warning(
            "%sfail code=%s detail=%s",
            log_prefix,
            exc.code,
            raw or exc.detail,
        )
        with psycopg.connect(cfg.database_url) as conn:
            with conn.cursor() as cur:
                _set_lead_job_failed(cur, lead_id, stored)
            conn.commit()
    except Exception as exc:
        logger.error("%serror %s", log_prefix, exc)
        with psycopg.connect(cfg.database_url) as conn:
            with conn.cursor() as cur:
                _set_lead_job_failed(cur, lead_id, _DRAFT_USER_FAIL)
            conn.commit()
    finally:
        with _jobs_lock:
            _active_futures.pop(lead_id, None)


def _start_worker(cfg: Config, user_id: str, lead_id: int, log_prefix: str) -> None:
    with _jobs_lock:
        fut = _active_futures.get(lead_id)
        if fut is not None and not fut.done():
            return
        fut = _pool.submit(_run_generation, cfg, user_id, lead_id, log_prefix)
        _active_futures[lead_id] = fut


def poll_draft(
    cfg: Config,
    *,
    user_id: str,
    lead_id: int,
    log_prefix: str = "",
) -> DraftPollResponse:
    """GET / draft — current status without starting work."""
    if not cfg.database_url.strip():
        return DraftPollResponse(status="failed", lead_id=lead_id, error=_DRAFT_USER_FAIL)
    _ensure_draft_tables(cfg.database_url)
    prefix = log_prefix or f"lenta:draft:{lead_id}:"

    with psycopg.connect(cfg.database_url) as conn:
        with conn.cursor() as cur:
            saved = _fetch_saved_draft(cur, user_id, lead_id)
            if saved:
                return _draft_to_poll(saved, lead_id)
        conn.commit()

    materialized = _try_materialize_shared(
        cfg, user_id=user_id, lead_id=lead_id, log_prefix=prefix
    )
    if materialized:
        with psycopg.connect(cfg.database_url) as conn:
            with conn.cursor() as cur:
                _delete_lead_job(cur, lead_id)
            conn.commit()
        return materialized

    with psycopg.connect(cfg.database_url) as conn:
        with conn.cursor() as cur:
            _clear_stale_lead_pending(cur, lead_id)
            job = _read_lead_job(cur, lead_id)
        conn.commit()

    if not job:
        return DraftPollResponse(status="failed", lead_id=lead_id, error="Черновик ещё не запущен")

    status, err = job
    if status == "pending":
        return DraftPollResponse(status="pending", lead_id=lead_id)
    return DraftPollResponse(
        status="failed",
        lead_id=lead_id,
        error=_poll_error_from_stored(err),
    )


def submit_draft(
    cfg: Config,
    *,
    user_id: str,
    lead_id: int,
    log_prefix: str = "",
    quick_wait_sec: float = _DRAFT_QUICK_WAIT_SEC,
) -> DraftPollResponse:
    """POST / draft — idempotent start + optional quick wait."""
    if not cfg.ai_active:
        raise DraftError("ai_unavailable")
    if not cfg.database_url.strip():
        raise DraftError("ai_unavailable")

    _ensure_draft_tables(cfg.database_url)
    prefix = log_prefix or f"lenta:draft:{lead_id}:"

    with psycopg.connect(cfg.database_url) as conn:
        with conn.cursor() as cur:
            saved = _fetch_saved_draft(cur, user_id, lead_id)
            if saved:
                _delete_lead_job(cur, lead_id)
                conn.commit()
                return _draft_to_poll(saved, lead_id)
        conn.commit()

    materialized = _try_materialize_shared(
        cfg, user_id=user_id, lead_id=lead_id, log_prefix=prefix
    )
    if materialized:
        with psycopg.connect(cfg.database_url) as conn:
            with conn.cursor() as cur:
                _delete_lead_job(cur, lead_id)
            conn.commit()
        return materialized

    with psycopg.connect(cfg.database_url) as conn:
        with conn.cursor() as cur:
            _clear_stale_lead_pending(cur, lead_id)
            job = _read_lead_job(cur, lead_id)
            if job and job[0] == "failed":
                _delete_lead_job(cur, lead_id)
                job = None

            if job and job[0] == "pending":
                conn.commit()
                _start_worker(cfg, user_id, lead_id, prefix)
            else:
                owned = _insert_lead_pending(cur, lead_id)
                conn.commit()
                if owned:
                    _start_worker(cfg, user_id, lead_id, prefix)
                else:
                    _start_worker(cfg, user_id, lead_id, prefix)

    deadline = time.monotonic() + max(0.0, quick_wait_sec)
    while time.monotonic() < deadline:
        resp = poll_draft(cfg, user_id=user_id, lead_id=lead_id, log_prefix=prefix)
        if resp.status != "pending":
            return resp
        time.sleep(0.35)

    return DraftPollResponse(status="pending", lead_id=lead_id)


def draft_response_body(resp: DraftPollResponse) -> dict[str, Any]:
    body: dict[str, Any] = {"status": resp.status, "lead_id": resp.lead_id, "id": resp.lead_id}
    if resp.status == "ready":
        body["reply_draft"] = resp.reply_draft
        body["tools_required"] = resp.tools_required or []
        if resp.keyword_match is not None:
            body["keyword_match"] = resp.keyword_match
    if resp.status == "failed":
        body["error"] = resp.error or _DRAFT_USER_FAIL
        body["detail"] = body["error"]
    return body
