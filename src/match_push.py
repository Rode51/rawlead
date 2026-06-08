"""MATCH_PUSH (O30/O50): уведомления подписчикам @rawlead_bot — per-user threshold."""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import psycopg
import requests

from ai_analyze import (
    AiLiteAnalysis,
    analyze_lead_tools,
    rephrase_reply_draft_per_user,
    analyze_shared_reply_draft,
    note_draft_request,
)
from config import Config, telegram_requests_proxies
from public_feed import feed_visibility_where_sql
from radar_cycle_log import SOURCE_LABELS
from rank import keyword_match, parse_lead_tags, tags_as_weights
from reply_draft_strip import strip_reply_draft_price_deadline, strip_tg_draft_price_deadline
from draft_limits import draft_hourly_limit
from skills_catalog import lead_tags_for_feed, normalize_user_tags

logger = logging.getLogger(__name__)

_LENTA_BASE = "https://rawlead.ru/lenta/"


def _lenta_lead_url(lead_id: int) -> str:
    return f"{_LENTA_BASE}?lead={int(lead_id)}"
_CABINET_URL = "https://rawlead.ru/cabinet/"
_PUSH_MIN_MATCH_DEFAULT = 60
_DRAFT_CALLBACK_RE = re.compile(r"^draft:(\d+)$")
_DRAFT_WINDOW_SEC = 3600
_ONDEMAND_L2_SEM = threading.Semaphore(2)
_ONDEMAND_L2_BACKOFF_SEC = (0.5, 1)
_draft_attempts: dict[str, deque[float]] = defaultdict(deque)

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


def draft_rate_limit_retry_after(user_id: str) -> int | None:
    """O48/O60b: DRAFT_HOURLY_LIMIT per user; 0 = без лимита."""
    limit = draft_hourly_limit()
    if limit <= 0:
        return None
    now = time.time()
    q = _draft_attempts[user_id]
    cutoff = now - _DRAFT_WINDOW_SEC
    while q and q[0] < cutoff:
        q.popleft()
    if len(q) >= limit:
        return max(1, int(_DRAFT_WINDOW_SEC - (now - q[0])))
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
    cur.execute(
        "SELECT tag FROM user_tags WHERE user_id = %s::uuid ORDER BY tag",
        (user_id,),
    )
    tags = normalize_user_tags([row[0] for row in cur.fetchall()])
    return tags_as_weights(tags)


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
    return AiLiteAnalysis(
        feed_visible=not hidden,
        task_summary=(row[12] or "").strip() or (row[3] or "")[:400],
        lead_tags=tuple(tags),
        ai_reasons=tuple(_parse_ai_reasons(row[9])),
    )


def _ondemand_lead_tools(
    cfg: Config,
    row: tuple[Any, ...],
    *,
    ai_errors: list[str],
    log_prefix: str,
    max_retries: int = 2,
) -> list[str]:
    """O57/O125: tools-only L2 on draft click — not radar backlog, not full premium."""
    tools = _parse_tools_required(row[13])
    if tools:
        return tools
    lite = _lite_from_lead_row(row)
    snippet = (row[3] or lite.task_summary or "").strip()
    result = analyze_lead_tools(
        cfg,
        title=row[2] or "",
        budget_text=row[5] or "",
        description=snippet,
        lite=lite,
        errors=ai_errors,
        log_prefix=log_prefix,
        max_retries=max(1, min(int(max_retries), 2)),
    )
    if not result:
        return []
    return [str(t).strip() for t in result if str(t).strip()]


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
        f"🔔 Match {match_pct}%",
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


def _push_keyboard(*, show_generate: bool, lead_id: int, order_url: str = "") -> str:
    order = (order_url or "").strip() or _LENTA_BASE
    rows: list[list[dict[str, str]]] = []
    if show_generate:
        rows.append(
            [{"text": "Сгенерировать отклик", "callback_data": f"draft:{lead_id}"}]
        )
    rows.append(
        [
            {"text": "Открыть заказ", "url": order},
            {"text": "Лента", "url": _lenta_lead_url(lead_id)},
        ]
    )
    return json.dumps({"inline_keyboard": rows}, ensure_ascii=False)


