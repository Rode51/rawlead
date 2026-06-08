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
from draft_trace import DraftTimer, log_draft_stage
from match_push import (
    DraftError,
    DraftResult,
    _fetch_lead_row,
    _fetch_saved_draft as _fetch_user_reply_draft,
    _user_effective_access,
    generate_and_store_lead_draft,
    materialize_shared_draft_for_user,
    warm_rate_limit_retry_after,
    warm_shared_lead_draft,
)

logger = logging.getLogger(__name__)

_DRAFT_QUICK_WAIT_SEC = 3.0
_DRAFT_JOB_TTL_SEC = 600
_WARM_USER_KEY = "__warm__"
_DRAFT_USER_FAIL = "ИИ временно недоступен — повторите"
_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|bearer\s+\S+|sk-[a-z0-9]{8,}|openrouter[_-]?api[_-]?key)\s*[:=]?\s*\S+"
)
_SQL_DIR = Path(__file__).resolve().parent.parent / "sql"

_tables_ready = False
_table_lock = threading.Lock()
_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="draft-job")
_jobs_lock = threading.Lock()
_active_futures: dict[tuple[str, int], Future[None]] = {}
_job_errors: dict[tuple[str, int], str] = {}

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


def _poll_error_from_stored(stored: str | None) -> str:
    msg = (stored or "").strip()
    return sanitize_draft_error_detail(msg) if msg else _DRAFT_USER_FAIL


def _worker_running(key: tuple[str, int]) -> bool:
    with _jobs_lock:
        fut = _active_futures.get(key)
        return fut is not None and not fut.done()


def _lead_worker_running(lead_id: int) -> bool:
    with _jobs_lock:
        for key, fut in _active_futures.items():
            if key[1] == lead_id and fut is not None and not fut.done():
                return True
    return False


def _restart_worker(cfg: Config, user_id: str, lead_id: int, log_prefix: str) -> None:
    key = (user_id, lead_id)
    with _jobs_lock:
        _job_errors.pop(key, None)
    logger.info("draft:restart lead=%s", lead_id)
    _start_worker(cfg, user_id, lead_id, log_prefix)


def _run_generation(cfg: Config, user_id: str, lead_id: int, log_prefix: str) -> None:
    key = (user_id, lead_id)
    trace = DraftTimer()
    log_draft_stage(
        log_prefix,
        stage="worker_start",
        timer=trace,
        lead_id=lead_id,
        user_id=user_id[:8],
    )
    try:
        generate_and_store_lead_draft(
            cfg,
            user_id=user_id,
            lead_id=lead_id,
            log_prefix=log_prefix,
            max_retries=2,
            enforce_rate_limit=False,
        )
        with psycopg.connect(cfg.database_url) as conn:
            with conn.cursor() as cur:
                _delete_lead_job(cur, lead_id)
            conn.commit()
        with _jobs_lock:
            _job_errors.pop(key, None)
        log_draft_stage(
            log_prefix,
            stage="worker_ok",
            timer=trace,
            lead_id=lead_id,
            user_id=user_id[:8],
        )
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
        with _jobs_lock:
            _job_errors[key] = stored
        log_draft_stage(
            log_prefix,
            stage="worker_fail",
            timer=trace,
            lead_id=lead_id,
            code=exc.code,
            user_id=user_id[:8],
        )
    except Exception as exc:
        logger.error("%serror %s", log_prefix, exc)
        with psycopg.connect(cfg.database_url) as conn:
            with conn.cursor() as cur:
                _set_lead_job_failed(cur, lead_id, _DRAFT_USER_FAIL)
            conn.commit()
        with _jobs_lock:
            _job_errors[key] = _DRAFT_USER_FAIL
        log_draft_stage(
            log_prefix,
            stage="worker_error",
            timer=trace,
            lead_id=lead_id,
            user_id=user_id[:8],
        )
    finally:
        with _jobs_lock:
            _active_futures.pop(key, None)
        ms = trace.elapsed_ms()
        logger.info("draft:worker_done lead=%s ms=%s", lead_id, ms)


def _start_worker(cfg: Config, user_id: str, lead_id: int, log_prefix: str) -> None:
    if _lead_worker_running(lead_id):
        return
    key = (user_id, lead_id)
    with _jobs_lock:
        fut = _active_futures.get(key)
        if fut is not None and not fut.done():
            return
        fut = _pool.submit(_run_generation, cfg, user_id, lead_id, log_prefix)
        _active_futures[key] = fut


