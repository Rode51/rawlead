"""MATCH_PUSH (O30/O50): уведомления подписчикам @rawlead_bot — per-user threshold."""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from collections import defaultdict, deque
from urllib.parse import urlparse, urlunparse
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import psycopg
import requests

from ai_analyze import (
    AiLiteAnalysis,
    rephrase_reply_draft_per_user,
    analyze_shared_reply_draft,
    note_draft_request,
)
from config import Config, telegram_requests_proxies
from lead_category import CATEGORIES, resolve_lead_category
from public_feed import feed_visibility_where_sql
from radar_cycle_log import SOURCE_LABELS, log_pipeline_line
from rank import (
    compatibility_match,
    effective_user_tag_weights,
    keyword_match,
    parse_lead_tags,
    user_quiz_niches_from_tags,
)
from reply_draft_strip import strip_reply_draft_price_deadline, strip_tg_draft_price_deadline
from draft_limits import draft_hourly_limit, draft_warm_hourly_cap
from skills_catalog import lead_tags_for_feed
from tools_catalog import normalize_tools_required, tools_from_tz_text
from tg_proxy_pool import tg_http_request

logger = logging.getLogger(__name__)

_LENTA_BASE = "https://rawlead.ru/lenta/"


def _lenta_lead_url(lead_id: int) -> str:
    return f"{_LENTA_BASE}?lead={int(lead_id)}"


def _uid8(user_id: Any) -> str:
    """Log-safe first 8 chars (psycopg may return uuid.UUID)."""
    return str(user_id)[:8]