def _send_push_message(
    cfg: Config,
    chat_id: int,
    text: str,
    *,
    lead_id: int,
    show_generate: bool,
    order_url: str = "",
) -> bool:
    proxies = telegram_requests_proxies(cfg)
    api_url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/sendMessage"
    markup = _push_keyboard(
        show_generate=show_generate, lead_id=lead_id, order_url=order_url
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
                errors=ai_errors,
                log_prefix=log_prefix,
                timeout_sec=90.0,
                max_attempts=2,
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
            logger.info("%s%s lead=%s user=%s", prefix, mode, lead_id, user_id[:8])
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
            raise DraftError("rate_limit", f"max {lim}/hour")

    prefix = log_prefix or f"draft:{lead_id}:"
    ai_errors: list[str] = []
    with psycopg.connect(cfg.database_url) as conn:
        with conn.cursor() as cur:
            if not _user_effective_access(cur, user_id):
                raise DraftError("forbidden", "paid subscription required")

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
                return _draft_result_from_row(cur, user_id, row, saved)

            row = _fetch_lead_row(cur, lead_id)
            if row is None:
                raise DraftError("not_found")

            user_tags = _load_user_tags(cur, user_id)
            tags = _canonical_lead_tags(row[8])
            km = keyword_match(tags, user_tags)

            shared = (row[14] or "").strip()
            if shared:
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
                logger.info("%sfast_shared lead=%s user=%s", prefix, lead_id, user_id[:8])
                if fallback_shared:
                    logger.warning("%sfallback_shared lead=%s user=%s", prefix, lead_id, user_id[:8])
                note_draft_request(True)
                if tools:
                    row = _fetch_lead_row(cur, lead_id) or row
                return _draft_result_from_row(cur, user_id, row, reply)

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
            )
            if not reply_raw:
                note_draft_request(False)
                detail = "; ".join(ai_errors) if ai_errors else "draft generation failed"
                logger.warning("%sfail %s", prefix, detail)
                raise DraftError("ai_fail", detail)
            reply = strip_reply_draft_price_deadline(reply_raw.strip())
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
                user_id[:8],
            )

    note_draft_request(True)
    return DraftResult(reply_draft=reply, tools_required=tools, keyword_match=km)


def _send_tg_draft_result(
    cfg: Config,
    chat_id: int,
    lead_id: int,
    reply_draft: str,
    errors: list[str],
    user_id: str,
) -> None:
    tg_draft = strip_tg_draft_price_deadline(reply_draft)
    body = (
        f"✍️ Черновик отклика (lead #{lead_id}):\n\n"
        f"{tg_draft}\n\n"
        f"→ Inbox: {_CABINET_URL}"
    )
    _send_draft_reply(cfg, chat_id, body, errors)
    errors.append(f"tg:draft:ok user={user_id[:8]} lead={lead_id}")


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

    _answer_callback_query(cfg, str(callback_id), "Генерирую отклик…", errors)

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
            _send_tg_draft_result(cfg, int(chat_id), lead_id, resp.reply_draft, errors, user_id)
            return True

        def _poll_and_send() -> None:
            deadline = time.time() + 90
            while time.time() < deadline:
                polled = poll_draft(cfg, user_id=user_id, lead_id=lead_id, log_prefix=prefix)
                if polled.status == "ready":
                    _send_tg_draft_result(
                        cfg, int(chat_id), lead_id, polled.reply_draft, errors, user_id
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
) -> None:
    proxies = telegram_requests_proxies(cfg)
    api_url = f"https://api.telegram.org/bot{cfg.telegram_bot_token}/sendMessage"
    chunk = text[:4000]
    err = errors if errors is not None else []
    try:
        session = requests.Session()
        session.trust_env = False
        resp = session.post(
            api_url,
            data={"chat_id": str(chat_id), "text": chunk},
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
    у кого km >= push_min_match → sendMessage (O50: полная карточка).
    """
    if not cfg.match_push_enabled or not cfg.database_url.strip():
        return 0

    err = errors if errors is not None else []
    now = datetime.now(timezone.utc)
    sent = 0

    try:
        with psycopg.connect(cfg.database_url) as conn:
            with conn.cursor() as cur:
                row = _fetch_lead_row(cur, lead_id)
                if row is None:
                    err.append(f"push:match:lead_missing id={lead_id}")
                    return 0

                lead_title = (row[2] or title or "").strip()
                lead_summary = (row[12] or task_summary or "").strip()
                lead_source = str(row[1] or "")
                lead_budget = str(row[5] or "")
                lead_order_url = str(row[4] or "").strip()
                tools = _parse_tools_required(row[13])
                card_tags = _canonical_lead_tags(row[8]) or lead_tags

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
                        continue
                    if not bool(push_enabled):
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
                        continue
                    user_tags = _load_user_tags(cur, str(user_id))
                    if not user_tags:
                        continue
                    km = keyword_match(card_tags, user_tags)
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
                    if not _send_push_message(
                        cfg,
                        chat_id,
                        text,
                        lead_id=lead_id,
                        show_generate=show_generate,
                        order_url=lead_order_url,
                    ):
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
                    err.append(
                        f"push:match:user={user_id[:8]} lead={lead_id} km={km} thr={push_min_match}"
                    )
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