def _run_warm_generation(cfg: Config, lead_id: int, log_prefix: str) -> None:
    key = (_WARM_USER_KEY, lead_id)
    trace = DraftTimer()
    log_draft_stage(
        log_prefix,
        stage="worker_start",
        timer=trace,
        lead_id=lead_id,
        path="warm",
    )
    try:
        warm_shared_lead_draft(cfg, lead_id=lead_id, log_prefix=log_prefix)
        with psycopg.connect(cfg.database_url) as conn:
            with conn.cursor() as cur:
                _delete_lead_job(cur, lead_id)
            conn.commit()
        with _jobs_lock:
            _job_errors.pop(key, None)
        log_draft_stage(
            log_prefix,
            stage="worker_ok",
            timer=trace,
            lead_id=lead_id,
            path="warm",
        )
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
        with _jobs_lock:
            _job_errors[key] = stored
        log_draft_stage(
            log_prefix,
            stage="worker_fail",
            timer=trace,
            lead_id=lead_id,
            code=exc.code,
            path="warm",
        )
    except Exception as exc:
        logger.error("%serror %s", log_prefix, exc)
        with psycopg.connect(cfg.database_url) as conn:
            with conn.cursor() as cur:
                _set_lead_job_failed(cur, lead_id, _DRAFT_USER_FAIL)
            conn.commit()
        with _jobs_lock:
            _job_errors[key] = _DRAFT_USER_FAIL
    finally:
        with _jobs_lock:
            _active_futures.pop(key, None)
        ms = trace.elapsed_ms()
        logger.info("draft:warm_done lead=%s ms=%s", lead_id, ms)


def _start_warm_worker(cfg: Config, lead_id: int, log_prefix: str) -> None:
    if _lead_worker_running(lead_id):
        return
    key = (_WARM_USER_KEY, lead_id)
    with _jobs_lock:
        fut = _active_futures.get(key)
        if fut is not None and not fut.done():
            return
        fut = _pool.submit(_run_warm_generation, cfg, lead_id, log_prefix)
        _active_futures[key] = fut


def submit_warm(
    cfg: Config,
    *,
    user_id: str,
    lead_id: int,
    log_prefix: str = "",
) -> DraftPollResponse:
    """POST /draft/warm — shared L2 pre-warm on premium expand."""
    if not cfg.ai_active:
        raise DraftError("ai_unavailable")
    if not cfg.database_url.strip():
        raise DraftError("ai_unavailable")

    prefix = log_prefix or f"lenta:draft:warm:{lead_id}:"
    trace = DraftTimer()
    log_draft_stage(
        prefix,
        stage="submit",
        timer=trace,
        lead_id=lead_id,
        path="warm",
        user_id=user_id[:8],
    )

    _ensure_draft_tables(cfg.database_url)
    with psycopg.connect(cfg.database_url) as conn:
        with conn.cursor() as cur:
            if not _user_effective_access(cur, user_id):
                raise DraftError("forbidden", "paid subscription required")
            if _fetch_user_reply_draft(cur, user_id, lead_id):
                log_draft_stage(
                    prefix,
                    stage="submit_done",
                    timer=trace,
                    lead_id=lead_id,
                    status="ready",
                    path="user_cache",
                    user_id=user_id[:8],
                )
                return DraftPollResponse(status="ready", lead_id=lead_id)
            row = _fetch_lead_row(cur, lead_id)
            if row is None:
                raise DraftError("not_found")
            if (row[14] or "").strip():
                log_draft_stage(
                    prefix,
                    stage="submit_done",
                    timer=trace,
                    lead_id=lead_id,
                    status="ready",
                    path="shared_cache",
                    user_id=user_id[:8],
                )
                return DraftPollResponse(status="ready", lead_id=lead_id)
        conn.commit()

    retry_after = warm_rate_limit_retry_after(user_id, consume=False)
    if retry_after is not None:
        from draft_limits import draft_warm_hourly_cap

        lim = draft_warm_hourly_cap()
        raise DraftError("rate_limit", f"warm cap {lim}/hour")

    with psycopg.connect(cfg.database_url) as conn:
        with conn.cursor() as cur:
            _clear_stale_lead_pending(cur, lead_id)
            job = _read_lead_job(cur, lead_id)
            if job and job[0] == "failed":
                _delete_lead_job(cur, lead_id)
            if job is None or (job and job[0] == "failed"):
                _insert_lead_pending(cur, lead_id)
            conn.commit()

    warm_rate_limit_retry_after(user_id, consume=True)
    if not _worker_running((_WARM_USER_KEY, lead_id)) and not _lead_worker_running(lead_id):
        log_draft_stage(
            prefix,
            stage="worker_queue",
            timer=trace,
            lead_id=lead_id,
            path="warm",
            user_id=user_id[:8],
        )
        _start_warm_worker(cfg, lead_id, prefix)

    log_draft_stage(
        prefix,
        stage="submit_done",
        timer=trace,
        lead_id=lead_id,
        status="pending",
        path="warm",
        user_id=user_id[:8],
    )
    return DraftPollResponse(status="pending", lead_id=lead_id)