def _match_push_debug() -> bool:
    raw = os.environ.get("MATCH_PUSH_DEBUG", "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def _log_push_line(log_path: Any, line: str, err: list[str]) -> None:
    err.append(line)
    log_pipeline_line(log_path, line)


def _tg_api_fail_detail(resp: requests.Response) -> str:
    if resp.status_code != 200:
        return f"HTTP {resp.status_code}"
    try:
        body = resp.json()
    except ValueError:
        return f"HTTP {resp.status_code} non-json"
    if body.get("ok"):
        return ""
    desc = str(body.get("description") or "not_ok")[:120]
    return f"HTTP {resp.status_code} {desc}"
_CABINET_URL = "https://rawlead.ru/cabinet/"
_PUSH_MIN_MATCH_DEFAULT = 60
_DRAFT_CALLBACK_RE = re.compile(r"^draft:(\d+)$")
_NOPE_CALLBACK_RE = re.compile(r"^nope:(\d+)$")
_DRAFT_WINDOW_SEC = 3600
_ONDEMAND_L2_SEM = threading.Semaphore(2)
_ONDEMAND_L2_BACKOFF_SEC = (0.5, 1)
_draft_attempts: dict[str, deque[float]] = defaultdict(deque)
_warm_attempts: dict[str, deque[float]] = defaultdict(deque)
_draft_lock = threading.Lock()

_LEAD_SELECT_COLS = """
    id, source, title, body, url, budget_text,
    ai_score, ai_verdict, lead_tags, ai_reasons, created_at, category,
    task_summary, tools_required, reply_draft
"""


class DraftError(Exception):
    """On-demand draft (lenta / TG callback)."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail or code
        super().__init__(self.detail)


@dataclass(frozen=True)
class DraftResult:
    reply_draft: str
    tools_required: list[str]
    keyword_match: int


def _prune_draft_window(q: deque[float], now: float) -> None:
    cutoff = now - _DRAFT_WINDOW_SEC
    while q and q[0] < cutoff:
        q.popleft()


def preprod_e2e_user_ids() -> frozenset[str]:
    """UUIDs allowed to reset in-memory draft quota (E2E gate). Public acc1 in PREPROD_ACCOUNTS.md."""
    raw = os.environ.get("PREPROD_E2E_USER_IDS", "").strip()
    if raw:
        return frozenset(x.strip() for x in raw.split(",") if x.strip())
    return frozenset({"7a83dbd8-ab41-4350-a183-38370d5b5c1c"})


def reset_draft_quota_for_user(user_id: str) -> dict[str, int]:
    """Clear rolling draft + warm counters for E2E (in-memory only)."""
    with _draft_lock:
        _draft_attempts.pop(user_id, None)
    _warm_attempts.pop(user_id, None)
    return draft_quota_for_user(user_id)


def draft_quota_for_user(user_id: str) -> dict[str, int]:
    """O247: rolling 1h draft quota snapshot (read-only)."""
    limit = draft_hourly_limit()
    if limit <= 0:
        return {
            "draft_hourly_limit": 0,
            "draft_used": 0,
            "draft_remaining": 0,
            "draft_retry_after_sec": 0,
        }
    with _draft_lock:
        now = time.time()
        q = _draft_attempts[user_id]
        _prune_draft_window(q, now)
        used = len(q)
        remaining = max(0, limit - used)
        retry = 0
        if remaining <= 0 and q:
            retry = max(1, int(_DRAFT_WINDOW_SEC - (now - q[0])))
        return {
            "draft_hourly_limit": limit,
            "draft_used": used,
            "draft_remaining": remaining,
            "draft_retry_after_sec": retry,
        }


def draft_rate_limit_retry_after(user_id: str) -> int | None:
    """O48/O60b: DRAFT_HOURLY_LIMIT per user; 0 = без лимита."""
    limit = draft_hourly_limit()
    if limit <= 0:
        return None
    with _draft_lock:
        now = time.time()
        q = _draft_attempts[user_id]
        _prune_draft_window(q, now)
        if len(q) >= limit:
            return max(1, int(_DRAFT_WINDOW_SEC - (now - q[0])))
        q.append(now)
        return None


def warm_rate_limit_retry_after(user_id: str, *, consume: bool = True) -> int | None:
    """O148: DRAFT_WARM_HOURLY_CAP per user on expand pre-warm."""
    cap = draft_warm_hourly_cap()
    if cap <= 0:
        return None
    now = time.time()
    q = _warm_attempts[user_id]
    cutoff = now - _DRAFT_WINDOW_SEC
    while q and q[0] < cutoff:
        q.popleft()
    if len(q) >= cap:
        return max(1, int(_DRAFT_WINDOW_SEC - (now - q[0])))
    if consume:
        q.append(now)
    return None


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


def merge_chat_id_on_login(cur: Any, *, tg_user_id: int, tg_chat_id: int | None = None) -> None:
    """Login Widget / auth: сохранить chat_id (private chat id == user id)."""
    chat = tg_chat_id if tg_chat_id is not None else tg_user_id
    cur.execute(
        """
        UPDATE users
        SET tg_chat_id = COALESCE(tg_chat_id, %s)
        WHERE tg_user_id = %s
        """,
        (chat, tg_user_id),
    )


def _user_push_eligible(
    plan: str,
    is_active: bool,
    paused_until: datetime | None,
    now: datetime,
    *,
    active_until: datetime | None = None,
) -> bool:
    if paused_until is not None and paused_until > now:
        return False
    if plan == "owner":
        return True
    au = active_until
    if au is not None and au.tzinfo is None:
        au = au.replace(tzinfo=timezone.utc)
    if plan == "trial" and is_active and au is not None and au > now:
        return True
    if plan in ("agent", "pro", "beta") and is_active:
        if au is None or au > now:
            return True
    return False


def _user_effective_access(cur: Any, user_id: str) -> bool:
    cur.execute(
        """
        SELECT plan, is_active, paused_until, active_until
        FROM subscriptions
        WHERE user_id = %s::uuid
        """,
        (user_id,),
    )
    row = cur.fetchone()
    if not row:
        return False
    plan, is_active, paused_until, active_until = (
        row[0],
        bool(row[1]),
        row[2],
        row[3],
    )
    now = datetime.now(timezone.utc)
    return _user_push_eligible(
        str(plan or "free"),
        is_active,
        paused_until,
        now,
        active_until=active_until,
    )


def _feed_where_sql() -> tuple[str, list[Any]]:
    return feed_visibility_where_sql()


def _load_user_tags(cur: Any, user_id: str) -> dict[str, float]:
    """O250d: same loader as api_server._load_user_tags (weights + decay)."""
    from config import load_config
    from pg_storage import _ensure_user_tags_columns

    url = (load_config().database_url or "").strip()
    if url:
        _ensure_user_tags_columns(url)
    cur.execute(
        """
        SELECT tag, COALESCE(weight, 1.0), last_active_at
        FROM user_tags
        WHERE user_id = %s::uuid
        ORDER BY tag
        """,
        (user_id,),
    )
    return effective_user_tag_weights(cur.fetchall())


def _canonical_lead_tags(raw: Any) -> list[str]:
    slugs, _ = lead_tags_for_feed(raw)
    return slugs


def _parse_ai_reasons(raw: Any) -> list[str]:
    from ai_reasons import parse_ai_reasons_raw

    reasons, _ = parse_ai_reasons_raw(raw)
    return reasons


def _parse_tools_required(raw: Any) -> list[str]:
    from tools_catalog import normalize_tools_required

    if raw is None:
        return []
    items: list[str] = []
    if isinstance(raw, list):
        items = [str(t).strip() for t in raw if str(t).strip()]
    elif isinstance(raw, str) and raw.strip():
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                items = [str(t).strip() for t in data if str(t).strip()]
            else:
                items = [raw.strip()]
        except json.JSONDecodeError:
            items = [raw.strip()]
    return list(normalize_tools_required(items))


def _persist_lead_tools_required(cur: Any, lead_id: int, tools: list[str]) -> None:
    """O37b: L2 tools → Neon leads.tools_required."""
    clean = [str(t).strip() for t in tools if str(t).strip()]
    if not clean:
        return
    tools_json = json.dumps(clean, ensure_ascii=False)
    cur.execute(
        "UPDATE leads SET tools_required = %s::jsonb WHERE id = %s",
        (tools_json, lead_id),
    )


def _lite_from_lead_row(row: tuple[Any, ...]) -> AiLiteAnalysis:
    tags = _canonical_lead_tags(row[8])
    v = (row[7] or "OK").strip().casefold()
    hidden = v in ("мимо", "пропустить", "skip")
    cat_raw = (row[11] or "").strip()
    primary_category = cat_raw if cat_raw in CATEGORIES else ""
    return AiLiteAnalysis(
        feed_visible=not hidden,
        task_summary=(row[12] or "").strip() or (row[3] or "")[:400],
        lead_tags=tuple(tags),
        ai_reasons=tuple(_parse_ai_reasons(row[9])),
        primary_category=primary_category,
    )


def _tools_from_lead_row(row: tuple[Any, ...]) -> list[str]:
    """O148: regex/heuristic from TZ — 0 LLM on draft/warm hot path."""
    tools = _parse_tools_required(row[13])
    if tools:
        return tools
    lite = _lite_from_lead_row(row)
    hints = tools_from_tz_text(
        row[2] or "",
        row[3] or "",
        lite.task_summary or "",
    )
    if not hints:
        return []
    return list(normalize_tools_required(hints))


def _ondemand_lead_tools(
    cfg: Config,
    row: tuple[Any, ...],
    *,
    ai_errors: list[str],
    log_prefix: str,
    max_retries: int = 2,
) -> list[str]:
    """O148: was pro LLM — tz heuristic only (offline backlog keeps analyze_lead_tools)."""
    del cfg, ai_errors, log_prefix, max_retries
    return _tools_from_lead_row(row)


def _backfill_lead_tools_if_empty(
    cur: Any,
    cfg: Config,
    row: tuple[Any, ...],
    *,
    ai_errors: list[str],
    log_prefix: str,
    max_retries: int = 2,
) -> list[str]:
    """O37b: on-demand / cache-hit — заполнить tools_required, если колонка пуста."""
    tools = _ondemand_lead_tools(
        cfg,
        row,
        ai_errors=ai_errors,
        log_prefix=log_prefix,
        max_retries=max_retries,
    )
    if tools:
        _persist_lead_tools_required(cur, int(row[0]), tools)
    return tools


def _source_label(source: str) -> str:
    key = (source or "").strip().lower()
    return SOURCE_LABELS.get(key, key or "—")


def _format_push_text(
    *,
    title: str,
    source: str,
    budget_text: str,
    task_summary: str,
    match_pct: int,
    lead_tags: list[str],
    tools_required: list[str],
    order_url: str = "",
) -> str:
    head = (title or "Новый заказ").strip()[:120]
    summary = (task_summary or "").strip()
    if len(summary) > 280:
        summary = summary[:277].rstrip() + "…"
    budget = (budget_text or "").strip() or "—"
    src = _source_label(source)
    _, tag_labels = lead_tags_for_feed(lead_tags)
    lines = [
        "🔔 Match",
        f"{src} · {budget}",
        "",
        head,
    ]
    if summary:
        lines.append(summary)
    if tag_labels:
        lines.append("")
        lines.append("Навыки: " + ", ".join(tag_labels[:6]))
    if tools_required:
        lines.append("Инструменты: " + ", ".join(tools_required[:5]))
    lines.append("")
    link = (order_url or "").strip() or _LENTA_BASE
    lines.append(f"→ {link}")
    return "\n".join(lines)


def _draft_result_keyboard(
    *,
    reply_draft: str,
    order_url: str,
    source: str,
) -> str:
    """Inline keyboard for draft result message: copy_text + source link."""
    copy_text = strip_tg_draft_price_deadline(reply_draft)
    if len(copy_text) > 256:
        copy_text = copy_text[:253] + "…"
    label = f"На {_source_label(source)} ↗" if source else "На биржу ↗"
    link = (order_url or "").strip() or _LENTA_BASE
    rows: list[list[dict[str, str | dict[str, str]]]] = [
        [
            {"text": "Скопировать текст", "copy_text": {"text": copy_text}},
            {"text": label, "url": link},
        ],
    ]
    return json.dumps({"inline_keyboard": rows}, ensure_ascii=False)


def _push_keyboard(*, show_generate: bool, lead_id: int, order_url: str = "") -> str:
    del show_generate  # O265: premium gate in draft callback, not keyboard layout
    order = (order_url or "").strip() or _LENTA_BASE
    rows: list[list[dict[str, str]]] = [
        [
            {"text": "Не моё", "callback_data": f"nope:{lead_id}"},
            {"text": "Отклик", "callback_data": f"draft:{lead_id}"},
        ],
        [
            {"text": "Смотреть в ленте", "url": _lenta_lead_url(lead_id)},
            {"text": "Смотреть на бирже", "url": order},
        ],
    ]
    return json.dumps({"inline_keyboard": rows}, ensure_ascii=False)


def _send_push_message(
    cfg: Config,
    chat_id: int,
    text: str,
    *,
    lead_id: int,
    show_generate: bool,
    order_url: str = "",
) -> tuple[bool, str]:
    api_url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/sendMessage"
    markup = _push_keyboard(
        show_generate=show_generate, lead_id=lead_id, order_url=order_url
    )
    try:
        session = requests.Session()
        session.trust_env = False
        resp = tg_http_request(
            "POST",
            api_url,
            session=session,
            data={
                "chat_id": str(chat_id),
                "text": text,
                "reply_markup": markup,
                "disable_web_page_preview": True,
            },
            timeout=20.0,
        )
        if resp.status_code != 200:
            return False, _tg_api_fail_detail(resp)
        body = resp.json()
        if not body.get("ok"):
            return False, _tg_api_fail_detail(resp)
        return True, ""
    except requests.RequestException as exc:
        return False, type(exc).__name__


def _normalize_order_url(url: str) -> str:
    """Canonical order URL for push dedup (no query/fragment, lower host)."""
    raw = (url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.netloc:
        return raw.split("?", 1)[0].rstrip("/") or raw
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, "", "", ""))


def _user_already_pushed_for_order(
    cur: Any,
    user_id: str,
    *,
    source: str,
    external_id: str,
    order_url: str,
) -> bool:
    """O158: dedup push by (source, external_id) or normalized URL — not only lead_id."""
    src = (source or "").strip()
    ext = (external_id or "").strip()
    if src and ext:
        cur.execute(
            """
            SELECT 1 FROM match_push_log mpl
            INNER JOIN leads l ON l.id = mpl.lead_id
            WHERE mpl.user_id = %s::uuid
              AND l.source = %s
              AND l.external_id = %s
            LIMIT 1
            """,
            (user_id, src, ext),
        )
        if cur.fetchone():
            return True
    norm = _normalize_order_url(order_url)
    if not norm:
        return False
    cur.execute(
        """
        SELECT 1 FROM match_push_log mpl
        INNER JOIN leads l ON l.id = mpl.lead_id
        WHERE mpl.user_id = %s::uuid
          AND l.url IS NOT NULL
          AND TRIM(l.url) <> ''
          AND split_part(regexp_replace(TRIM(l.url), '/$', ''), '?', 1)
              = split_part(%s, '?', 1)
        LIMIT 1
        """,
        (user_id, norm),
    )
    return cur.fetchone() is not None


def _fetch_lead_row(cur: Any, lead_id: int) -> tuple[Any, ...] | None:
    feed_where, feed_params = _feed_where_sql()
    cur.execute(
        f"SELECT {_LEAD_SELECT_COLS} FROM leads WHERE id = %s AND {feed_where}",
        (lead_id, *feed_params),
    )
    return cur.fetchone()


def _analyze_shared_ondemand(
    cfg: Config,
    *,
    title: str,
    budget_text: str,
    description: str,
    lite: AiLiteAnalysis,
    tools_required: list[str],
    ai_errors: list[str],
    log_prefix: str,
    max_retries: int = 2,
    lead_id: int | None = None,
    source: str = "",
    url: str = "",
) -> str | None:
    """O57/O59a: shared on-demand L2 — без profile, отдельный semaphore + backoff."""
    attempts = max(1, int(max_retries))
    with _ONDEMAND_L2_SEM:
        for attempt in range(attempts):
            draft = analyze_shared_reply_draft(
                cfg,
                title=title,
                budget_text=budget_text,
                lite=lite,
                tools_required=tools_required,
                description=description,
                source=source,
                url=url,
                errors=ai_errors,
                log_prefix=log_prefix,
                timeout_sec=90.0,
                max_attempts=2,
                lead_id=lead_id,
            )
            if draft:
                return draft
            if attempt < attempts - 1:
                delay = _ONDEMAND_L2_BACKOFF_SEC[min(attempt, len(_ONDEMAND_L2_BACKOFF_SEC) - 1)]
                time.sleep(delay)
    return None


def _insert_user_draft(cur: Any, user_id: str, lead_id: int, reply: str) -> None:
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


def _build_personalized_reply(
    cfg: Config,
    *,
    user_id: str,
    lead_id: int,
    shared_reply: str,
    ai_errors: list[str],
    log_prefix: str,
    max_attempts: int = 2,
) -> tuple[str, bool]:
    """O89: per-user uniquify; fallback to shared only on emergency."""
    base = strip_reply_draft_price_deadline(shared_reply)
    personalized = rephrase_reply_draft_per_user(
        cfg,
        base_reply_draft=base,
        user_id=user_id,
        lead_id=lead_id,
        errors=ai_errors,
        log_prefix=log_prefix,
        max_attempts=max_attempts,
    )
    if personalized:
        return personalized, False
    return base, True


def _draft_result_from_row(
    cur: Any,
    user_id: str,
    row: tuple[Any, ...],
    reply: str,
) -> DraftResult:
    user_tags = _load_user_tags(cur, user_id)
    tags = _canonical_lead_tags(row[8])
    km = keyword_match(tags, user_tags)
    tools = _parse_tools_required(row[13])
    return DraftResult(reply_draft=reply, tools_required=tools, keyword_match=km)


def materialize_shared_draft_for_user(
    cfg: Config,
    *,
    user_id: str,
    lead_id: int,
    log_prefix: str = "",
) -> DraftResult | None:
    """O89: leads.reply_draft (shared) -> per-user uniquified cache."""
    if not cfg.database_url.strip():
        return None
    prefix = log_prefix or f"draft:{lead_id}:"
    ai_errors: list[str] = []
    with psycopg.connect(cfg.database_url) as conn:
        with conn.cursor() as cur:
            if not _user_effective_access(cur, user_id):
                return None

            saved = _fetch_saved_draft(cur, user_id, lead_id)
            if saved:
                row = _fetch_lead_row(cur, lead_id)
                if row is None:
                    return None
                tools = _backfill_lead_tools_if_empty(
                    cur, cfg, row, ai_errors=ai_errors, log_prefix=prefix
                )
                if tools:
                    row = _fetch_lead_row(cur, lead_id) or row
                    conn.commit()
                return _draft_result_from_row(cur, user_id, row, saved)

            row = _fetch_lead_row(cur, lead_id)
            if row is None:
                return None

            shared = (row[14] or "").strip()
            if not shared:
                return None

            reply, fallback_shared = _build_personalized_reply(
                cfg,
                user_id=user_id,
                lead_id=lead_id,
                shared_reply=shared,
                ai_errors=ai_errors,
                log_prefix=prefix,
            )
            tools = _backfill_lead_tools_if_empty(
                cur, cfg, row, ai_errors=ai_errors, log_prefix=prefix
            )
            _insert_user_draft(cur, user_id, lead_id, reply)
            conn.commit()
            mode = "fallback_shared" if fallback_shared else "personalized"
            logger.info("%s%s lead=%s user=%s", prefix, mode, lead_id, _uid8(user_id))
            if tools:
                row = _fetch_lead_row(cur, lead_id) or row
            return _draft_result_from_row(cur, user_id, row, reply)


def _fetch_saved_draft(cur: Any, user_id: str, lead_id: int) -> str | None:
    cur.execute(
        """
        SELECT reply_draft FROM user_lead_replies
        WHERE user_id = %s::uuid AND lead_id = %s AND deleted_at IS NULL
        """,
        (user_id, lead_id),
    )
    row = cur.fetchone()
    if not row:
        return None
    draft = (row[0] or "").strip()
    return draft or None


def generate_and_store_lead_draft(
    cfg: Config,
    *,
    user_id: str,
    lead_id: int,
    log_prefix: str = "",
    max_retries: int = 2,
    enforce_rate_limit: bool = True,
) -> DraftResult:
    """O57: shared on-demand L2 → leads.reply_draft + user_lead_replies."""
    if not cfg.ai_active:
        raise DraftError("ai_unavailable")

    if enforce_rate_limit:
        retry_after = draft_rate_limit_retry_after(user_id)
        if retry_after is not None:
            lim = draft_hourly_limit()
            raise DraftError("rate_limit", f"Лимит — {lim} черновиков в час")

    prefix = log_prefix or f"draft:{lead_id}:"
    ai_errors: list[str] = []
    from draft_trace import DraftTimer, log_draft_stage

    trace = DraftTimer()
    log_draft_stage(prefix, stage="start", timer=trace, lead_id=lead_id, user_id=_uid8(user_id))
    with psycopg.connect(cfg.database_url) as conn:
        with conn.cursor() as cur:
            if not _user_effective_access(cur, user_id):
                raise DraftError("forbidden", "paid subscription required")
            log_draft_stage(prefix, stage="access_ok", timer=trace, lead_id=lead_id)

            saved = _fetch_saved_draft(cur, user_id, lead_id)
            if saved:
                row = _fetch_lead_row(cur, lead_id)
                if row is None:
                    raise DraftError("not_found")
                tools = _backfill_lead_tools_if_empty(
                    cur, cfg, row, ai_errors=ai_errors, log_prefix=prefix
                )
                if tools:
                    row = _fetch_lead_row(cur, lead_id) or row
                    conn.commit()
                log_draft_stage(
                    prefix,
                    stage="done",
                    timer=trace,
                    lead_id=lead_id,
                    path="cache_hit",
                    user_id=_uid8(user_id),
                )
                return _draft_result_from_row(cur, user_id, row, saved)

            row = _fetch_lead_row(cur, lead_id)
            if row is None:
                raise DraftError("not_found")
            log_draft_stage(prefix, stage="lead_loaded", timer=trace, lead_id=lead_id)

            user_tags = _load_user_tags(cur, user_id)
            tags = _canonical_lead_tags(row[8])
            km = keyword_match(tags, user_tags)

            shared = (row[14] or "").strip()
            if shared:
                log_draft_stage(
                    prefix,
                    stage="path_fast_shared",
                    timer=trace,
                    lead_id=lead_id,
                    shared_len=len(shared),
                )
                reply, fallback_shared = _build_personalized_reply(
                    cfg,
                    user_id=user_id,
                    lead_id=lead_id,
                    shared_reply=shared,
                    ai_errors=ai_errors,
                    log_prefix=prefix,
                )
                log_draft_stage(
                    prefix,
                    stage="l3",
                    timer=trace,
                    lead_id=lead_id,
                    fallback=fallback_shared,
                )
                tools = _backfill_lead_tools_if_empty(
                    cur, cfg, row, ai_errors=ai_errors, log_prefix=prefix
                )
                _insert_user_draft(cur, user_id, lead_id, reply)
                conn.commit()
                logger.info("%sfast_shared lead=%s user=%s", prefix, lead_id, _uid8(user_id))
                if fallback_shared:
                    logger.warning("%sfallback_shared lead=%s user=%s", prefix, lead_id, _uid8(user_id))
                note_draft_request(True)
                log_draft_stage(
                    prefix,
                    stage="done",
                    timer=trace,
                    lead_id=lead_id,
                    path="fast_shared",
                    user_id=_uid8(user_id),
                )
                if tools:
                    row = _fetch_lead_row(cur, lead_id) or row
                return _draft_result_from_row(cur, user_id, row, reply)

            log_draft_stage(prefix, stage="path_cold_l2", timer=trace, lead_id=lead_id)
            lite = _lite_from_lead_row(row)
            tools = _parse_tools_required(row[13])
            if not tools:
                tools = _ondemand_lead_tools(
                    cfg,
                    row,
                    ai_errors=ai_errors,
                    log_prefix=prefix,
                    max_retries=max_retries,
                )
                if tools:
                    _persist_lead_tools_required(cur, lead_id, tools)
            log_draft_stage(
                prefix,
                stage="tools",
                timer=trace,
                lead_id=lead_id,
                count=len(tools),
            )
            reply_raw = _analyze_shared_ondemand(
                cfg,
                title=row[2] or "",
                budget_text=row[5] or "",
                description=row[3] or "",
                lite=lite,
                tools_required=tools,
                ai_errors=ai_errors,
                log_prefix=prefix,
                max_retries=max_retries,
                lead_id=lead_id,
                source=row[1] or "",
                url=row[4] or "",
            )
            log_draft_stage(
                prefix,
                stage="l2",
                timer=trace,
                lead_id=lead_id,
                ok=bool(reply_raw),
            )
            if not reply_raw:
                note_draft_request(False)
                detail = "; ".join(ai_errors) if ai_errors else "draft generation failed"
                logger.warning("%sfail %s", prefix, detail)
                raise DraftError("ai_fail", detail)
            reply = strip_reply_draft_price_deadline(str(reply_raw or "").strip())
            cur.execute(
                """
                UPDATE leads
                SET reply_draft = COALESCE(NULLIF(%s, ''), reply_draft)
                WHERE id = %s
                """,
                (reply, lead_id),
            )
            # O135: first user on cold lead — store shared L2 as-is (skip L3 uniquify).
            _insert_user_draft(cur, user_id, lead_id, reply)
            conn.commit()
            logger.info(
                "%sfirst_user_l2_only lead=%s user=%s",
                prefix,
                lead_id,
                _uid8(user_id),
            )
            log_draft_stage(
                prefix,
                stage="done",
                timer=trace,
                lead_id=lead_id,
                path="cold_l2",
                user_id=_uid8(user_id),
            )

    note_draft_request(True)
    return DraftResult(reply_draft=reply, tools_required=tools, keyword_match=km)


def warm_shared_lead_draft(
    cfg: Config,
    *,
    lead_id: int,
    log_prefix: str = "",
) -> bool:
    """O148: 1× pro L2 → leads.reply_draft only (no user_lead_replies)."""
    if not cfg.ai_active:
        raise DraftError("ai_unavailable")

    prefix = log_prefix or f"draft:warm:{lead_id}:"
    ai_errors: list[str] = []
    from draft_trace import DraftTimer, log_draft_stage

    trace = DraftTimer()
    log_draft_stage(prefix, stage="start", timer=trace, lead_id=lead_id, path="warm")
    with psycopg.connect(cfg.database_url) as conn:
        with conn.cursor() as cur:
            row = _fetch_lead_row(cur, lead_id)
            if row is None:
                raise DraftError("not_found")

            shared = (row[14] or "").strip()
            if shared:
                log_draft_stage(
                    prefix,
                    stage="done",
                    timer=trace,
                    lead_id=lead_id,
                    path="warm_skip",
                )
                return True

            lite = _lite_from_lead_row(row)
            tools = _tools_from_lead_row(row)
            if tools:
                _persist_lead_tools_required(cur, int(row[0]), tools)
                conn.commit()
                row = _fetch_lead_row(cur, lead_id) or row

            log_draft_stage(prefix, stage="path_warm", timer=trace, lead_id=lead_id)
            reply_raw = _analyze_shared_ondemand(
                cfg,
                title=row[2] or "",
                budget_text=row[5] or "",
                description=row[3] or "",
                lite=lite,
                tools_required=tools,
                ai_errors=ai_errors,
                log_prefix=prefix,
                max_retries=2,
                lead_id=lead_id,
                source=row[1] or "",
                url=row[4] or "",
            )
            log_draft_stage(
                prefix,
                stage="l2",
                timer=trace,
                lead_id=lead_id,
                ok=bool(reply_raw),
            )
            if not reply_raw:
                note_draft_request(False)
                detail = "; ".join(ai_errors) if ai_errors else "draft generation failed"
                logger.warning("%sfail %s", prefix, detail)
                raise DraftError("ai_fail", detail)

            reply = strip_reply_draft_price_deadline(str(reply_raw or "").strip())
            cur.execute(
                """
                UPDATE leads
                SET reply_draft = COALESCE(NULLIF(%s, ''), reply_draft)
                WHERE id = %s
                """,
                (reply, lead_id),
            )
            conn.commit()
            note_draft_request(True)
            log_draft_stage(
                prefix,
                stage="done",
                timer=trace,
                lead_id=lead_id,
                path="warm",
            )
            return True


def _send_tg_draft_result(
    cfg: Config,
    chat_id: int,
    lead_id: int,
    reply_draft: str,
    errors: list[str],
    user_id: str,
    *,
    source: str = "",
    order_url: str = "",
) -> None:
    tg_draft = strip_tg_draft_price_deadline(reply_draft)
    body = (
        f"✍️ Черновик отклика (lead #{lead_id}):\n\n"
        f"{tg_draft}\n\n"
        f"→ Inbox: {_CABINET_URL}"
    )
    keyboard = _draft_result_keyboard(
        reply_draft=reply_draft,
        order_url=order_url,
        source=source,
    )
    _send_draft_reply(cfg, chat_id, body, errors, reply_markup=keyboard)
    errors.append(f"tg:draft:ok user={_uid8(user_id)} lead={lead_id}")
    from api_server import _apply_tag_weight_event_for_lead

    _apply_tag_weight_event_for_lead(user_id, lead_id, "draft")


def handle_tg_nope_callback(
    cfg: Config,
    callback_query: dict[str, Any],
    errors: list[str],
) -> bool:
    """O265/O281: callback nope:{lead_id} → push_nope weight + delete push message."""
    data = str(callback_query.get("data") or "").strip()
    m = _NOPE_CALLBACK_RE.match(data)
    if not m:
        return False

    lead_id = int(m.group(1))
    from_user = callback_query.get("from") or {}
    tg_user_id = from_user.get("id")
    callback_id = callback_query.get("id")
    message = callback_query.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    message_id = message.get("message_id")

    if tg_user_id is None:
        errors.append(f"tg:push:nope:skip lead={lead_id} missing from")
        return True

    _answer_callback_query(cfg, str(callback_id), "Учтём в профиле", errors)

    if not cfg.database_url.strip():
        errors.append(f"tg:push:nope:skip lead={lead_id} no_db")
        return True

    try:
        with psycopg.connect(cfg.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM users WHERE tg_user_id = %s",
                    (int(tg_user_id),),
                )
                row = cur.fetchone()
                if not row:
                    errors.append(f"tg:push:nope:skip lead={lead_id} no_user")
                    return True
                user_id = str(row[0])
    except Exception as exc:
        logger.warning("tg:push:nope lead=%s: %s", lead_id, exc)
        errors.append(f"tg:push:nope:err lead={lead_id}")
        return True

    from api_server import _apply_tag_weight_event_for_lead

    _apply_tag_weight_event_for_lead(user_id, lead_id, "push_nope")
    logger.info("tg:push:nope lead=%s user=%s", lead_id, _uid8(user_id))
    errors.append(f"tg:push:nope lead={lead_id} user={_uid8(user_id)}")
    if chat_id is not None and message_id is not None:
        _delete_message(cfg, int(chat_id), int(message_id))
    return True


def handle_tg_draft_callback(
    cfg: Config,
    callback_query: dict[str, Any],
    errors: list[str],
) -> bool:
    """O50: callback draft:{lead_id} → черновик в TG + inbox."""
    data = str(callback_query.get("data") or "").strip()
    m = _DRAFT_CALLBACK_RE.match(data)
    if not m:
        return False

    lead_id = int(m.group(1))
    from_user = callback_query.get("from") or {}
    tg_user_id = from_user.get("id")
    message = callback_query.get("message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    callback_id = callback_query.get("id")

    logger.info(
        "tg:draft:callback lead=%s tg_user=%s chat=%s",
        lead_id,
        tg_user_id,
        chat_id,
    )
    errors.append(f"tg:draft:callback lead={lead_id} tg={tg_user_id}")

    if tg_user_id is None or chat_id is None:
        errors.append(f"tg:draft:skip lead={lead_id} missing from/chat")
        return True

    if not cfg.database_url.strip():
        _log_draft_mute(errors, chat_id=int(chat_id), code="no_db")
        return True

    try:
        with psycopg.connect(cfg.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM users WHERE tg_user_id = %s",
                    (int(tg_user_id),),
                )
                row = cur.fetchone()
                if not row:
                    _log_draft_mute(
                        errors,
                        chat_id=int(chat_id),
                        code="no_user",
                    )
                    return True
                user_id = str(row[0])
                if not _user_effective_access(cur, user_id):
                    _answer_callback_query(
                        cfg,
                        str(callback_id),
                        f"Нужна подписка — {_CABINET_URL}",
                        errors,
                    )
                    _log_draft_mute(
                        errors,
                        chat_id=int(chat_id),
                        code="forbidden",
                    )
                    return True

                retry_after = draft_rate_limit_retry_after(user_id)
                if retry_after is not None:
                    lim = draft_hourly_limit()
                    _answer_callback_query(
                        cfg,
                        str(callback_id),
                        f"Лимит — {lim} черновиков в час",
                        errors,
                    )
                    _log_draft_mute(
                        errors,
                        chat_id=int(chat_id),
                        code="rate_limit",
                    )
                    return True

        _answer_callback_query(cfg, str(callback_id), "Генерирую отклик…", errors)

        # Lookup lead source + url for inline buttons
        lead_source = ""
        lead_url = ""
        try:
            with psycopg.connect(cfg.database_url) as lconn:
                with lconn.cursor() as lcur:
                    lcur.execute(
                        "SELECT source, url FROM leads WHERE id = %s",
                        (lead_id,),
                    )
                    lrow = lcur.fetchone()
                    if lrow:
                        lead_source = str(lrow[0] or "")
                        lead_url = str(lrow[1] or "")
        except Exception:
            pass

        from draft_async import poll_draft, submit_draft

        prefix = f"tg:draft:{lead_id}:"
        resp = submit_draft(
            cfg,
            user_id=user_id,
            lead_id=lead_id,
            log_prefix=prefix,
            quick_wait_sec=3.0,
        )
        if resp.status == "ready":
            _send_tg_draft_result(
                cfg, int(chat_id), lead_id, resp.reply_draft, errors, user_id,
                source=lead_source, order_url=lead_url,
            )
            return True

        def _poll_and_send() -> None:
            deadline = time.time() + 90
            while time.time() < deadline:
                polled = poll_draft(cfg, user_id=user_id, lead_id=lead_id, log_prefix=prefix)
                if polled.status == "ready":
                    _send_tg_draft_result(
                        cfg, int(chat_id), lead_id, polled.reply_draft, errors, user_id,
                        source=lead_source, order_url=lead_url,
                    )
                    return
                if polled.status == "failed":
                    _log_draft_mute(
                        errors,
                        chat_id=int(chat_id),
                        code="poll_fail",
                        detail=polled.error or "",
                    )
                    errors.append(f"tg:draft:fail lead={lead_id}")
                    return
                time.sleep(2)
            _log_draft_mute(errors, chat_id=int(chat_id), code="poll_timeout")

        threading.Thread(target=_poll_and_send, daemon=True).start()
        return True
    except DraftError as exc:
        _log_draft_mute(
            errors,
            chat_id=int(chat_id),
            code=exc.code,
            detail=exc.detail,
        )
        errors.append(f"tg:draft:fail lead={lead_id} {exc.code}")
    except Exception as exc:
        logger.warning("tg:draft callback lead=%s: %s", lead_id, exc)
        _log_draft_mute(
            errors,
            chat_id=int(chat_id),
            code="err",
            detail=type(exc).__name__,
        )
        errors.append(f"tg:draft:err lead={lead_id}")

    return True


def _log_draft_mute(
    errors: list[str] | None,
    *,
    chat_id: int,
    code: str,
    detail: str = "",
) -> None:
    """O86: ошибки draft — только radar.log, без sendMessage подписчику."""
    err = errors if errors is not None else []
    msg = f"tg:draft:mute chat={chat_id} {code}"
    if detail:
        msg += f" {detail[:120]}"
    err.append(msg)
    logger.info(msg)


def _delete_message(
    cfg: Config,
    chat_id: int,
    message_id: int,
) -> None:
    """O281: remove push card from TG chat (best-effort; warn-only on failure)."""
    proxies = telegram_requests_proxies(cfg)
    api_url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/deleteMessage"
    try:
        session = requests.Session()
        session.trust_env = False
        resp = session.post(
            api_url,
            data={"chat_id": str(chat_id), "message_id": str(message_id)},
            timeout=10.0,
            proxies=proxies,
        )
        if resp.status_code != 200:
            msg = resp.text[:200] if resp.text else f"HTTP {resp.status_code}"
            logger.warning(
                "tg:push:deleteMessage fail chat=%s msg=%s: %s",
                chat_id,
                message_id,
                msg,
            )
            return
        body = resp.json()
        if not body.get("ok", False):
            desc = str(body.get("description") or body)[:200]
            logger.warning(
                "tg:push:deleteMessage fail chat=%s msg=%s: %s",
                chat_id,
                message_id,
                desc,
            )
    except requests.RequestException as exc:
        logger.warning(
            "tg:push:deleteMessage err chat=%s msg=%s: %s",
            chat_id,
            message_id,
            exc,
        )


def _answer_callback_query(
    cfg: Config,
    callback_id: str,
    text: str,
    errors: list[str] | None = None,
) -> None:
    proxies = telegram_requests_proxies(cfg)
    api_url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/answerCallbackQuery"
    err = errors if errors is not None else []
    try:
        session = requests.Session()
        session.trust_env = False
        resp = session.post(
            api_url,
            data={"callback_query_id": callback_id, "text": text[:180]},
            timeout=10.0,
            proxies=proxies,
        )
        if resp.status_code != 200 or not resp.json().get("ok", False):
            msg = resp.text[:200] if resp.text else f"HTTP {resp.status_code}"
            logger.warning("tg:draft:answerCallback fail: %s", msg)
            err.append(f"tg:draft:answer:fail {resp.status_code}")
    except requests.RequestException as exc:
        logger.warning("tg:draft:answerCallback err: %s", exc)
        err.append(f"tg:draft:answer:err {type(exc).__name__}")


def _send_draft_reply(
    cfg: Config,
    chat_id: int,
    text: str,
    errors: list[str] | None = None,
    *,
    reply_markup: str | None = None,
) -> None:
    proxies = telegram_requests_proxies(cfg)
    api_url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/sendMessage"
    chunk = text[:4000]
    err = errors if errors is not None else []
    payload: dict[str, Any] = {"chat_id": str(chat_id), "text": chunk}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        session = requests.Session()
        session.trust_env = False
        resp = session.post(
            api_url,
            data=payload,
            timeout=20.0,
            proxies=proxies,
        )
        if resp.status_code != 200 or not resp.json().get("ok", False):
            msg = resp.text[:200] if resp.text else f"HTTP {resp.status_code}"
            logger.warning("tg:draft:sendMessage fail chat=%s: %s", chat_id, msg)
            err.append(f"tg:draft:send:fail HTTP {resp.status_code}")
    except requests.RequestException as exc:
        logger.warning("tg:draft:sendMessage err chat=%s: %s", chat_id, exc)
        err.append(f"tg:draft:send:err {type(exc).__name__}")


def _push_km_for_lead_row(
    row: tuple[Any, ...],
    user_tags: dict[str, float],
) -> int | None:
    """O250b: same km as feed (`api_server._km_for_lead_row`)."""
    tags = _canonical_lead_tags(row[8])
    category = resolve_lead_category(row[11], row[2] or "", row[3] or "", tags)
    if not user_tags:
        return 0
    return compatibility_match(
        tags,
        user_tags,
        lead_category=category,
        user_quiz_niches=user_quiz_niches_from_tags(user_tags),
    )


def push_match_for_lead(
    cfg: Config,
    lead_id: int,
    *,
    title: str,
    task_summary: str,
    lead_tags: list[str],
    errors: list[str] | None = None,
    log_path: Any = None,
) -> int:
    """
    После L1 visible lead: каждому paid/beta с tg_chat_id + push_enabled
    у кого km >= push_min_match → sendMessage (O50: полная карточка).
    """
    if not cfg.match_push_enabled or not cfg.database_url.strip():
        return 0

    err = errors if errors is not None else []
    now = datetime.now(timezone.utc)
    sent = 0
    debug = _match_push_debug()
    radar_log = log_path if log_path is not None else cfg.radar_log_path

    try:
        with psycopg.connect(cfg.database_url) as conn:
            with conn.cursor() as cur:
                row = _fetch_lead_row(cur, lead_id)
                if row is None:
                    _log_push_line(
                        radar_log,
                        f"push:match:lead_missing id={lead_id}",
                        err,
                    )
                    return 0

                lead_title = (row[2] or title or "").strip()
                lead_summary = (row[12] or task_summary or "").strip()
                lead_source = str(row[1] or "")
                lead_budget = str(row[5] or "")
                lead_order_url = str(row[4] or "").strip()
                tools = _parse_tools_required(row[13])
                card_tags = _canonical_lead_tags(row[8]) or lead_tags
                cur.execute(
                    "SELECT external_id FROM leads WHERE id = %s",
                    (lead_id,),
                )
                ext_row = cur.fetchone()
                lead_external_id = str(ext_row[0] or "").strip() if ext_row else ""

                cur.execute(
                    """
                    SELECT u.id, u.tg_chat_id, s.plan, s.is_active, s.paused_until,
                           s.active_until,
                           COALESCE(u.push_min_match, %s),
                           COALESCE(u.push_enabled, TRUE)
                    FROM users u
                    INNER JOIN subscriptions s ON s.user_id = u.id
                    WHERE u.tg_chat_id IS NOT NULL
                    """,
                    (_PUSH_MIN_MATCH_DEFAULT,),
                )
                for (
                    user_id,
                    chat_id,
                    plan,
                    is_active,
                    paused_until,
                    active_until,
                    push_min_match,
                    push_enabled,
                ) in cur.fetchall():
                    if chat_id is None:
                        if debug:
                            _log_push_line(
                                radar_log,
                                f"push:match:skip user={_uid8(user_id)} lead={lead_id} reason=no_chat",
                                err,
                            )
                        continue
                    if not bool(push_enabled):
                        if debug:
                            _log_push_line(
                                radar_log,
                                f"push:match:skip user={_uid8(user_id)} lead={lead_id} reason=push_off",
                                err,
                            )
                        continue
                    plan_str = str(plan or "free")
                    is_act = bool(is_active)
                    if not _user_push_eligible(
                        plan_str,
                        is_act,
                        paused_until,
                        now,
                        active_until=active_until,
                    ):
                        if debug:
                            _log_push_line(
                                radar_log,
                                f"push:match:skip user={_uid8(user_id)} lead={lead_id} reason=plan",
                                err,
                            )
                        continue
                    user_tags = _load_user_tags(cur, str(user_id))
                    if not user_tags:
                        if debug:
                            _log_push_line(
                                radar_log,
                                f"push:match:skip user={_uid8(user_id)} lead={lead_id} reason=tags",
                                err,
                            )
                        continue
                    km = _push_km_for_lead_row(row, user_tags)
                    if km is None or km < int(push_min_match):
                        if debug:
                            feed_km = km
                            skip_line = (
                                f"push:match:skip user={_uid8(user_id)} lead={lead_id} "
                                f"reason=km km={km} thr={push_min_match}"
                            )
                            if feed_km is not None:
                                skip_line += f" feed_km={feed_km} push_km={km}"
                            _log_push_line(radar_log, skip_line, err)
                        continue
                    cur.execute(
                        """
                        SELECT 1 FROM match_push_log
                        WHERE user_id = %s::uuid AND lead_id = %s
                        """,
                        (user_id, lead_id),
                    )
                    if cur.fetchone():
                        if debug:
                            _log_push_line(
                                radar_log,
                                f"push:match:skip user={_uid8(user_id)} lead={lead_id} reason=dedup",
                                err,
                            )
                        continue
                    if _user_already_pushed_for_order(
                        cur,
                        str(user_id),
                        source=lead_source,
                        external_id=lead_external_id,
                        order_url=lead_order_url,
                    ):
                        if debug:
                            _log_push_line(
                                radar_log,
                                f"push:match:skip user={_uid8(user_id)} lead={lead_id} reason=dedup_order",
                                err,
                            )
                        continue
                    show_generate = _user_effective_access(cur, str(user_id))
                    text = _format_push_text(
                        title=lead_title,
                        source=lead_source,
                        budget_text=lead_budget,
                        task_summary=lead_summary,
                        match_pct=km,
                        lead_tags=card_tags,
                        tools_required=tools,
                        order_url=lead_order_url,
                    )
                    sent_ok, fail_detail = _send_push_message(
                        cfg,
                        chat_id,
                        text,
                        lead_id=lead_id,
                        show_generate=show_generate,
                        order_url=lead_order_url,
                    )
                    if not sent_ok:
                        fail_line = (
                            f"push:match:fail user={_uid8(user_id)} lead={lead_id}"
                        )
                        if fail_detail:
                            fail_line += f" {fail_detail}"
                        _log_push_line(radar_log, fail_line, err)
                        continue
                    cur.execute(
                        """
                        INSERT INTO match_push_log (user_id, lead_id)
                        VALUES (%s::uuid, %s)
                        ON CONFLICT (user_id, lead_id) DO NOTHING
                        """,
                        (user_id, lead_id),
                    )
                    ok_line = (
                        f"push:match:user={_uid8(user_id)} lead={lead_id} km={km} thr={push_min_match}"
                    )
                    _log_push_line(radar_log, ok_line, err)
                    sent += 1
                conn.commit()
    except Exception as exc:
        logger.warning("push_match_for_lead %d: %s", lead_id, exc)
        _log_push_line(radar_log, f"push:match:err lead={lead_id}:{exc}", err)

    return sent


def lead_tags_from_lite(lite: Any) -> list[str]:
    if lite is None:
        return []
    return parse_lead_tags(list(lite.lead_tags))