def poll_draft(
    cfg: Config,
    *,
    user_id: str,
    lead_id: int,
    log_prefix: str = "",
) -> DraftPollResponse:
    """GET / draft — current status; O135: restart worker if job pending but process lost."""
    if not cfg.database_url.strip():
        return DraftPollResponse(status="failed", lead_id=lead_id, error=_DRAFT_USER_FAIL)
    prefix = log_prefix or f"lenta:draft:{lead_id}:"
    key = (user_id, lead_id)

    _ensure_draft_tables(cfg.database_url)
    job: tuple[str, str] | None = None
    with psycopg.connect(cfg.database_url) as conn:
        with conn.cursor() as cur:
            saved = _fetch_saved_draft(cur, user_id, lead_id)
            if saved:
                trace = DraftTimer()
                log_draft_stage(
                    prefix,
                    stage="poll_ready",
                    timer=trace,
                    lead_id=lead_id,
                    path="cache",
                    user_id=user_id[:8],
                )
                return _draft_to_poll(saved, lead_id)
            _clear_stale_lead_pending(cur, lead_id)
            job = _read_lead_job(cur, lead_id)
        conn.commit()

    with _jobs_lock:
        fut = _active_futures.get(key)
        if fut is not None and not fut.done():
            return DraftPollResponse(status="pending", lead_id=lead_id)
        err = _job_errors.get(key, "")

    if err:
        trace = DraftTimer()
        log_draft_stage(
            prefix,
            stage="poll_failed",
            timer=trace,
            lead_id=lead_id,
            source="memory",
            user_id=user_id[:8],
        )
        return DraftPollResponse(
            status="failed",
            lead_id=lead_id,
            error=_poll_error_from_stored(err),
        )

    if job:
        status, stored_err = job
        if status == "failed":
            trace = DraftTimer()
            log_draft_stage(
                prefix,
                stage="poll_failed",
                timer=trace,
                lead_id=lead_id,
                source="db",
                user_id=user_id[:8],
            )
            return DraftPollResponse(
                status="failed",
                lead_id=lead_id,
                error=_poll_error_from_stored(stored_err),
            )
        if status == "pending" and not _worker_running(key):
            trace = DraftTimer()
            log_draft_stage(
                prefix,
                stage="poll_restart",
                timer=trace,
                lead_id=lead_id,
                user_id=user_id[:8],
            )
            _restart_worker(cfg, user_id, lead_id, prefix)
        return DraftPollResponse(status="pending", lead_id=lead_id)

    trace = DraftTimer()
    log_draft_stage(
        prefix,
        stage="poll_restart",
        timer=trace,
        lead_id=lead_id,
        reason="no_job",
        user_id=user_id[:8],
    )
    _restart_worker(cfg, user_id, lead_id, prefix)
    return DraftPollResponse(status="pending", lead_id=lead_id)


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

    prefix = log_prefix or f"lenta:draft:{lead_id}:"
    key = (user_id, lead_id)

    trace = DraftTimer()
    log_draft_stage(
        prefix,
        stage="submit",
        timer=trace,
        lead_id=lead_id,
        user_id=user_id[:8],
    )

    _ensure_draft_tables(cfg.database_url)
    with psycopg.connect(cfg.database_url) as conn:
        with conn.cursor() as cur:
            saved = _fetch_saved_draft(cur, user_id, lead_id)
            if saved:
                _delete_lead_job(cur, lead_id)
                conn.commit()
                log_draft_stage(
                    prefix,
                    stage="submit_done",
                    timer=trace,
                    lead_id=lead_id,
                    status="ready",
                    path="cache",
                    user_id=user_id[:8],
                )
                return _draft_to_poll(saved, lead_id)

            _clear_stale_lead_pending(cur, lead_id)
            job = _read_lead_job(cur, lead_id)
            if job and job[0] == "failed":
                _delete_lead_job(cur, lead_id)
            if job is None or (job and job[0] == "failed"):
                _insert_lead_pending(cur, lead_id)
            conn.commit()

    if not _worker_running(key):
        log_draft_stage(
            prefix,
            stage="worker_queue",
            timer=trace,
            lead_id=lead_id,
            user_id=user_id[:8],
        )
        _restart_worker(cfg, user_id, lead_id, prefix)

    deadline = time.monotonic() + max(0.0, quick_wait_sec)
    while time.monotonic() < deadline:
        resp = poll_draft(cfg, user_id=user_id, lead_id=lead_id, log_prefix=prefix)
        if resp.status != "pending":
            log_draft_stage(
                prefix,
                stage="submit_done",
                timer=trace,
                lead_id=lead_id,
                status=resp.status,
                user_id=user_id[:8],
            )
            return resp
        time.sleep(0.35)

    log_draft_stage(
        prefix,
        stage="submit_done",
        timer=trace,
        lead_id=lead_id,
        status="pending",
        user_id=user_id[:8],
    )
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
