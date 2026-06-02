"""Neon Postgres: дубль лидов (опционально, если задан DATABASE_URL)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import psycopg
from contextlib import contextmanager

from ai_analyze import AiLiteAnalysis, resolve_l1_primary_category, sanitize_l1_category
from config import Config
from lead_category import category_for_listing
from listing import ListingProject
from public_feed import FEED_VISIBILITY_DAYS, is_public_feed_source, public_feed_sources
from reply_draft_strip import strip_reply_draft_price_deadline

if TYPE_CHECKING:
    from ai_analyze import AiAnalysis

logger = logging.getLogger(__name__)

_SQL_DIR = Path(__file__).resolve().parent.parent / "sql"
_leads_columns_ready = False
_leads_columns_lock = __import__("threading").Lock()

_OWNER_USER_ID = "00000000-0000-0000-0000-000000000001"
_MIN_AI_SCORE_VISIBLE = 40
_MIN_AI_SCORE_VISIBLE_NONTECH = 50

_VERDICT_SCORE: dict[str, int] = {
    "брать": 85,
    "брат": 85,
    "сомнительно": 55,
    "пропустить": 25,
    "мимо": 15,
}


def _short_pg_err(exc: BaseException, *, max_len: int = 200) -> str:
    s = f"{type(exc).__name__}: {exc}".replace("\n", " ").strip()
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


def _ingest_category(project: ListingProject, snippet: str) -> str:
    raw = category_for_listing(
        project.source,
        listing_category=project.listing_category,
        title=project.title,
        snippet=snippet,
    )
    return sanitize_l1_category(raw, title=project.title, snippet=snippet)


def _ai_score_stub(analysis: AiAnalysis | None) -> int | None:
    if analysis is None:
        return None
    return _VERDICT_SCORE.get(analysis.verdict.strip().casefold(), 50)


def _ai_score_lite(lite: AiLiteAnalysis | None) -> int | None:
    if lite is None:
        return None
    if not lite.feed_visible:
        return _VERDICT_SCORE["мимо"]
    return _VERDICT_SCORE["брать"]


def neon_ai_verdict(lite: AiLiteAnalysis | None) -> str | None:
    """O72e-8: feed_visible → Neon ai_verdict (OK / МИМО)."""
    if lite is None:
        return None
    return "OK" if lite.feed_visible else "МИМО"


def _lite_tags_json(lite: AiLiteAnalysis | None) -> str:
    if lite is None or not lite.lead_tags:
        return json.dumps([], ensure_ascii=False)
    return json.dumps(list(lite.lead_tags), ensure_ascii=False)


def _lite_reasons_json(lite: AiLiteAnalysis | None) -> str | None:
    if lite is None or not lite.ai_reasons:
        return None
    return json.dumps(list(lite.ai_reasons), ensure_ascii=False)


def _is_visible_lite(lite: AiLiteAnalysis | None, category: str = "") -> bool:
    if lite is None:
        return True
    return lite.feed_visible


def _is_visible_stub(analysis: AiAnalysis | None) -> bool:
    """Заглушка модерации до фазы 3f: skip-вердикт или score < порога."""
    if analysis is None:
        return True
    if analysis.is_skip_verdict():
        return False
    score = _ai_score_stub(analysis)
    return score is not None and score >= _MIN_AI_SCORE_VISIBLE


def _lead_tags_json(analysis: AiAnalysis | None) -> str:
    if analysis is None or not analysis.lead_tags:
        return json.dumps([], ensure_ascii=False)
    return json.dumps(list(analysis.lead_tags), ensure_ascii=False)


@dataclass(frozen=True)
class NeonLeadLiteState:
    """Есть ли L1 в Neon (для dup-replay)."""

    ai_verdict: str | None
    ai_score: int | None

    @property
    def has_l1(self) -> bool:
        return self.ai_verdict is not None or self.ai_score is not None


@dataclass(frozen=True)
class NeonLeadRow:
    """Строка leads для legacy consumer (биржи из PUBLIC_FEED_SOURCES)."""

    lead_id: int
    source: str
    external_id: str
    title: str
    body: str
    url: str
    budget_text: str
    category: str = ""

    def to_listing(self) -> ListingProject:
        try:
            project_id = int(self.external_id)
        except ValueError:
            project_id = abs(hash((self.source, self.external_id))) % (2**31 - 1)
        return ListingProject(
            project_id=project_id,
            title=self.title,
            budget_text=self.budget_text,
            url=self.url,
            published_at="",
            listing_snippet=self.body,
            source=self.source,
            listing_category=self.category or "",
        )


def _ensure_leads_columns(database_url: str) -> None:
    global _leads_columns_ready
    if _leads_columns_ready:
        return
    with _leads_columns_lock:
        if _leads_columns_ready:
            return
        sql_files = (
            _SQL_DIR / "014_leads_delist_legacy.sql",
            _SQL_DIR / "016_leads_ingest_timestamps.sql",
        )
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                for sql_path in sql_files:
                    ddl = sql_path.read_text(encoding="utf-8") if sql_path.is_file() else ""
                    if ddl.strip():
                        cur.execute(ddl)
            conn.commit()
        _leads_columns_ready = True


def _source_bucket(source: str) -> str:
    s = (source or "").strip().lower()
    if s.startswith("tg"):
        return "tg"
    return s.split(":")[0] or s


def _parse_source_published_at(raw: str) -> datetime | None:
    text = (raw or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        pass
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y %H:%M:%S",
    ):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


class NeonLeadStorage:
    """Запись лидов в Postgres; ошибки не пробрасываются наружу."""

    def __init__(self, database_url: str) -> None:
        self._url = database_url.strip()

    @contextmanager
    def connection(self):
        _ensure_leads_columns(self._url)
        with psycopg.connect(self._url) as conn:
            yield conn

    @property
    def enabled(self) -> bool:
        return bool(self._url)

    def record_new_lead(
        self,
        project: ListingProject,
        errors: list[str],
        *,
        content_hash: str = "",
        body: str = "",
    ) -> bool:
        """
        INSERT ON CONFLICT DO NOTHING.
        True — новая запись; False — дубль (content_hash или source+external_id).
        Пустой content_hash — только UNIQUE (source, external_id).
        """
        if not self.enabled:
            return True
        h = (content_hash or "").strip() or None
        body_text = (body or project.listing_snippet or project.title or "").strip()
        category = _ingest_category(project, body_text)
        source_published_at = _parse_source_published_at(project.published_at)
        base_params = (
            project.source,
            str(project.project_id),
            project.title,
            body_text,
            project.url,
            project.budget_text,
            json.dumps([], ensure_ascii=False),
            False,
            category,
            source_published_at,
        )
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    if h:
                        params_with_hash = (
                            *base_params[:8],
                            h,
                            base_params[8],
                            base_params[9],
                        )
                        cur.execute(
                            """
                            INSERT INTO leads (
                                source, external_id, title, body, url, budget_text,
                                lead_tags, is_visible, content_hash, category,
                                source_published_at, last_fetch_ok_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, NOW())
                            ON CONFLICT (content_hash) DO NOTHING
                            RETURNING id
                            """,
                            params_with_hash,
                        )
                    else:
                        cur.execute(
                            """
                            INSERT INTO leads (
                                source, external_id, title, body, url, budget_text,
                                lead_tags, is_visible, content_hash, category,
                                source_published_at, last_fetch_ok_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, NULL, %s, %s, NOW())
                            ON CONFLICT (source, external_id) DO NOTHING
                            RETURNING id
                            """,
                            base_params,
                        )
                    inserted = cur.fetchone() is not None
                    if not inserted and h:
                        cur.execute(
                            """
                            SELECT source FROM leads
                            WHERE content_hash = %s
                            LIMIT 1
                            """,
                            (h,),
                        )
                        row = cur.fetchone()
                        if row and row[0] != project.source:
                            msg = (
                                f"cross_source_dup:winner={row[0]} "
                                f"hash={h[:8]} skip={project.source}:id={project.project_id}"
                            )
                            logger.info("%s", msg)
                            errors.append(msg)
                return inserted
        except Exception as exc:
            msg = f"pg:record:{project.source}:id={project.project_id}:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            errors.append(msg)
            return True

    def lead_exists(
        self,
        source: str,
        external_id: str,
        errors: list[str] | None = None,
    ) -> bool:
        """Есть ли строка leads по (source, external_id)."""
        if not self.enabled:
            return False
        src = (source or "").strip()
        eid = (external_id or "").strip()
        if not src or not eid:
            return False
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT 1 FROM leads
                        WHERE source = %s AND external_id = %s
                        LIMIT 1
                        """,
                        (src, eid),
                    )
                    return cur.fetchone() is not None
        except Exception as exc:
            msg = f"pg:exists:{src}:{eid}:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return False

    def external_ids_in_neon(
        self,
        source: str,
        external_ids: list[str],
        errors: list[str] | None = None,
    ) -> set[str]:
        """Подмножество external_id, уже присутствующих в Neon для source."""
        if not self.enabled or not external_ids:
            return set()
        src = (source or "").strip()
        if not src:
            return set()
        ids = [str(x).strip() for x in external_ids if str(x).strip()]
        if not ids:
            return set()
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT external_id FROM leads
                        WHERE source = %s AND external_id = ANY(%s)
                        """,
                        (src, ids),
                    )
                    return {str(r[0]) for r in cur.fetchall()}
        except Exception as exc:
            msg = f"pg:ext_ids:{src}:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return set()

    def fetch_lead_lite_state(
        self,
        *,
        content_hash: str = "",
        source: str = "",
        external_id: str = "",
        errors: list[str] | None = None,
    ) -> NeonLeadLiteState | None:
        """Строка leads для dup-replay: ai_verdict / ai_score."""
        if not self.enabled:
            return None
        h = (content_hash or "").strip() or None
        src = (source or "").strip()
        eid = (external_id or "").strip()
        if not h and not (src and eid):
            return None
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    if h:
                        cur.execute(
                            """
                            SELECT ai_verdict, ai_score
                            FROM leads
                            WHERE content_hash = %s
                            LIMIT 1
                            """,
                            (h,),
                        )
                    else:
                        cur.execute(
                            """
                            SELECT ai_verdict, ai_score
                            FROM leads
                            WHERE source = %s AND external_id = %s
                            LIMIT 1
                            """,
                            (src, eid),
                        )
                    row = cur.fetchone()
            if row is None:
                return None
            return NeonLeadLiteState(
                ai_verdict=row[0] if row[0] is not None else None,
                ai_score=int(row[1]) if row[1] is not None else None,
            )
        except Exception as exc:
            msg = f"pg:fetch_lite:{src}:{eid}:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return None

    def update_after_lite(
        self,
        project: ListingProject,
        *,
        lite: AiLiteAnalysis | None,
        errors: list[str],
        body_snippet: str,
    ) -> None:
        """После L1: поля ленты (не перезаписывать полным FL-body)."""
        if not self.enabled:
            return
        snippet = (body_snippet or project.listing_snippet or project.title or "").strip()
        ai_verdict = neon_ai_verdict(lite)
        ai_score = _ai_score_lite(lite)
        task_summary = lite.task_summary.strip() if lite is not None else None
        lead_tags = _lite_tags_json(lite)
        reasons = _lite_reasons_json(lite)
        if lite is not None:
            category = resolve_l1_primary_category(
                lite.primary_category,
                lite.lead_tags,
                title=project.title,
                snippet=snippet,
            )
        else:
            category = _ingest_category(project, snippet)
        is_visible = _is_visible_lite(lite, category) and is_public_feed_source(project.source)
        if lite is not None and lite.pending_tags:
            self.record_pending_tags(list(lite.pending_tags), category=category)
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE leads
                        SET body = %s,
                            ai_verdict = %s,
                            ai_score = %s,
                            lead_tags = %s::jsonb,
                            ai_reasons = %s::jsonb,
                            task_summary = COALESCE(%s, task_summary),
                            is_visible = %s,
                            category = %s,
                            l1_completed_at = NOW()
                        WHERE source = %s AND external_id = %s
                        """,
                        (
                            snippet,
                            ai_verdict,
                            ai_score,
                            lead_tags,
                            reasons,
                            task_summary,
                            is_visible,
                            category,
                            project.source,
                            str(project.project_id),
                        ),
                    )
        except Exception as exc:
            msg = (
                f"pg:lite:{project.source}:id={project.project_id}:"
                f"{_short_pg_err(exc)}"
            )
            logger.warning("%s", msg)
            errors.append(msg)

    def fetch_lead_id(
        self,
        source: str,
        external_id: str,
        errors: list[str] | None = None,
    ) -> int | None:
        """id строки leads по (source, external_id) — для match push после L1."""
        if not self.enabled:
            return None
        src = (source or "").strip()
        eid = (external_id or "").strip()
        if not src or not eid:
            return None
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id FROM leads
                        WHERE source = %s AND external_id = %s
                        LIMIT 1
                        """,
                        (src, eid),
                    )
                    row = cur.fetchone()
            return int(row[0]) if row else None
        except Exception as exc:
            msg = f"pg:lead_id:{src}:{eid}:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return None

    def mark_l1_failed(
        self,
        project: ListingProject,
        errors: list[str],
        *,
        body_snippet: str = "",
    ) -> None:
        """Терминал после retry L1: не попадает в count_leads_missing_l1."""
        if not self.enabled:
            return
        snippet = (body_snippet or project.listing_snippet or project.title or "").strip()
        category = _ingest_category(project, snippet)
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE leads
                        SET body = %s,
                            ai_verdict = 'l1_failed',
                            ai_score = 0,
                            is_visible = FALSE,
                            category = COALESCE(NULLIF(category, ''), %s)
                        WHERE source = %s AND external_id = %s
                        """,
                        (
                            snippet,
                            category,
                            project.source,
                            str(project.project_id),
                        ),
                    )
        except Exception as exc:
            msg = (
                f"pg:l1_failed:{project.source}:id={project.project_id}:"
                f"{_short_pg_err(exc)}"
            )
            logger.warning("%s", msg)
            errors.append(msg)

    def record_pending_tags(
        self,
        tags: list[str],
        *,
        category: str | None = None,
    ) -> None:
        """Теги L1 вне canonical pool → очередь review (не в UI)."""
        if not self.enabled or not tags:
            return
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    for tag in tags:
                        t = str(tag).strip().lower().lstrip("#")
                        if not t:
                            continue
                        cur.execute(
                            """
                            INSERT INTO pending_tags (tag, category, seen_count)
                            VALUES (%s, %s, 1)
                            ON CONFLICT (tag) DO UPDATE SET
                                seen_count = pending_tags.seen_count + 1,
                                category = COALESCE(EXCLUDED.category, pending_tags.category)
                            """,
                            (t, category),
                        )
        except Exception as exc:
            msg = f"pg:pending_tags:{_short_pg_err(exc)}"
            logger.warning("%s", msg)

    def update_after_premium(
        self,
        project: ListingProject,
        *,
        premium: AiAnalysis,
        errors: list[str],
    ) -> None:
        """После L2: инструменты и черновик отклика для кабинета подписчика."""
        if not self.enabled:
            return
        tools_json = json.dumps(list(premium.tools_required), ensure_ascii=False)
        reply = strip_reply_draft_price_deadline((premium.reply_draft or "").strip())
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE leads
                        SET tools_required = %s::jsonb,
                            reply_draft = COALESCE(NULLIF(%s, ''), reply_draft)
                        WHERE source = %s AND external_id = %s
                        """,
                        (
                            tools_json,
                            reply,
                            project.source,
                            str(project.project_id),
                        ),
                    )
        except Exception as exc:
            msg = (
                f"pg:premium:{project.source}:id={project.project_id}:"
                f"{_short_pg_err(exc)}"
            )
            logger.warning("%s", msg)
            errors.append(msg)

    def fetch_exchange_leads_after(
        self,
        after_id: int,
        *,
        limit: int = 40,
        errors: list[str] | None = None,
    ) -> list[NeonLeadRow]:
        """Новые лиды бирж (fl/kwork/…) для legacy consumer; только SELECT."""
        if not self.enabled:
            return []
        sources = sorted(public_feed_sources())
        if not sources:
            return []
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, source, external_id, title, body, url,
                               budget_text, COALESCE(category, '')
                        FROM leads
                        WHERE id > %s AND source = ANY(%s)
                        ORDER BY id ASC
                        LIMIT %s
                        """,
                        (after_id, sources, limit),
                    )
                    rows = cur.fetchall()
            return [
                NeonLeadRow(
                    lead_id=int(r[0]),
                    source=str(r[1]),
                    external_id=str(r[2]),
                    title=str(r[3] or ""),
                    body=str(r[4] or ""),
                    url=str(r[5] or ""),
                    budget_text=str(r[6] or ""),
                    category=str(r[7] or ""),
                )
                for r in rows
            ]
        except Exception as exc:
            msg = f"pg:fetch_legacy:after={after_id}:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return []

    def fetch_leads_missing_l1(
        self,
        *,
        limit: int = 50,
        order_desc: bool = True,
        errors: list[str] | None = None,
    ) -> list[NeonLeadRow]:
        """Site replay / конвейер: строки без L1 из PUBLIC_FEED_SOURCES."""
        if not self.enabled:
            return []
        sources = sorted(public_feed_sources())
        if not sources:
            return []
        err = errors if errors is not None else []
        lim = max(1, min(int(limit), 500))
        order_sql = "DESC" if order_desc else "ASC"
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        SELECT id, source, external_id, title, body, url,
                               budget_text, COALESCE(category, '')
                        FROM leads
                        WHERE ai_verdict IS NULL
                          AND ai_score IS NULL
                          AND source = ANY(%s)
                        ORDER BY id {order_sql}
                        LIMIT %s
                        """,
                        (sources, lim),
                    )
                    rows = cur.fetchall()
            return [
                NeonLeadRow(
                    lead_id=int(r[0]),
                    source=str(r[1]),
                    external_id=str(r[2]),
                    title=str(r[3] or ""),
                    body=str(r[4] or ""),
                    url=str(r[5] or ""),
                    budget_text=str(r[6] or ""),
                    category=str(r[7] or ""),
                )
                for r in rows
            ]
        except Exception as exc:
            msg = f"pg:fetch_missing_l1:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return []

    def fetch_leads_missing_tools(
        self,
        *,
        limit: int = 20,
        errors: list[str] | None = None,
    ) -> list[NeonLeadRow]:
        """Visible leads без tools_required (Site L2 backfill)."""
        if not self.enabled:
            return []
        sources = sorted(public_feed_sources())
        if not sources:
            return []
        err = errors if errors is not None else []
        lim = max(1, min(int(limit), 100))
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, source, external_id, title,
                               COALESCE(NULLIF(task_summary, ''), body) AS body,
                               url, budget_text, COALESCE(category, '')
                        FROM leads
                        WHERE is_visible = TRUE
                          AND source = ANY(%s)
                          AND ai_verdict IS NOT NULL
                          AND (
                            tools_required IS NULL
                            OR tools_required = '[]'::jsonb
                            OR jsonb_array_length(tools_required) = 0
                          )
                          AND COALESCE(task_summary, '') <> ''
                        ORDER BY id DESC
                        LIMIT %s
                        """,
                        (sources, lim),
                    )
                    rows = cur.fetchall()
            return [
                NeonLeadRow(
                    lead_id=int(r[0]),
                    source=str(r[1]),
                    external_id=str(r[2]),
                    title=str(r[3] or ""),
                    body=str(r[4] or ""),
                    url=str(r[5] or ""),
                    budget_text=str(r[6] or ""),
                    category=str(r[7] or ""),
                )
                for r in rows
            ]
        except Exception as exc:
            msg = f"pg:fetch_missing_tools:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return []

    def update_tools_required(
        self,
        source: str,
        external_id: str,
        tools: list[str],
        *,
        errors: list[str] | None = None,
    ) -> bool:
        if not self.enabled or not tools:
            return False
        err = errors if errors is not None else []
        tools_json = json.dumps(list(tools), ensure_ascii=False)
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE leads
                        SET tools_required = %s::jsonb
                        WHERE source = %s AND external_id = %s
                        """,
                        (tools_json, source, external_id),
                    )
                    return cur.rowcount > 0
        except Exception as exc:
            msg = f"pg:tools:{source}:{external_id}:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return False

    def count_leads_missing_l1(self, errors: list[str] | None = None) -> int:
        """Очередь без L1 (PUBLIC_FEED_SOURCES) — для § FEED-FRESHNESS."""
        if not self.enabled:
            return 0
        sources = sorted(public_feed_sources())
        if not sources:
            return 0
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT COUNT(*)
                        FROM leads
                        WHERE ai_verdict IS NULL
                          AND ai_score IS NULL
                          AND source = ANY(%s)
                        """,
                        (sources,),
                    )
                    row = cur.fetchone()
                    return int(row[0]) if row else 0
        except Exception as exc:
            msg = f"pg:count_missing_l1:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return 0

    def count_leads_missing_l1_recent(
        self, hours: int = 48, errors: list[str] | None = None
    ) -> int:
        """Без L1 за последние N часов (свежий хвост для /status)."""
        if not self.enabled:
            return 0
        sources = sorted(public_feed_sources())
        if not sources:
            return 0
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT COUNT(*)
                        FROM leads
                        WHERE ai_verdict IS NULL
                          AND ai_score IS NULL
                          AND source = ANY(%s)
                          AND created_at >= NOW() - make_interval(hours => %s)
                        """,
                        (sources, int(hours)),
                    )
                    row = cur.fetchone()
                    return int(row[0]) if row else 0
        except Exception as exc:
            msg = f"pg:count_missing_l1_recent:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return 0

    def clear_l1_backlog_tail(
        self,
        *,
        hours_protect: int = 48,
        top_ids_protect: int = 100,
        dry_run: bool = True,
        errors: list[str] | None = None,
        days_old: int | None = None,
        by_age: bool = False,
    ) -> dict[str, int]:
        """§ BACKLOG-CLEAR / BACKLOG-TAIL-CLEAR-O40: пометить старый хвост без L1.

        by_age=True + days_old=N: чистить только created_at < NOW()-N дней;
          защита — только hours_protect (top_ids_protect игнорируется).
        Legacy (by_age=False): как раньше — top_ids_protect + hours_protect.
        """
        if not self.enabled:
            return {
                "missing_before": 0,
                "older_than_Nd": 0,
                "protected": 0,
                "to_clear": 0,
                "cleared": 0,
                "missing_after": 0,
            }
        sources = sorted(public_feed_sources())
        if not sources:
            return {
                "missing_before": 0,
                "older_than_Nd": 0,
                "protected": 0,
                "to_clear": 0,
                "cleared": 0,
                "missing_after": 0,
            }
        err = errors if errors is not None else []
        if by_age:
            reasons_json = json.dumps(["backlog_cleared_age"], ensure_ascii=False)
        else:
            reasons_json = json.dumps(["backlog_cleared"], ensure_ascii=False)
        stats = {
            "missing_before": 0,
            "older_than_Nd": 0,
            "protected": 0,
            "to_clear": 0,
            "cleared": 0,
            "missing_after": 0,
        }
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT COUNT(*)
                        FROM leads
                        WHERE ai_verdict IS NULL
                          AND ai_score IS NULL
                          AND source = ANY(%s)
                        """,
                        (sources,),
                    )
                    row = cur.fetchone()
                    stats["missing_before"] = int(row[0]) if row else 0

                    if by_age and days_old is not None:
                        # Режим --by-age: кандидаты — только строки старше days_old дней
                        cur.execute(
                            """
                            SELECT COUNT(*)
                            FROM leads
                            WHERE ai_verdict IS NULL
                              AND ai_score IS NULL
                              AND source = ANY(%s)
                              AND created_at < NOW() - make_interval(days => %s)
                            """,
                            (sources, int(days_old)),
                        )
                        row = cur.fetchone()
                        stats["older_than_Nd"] = int(row[0]) if row else 0

                        cur.execute(
                            """
                            WITH missing AS (
                                SELECT id, created_at
                                FROM leads
                                WHERE ai_verdict IS NULL
                                  AND ai_score IS NULL
                                  AND source = ANY(%s)
                                  AND created_at < NOW() - make_interval(days => %s)
                            ),
                            protected AS (
                                SELECT id FROM missing
                                WHERE created_at >= NOW() - make_interval(hours => %s)
                            ),
                            to_clear AS (
                                SELECT id FROM missing
                                WHERE id NOT IN (SELECT id FROM protected)
                            )
                            SELECT
                                (SELECT COUNT(*) FROM protected),
                                (SELECT COUNT(*) FROM to_clear)
                            """,
                            (sources, int(days_old), int(hours_protect)),
                        )
                        prow = cur.fetchone()
                        stats["protected"] = int(prow[0]) if prow else 0
                        stats["to_clear"] = int(prow[1]) if prow else 0

                        if not dry_run and stats["to_clear"] > 0:
                            cur.execute(
                                """
                                WITH missing AS (
                                    SELECT id, created_at
                                    FROM leads
                                    WHERE ai_verdict IS NULL
                                      AND ai_score IS NULL
                                      AND source = ANY(%s)
                                      AND created_at < NOW() - make_interval(days => %s)
                                ),
                                protected AS (
                                    SELECT id FROM missing
                                    WHERE created_at >= NOW() - make_interval(hours => %s)
                                )
                                UPDATE leads
                                SET ai_verdict = 'Пропущено',
                                    ai_score = 0,
                                    is_visible = FALSE,
                                    ai_reasons = %s::jsonb
                                WHERE id IN (
                                    SELECT id FROM missing
                                    WHERE id NOT IN (SELECT id FROM protected)
                                )
                                """,
                                (
                                    sources,
                                    int(days_old),
                                    int(hours_protect),
                                    reasons_json,
                                ),
                            )
                            stats["cleared"] = cur.rowcount
                    else:
                        # Legacy режим: top_ids_protect + hours_protect
                        cur.execute(
                            """
                            WITH missing AS (
                                SELECT id, created_at
                                FROM leads
                                WHERE ai_verdict IS NULL
                                  AND ai_score IS NULL
                                  AND source = ANY(%s)
                            ),
                            protected AS (
                                SELECT id FROM missing
                                WHERE created_at >= NOW() - make_interval(hours => %s)
                                UNION
                                SELECT id FROM (
                                    SELECT id FROM missing
                                    ORDER BY id DESC
                                    LIMIT %s
                                ) recent_top
                            ),
                            to_clear AS (
                                SELECT id FROM missing
                                WHERE id NOT IN (SELECT id FROM protected)
                            )
                            SELECT
                                (SELECT COUNT(*) FROM protected),
                                (SELECT COUNT(*) FROM to_clear)
                            """,
                            (sources, int(hours_protect), int(top_ids_protect)),
                        )
                        prow = cur.fetchone()
                        stats["protected"] = int(prow[0]) if prow else 0
                        stats["to_clear"] = int(prow[1]) if prow else 0

                        if not dry_run and stats["to_clear"] > 0:
                            cur.execute(
                                """
                                WITH missing AS (
                                    SELECT id, created_at
                                    FROM leads
                                    WHERE ai_verdict IS NULL
                                      AND ai_score IS NULL
                                      AND source = ANY(%s)
                                ),
                                protected AS (
                                    SELECT id FROM missing
                                    WHERE created_at >= NOW() - make_interval(hours => %s)
                                    UNION
                                    SELECT id FROM (
                                        SELECT id FROM missing
                                        ORDER BY id DESC
                                        LIMIT %s
                                    ) recent_top
                                )
                                UPDATE leads
                                SET ai_verdict = 'Пропущено',
                                    ai_score = 0,
                                    is_visible = FALSE,
                                    ai_reasons = %s::jsonb
                                WHERE id IN (
                                    SELECT id FROM missing
                                    WHERE id NOT IN (SELECT id FROM protected)
                                )
                                """,
                                (
                                    sources,
                                    int(hours_protect),
                                    int(top_ids_protect),
                                    reasons_json,
                                ),
                            )
                            stats["cleared"] = cur.rowcount

                    cur.execute(
                        """
                        SELECT COUNT(*)
                        FROM leads
                        WHERE ai_verdict IS NULL
                          AND ai_score IS NULL
                          AND source = ANY(%s)
                        """,
                        (sources,),
                    )
                    row = cur.fetchone()
                    stats["missing_after"] = int(row[0]) if row else 0
            return stats
        except Exception as exc:
            msg = f"pg:clear_l1_backlog:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return stats

    def max_lead_id(self, errors: list[str] | None = None) -> int:
        if not self.enabled:
            return 0
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COALESCE(MAX(id), 0) FROM leads")
                    row = cur.fetchone()
                    return int(row[0]) if row else 0
        except Exception as exc:
            msg = f"pg:max_id:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return 0

    def ingest_lag_report(
        self,
        *,
        lookback_hours: int = 24,
        errors: list[str] | None = None,
    ) -> dict[str, dict[str, float | int]]:
        """O90: p50/p95 ingest/l1/feed lag по источникам."""
        out: dict[str, dict[str, float | int]] = {}
        if not self.enabled:
            return out
        err = errors if errors is not None else []
        lookback = max(1, min(int(lookback_hours), 24 * 30))
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        WITH lag_rows AS (
                          SELECT
                            CASE
                              WHEN source LIKE 'tg:%%' THEN 'tg'
                              ELSE split_part(source, ':', 1)
                            END AS source_bucket,
                            EXTRACT(EPOCH FROM (created_at - source_published_at)) AS ingest_lag_sec,
                            EXTRACT(EPOCH FROM (l1_completed_at - created_at)) AS l1_lag_sec,
                            EXTRACT(
                              EPOCH FROM (
                                COALESCE(l1_completed_at, created_at) - source_published_at
                              )
                            ) AS feed_lag_sec
                          FROM leads
                          WHERE created_at >= NOW() - make_interval(hours => %s)
                            AND source_published_at IS NOT NULL
                        )
                        SELECT
                          source_bucket,
                          COUNT(*)::int,
                          percentile_cont(0.5) WITHIN GROUP (ORDER BY ingest_lag_sec),
                          percentile_cont(0.95) WITHIN GROUP (ORDER BY ingest_lag_sec),
                          percentile_cont(0.5) WITHIN GROUP (ORDER BY l1_lag_sec)
                            FILTER (WHERE l1_lag_sec IS NOT NULL),
                          percentile_cont(0.95) WITHIN GROUP (ORDER BY l1_lag_sec)
                            FILTER (WHERE l1_lag_sec IS NOT NULL),
                          percentile_cont(0.5) WITHIN GROUP (ORDER BY feed_lag_sec),
                          percentile_cont(0.95) WITHIN GROUP (ORDER BY feed_lag_sec)
                        FROM lag_rows
                        GROUP BY source_bucket
                        ORDER BY source_bucket
                        """,
                        (lookback,),
                    )
                    for row in cur.fetchall():
                        bucket = str(row[0] or "")
                        if not bucket:
                            continue
                        out[bucket] = {
                            "count": int(row[1] or 0),
                            "ingest_p50_sec": float(row[2] or 0.0),
                            "ingest_p95_sec": float(row[3] or 0.0),
                            "l1_p50_sec": float(row[4] or 0.0),
                            "l1_p95_sec": float(row[5] or 0.0),
                            "feed_p50_sec": float(row[6] or 0.0),
                            "feed_p95_sec": float(row[7] or 0.0),
                        }
            return out
        except Exception as exc:
            msg = f"pg:ingest_lag_report:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return out

    def ingest_ops_snapshot(self, errors: list[str] | None = None) -> dict[str, dict[str, int | str]]:
        """O90: данные для /ops/ — lag/last insert/backlog по источникам."""
        out: dict[str, dict[str, int | str]] = {}
        if not self.enabled:
            return out
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        WITH base AS (
                          SELECT
                            CASE
                              WHEN source LIKE 'tg:%%' THEN 'tg'
                              ELSE split_part(source, ':', 1)
                            END AS source_bucket,
                            created_at,
                            l1_completed_at
                          FROM leads
                          WHERE source IS NOT NULL
                        )
                        SELECT
                          source_bucket,
                          EXTRACT(EPOCH FROM (NOW() - MAX(created_at)))::int AS last_insert_gap_sec,
                          TO_CHAR(MAX(created_at) AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS "UTC"') AS last_insert_at,
                          COUNT(*) FILTER (
                            WHERE l1_completed_at IS NULL
                              AND created_at >= NOW() - INTERVAL '48 hours'
                          )::int AS backlog
                        FROM base
                        GROUP BY source_bucket
                        ORDER BY source_bucket
                        """
                    )
                    for row in cur.fetchall():
                        bucket = str(row[0] or "")
                        if not bucket:
                            continue
                        out[bucket] = {
                            "last_insert_gap_sec": int(row[1] or 0),
                            "last_insert_at": str(row[2] or ""),
                            "backlog": int(row[3] or 0),
                        }
            return out
        except Exception as exc:
            msg = f"pg:ingest_ops_snapshot:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return out

    def last_visible_created_at(self, errors: list[str] | None = None) -> str | None:
        """MAX(created_at) для is_visible=true — свежесть ленты."""
        if not self.enabled:
            return None
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT MAX(created_at)
                        FROM leads
                        WHERE is_visible = TRUE
                        """
                    )
                    row = cur.fetchone()
                    if not row or row[0] is None:
                        return None
                    ts = row[0]
                    if isinstance(ts, datetime):
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                        return ts.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    return str(ts)
        except Exception as exc:
            msg = f"pg:last_visible:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return None

    def count_l1_backlog_by_source(
        self,
        *,
        hours: int = 48,
        errors: list[str] | None = None,
    ) -> dict[str, int]:
        """Без L1 за N часов — breakdown fl/kwork/tg (O64)."""
        out = {"fl": 0, "kwork": 0, "tg": 0}
        if not self.enabled:
            return out
        sources = sorted(public_feed_sources())
        if not sources:
            return out
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT source, COUNT(*)
                        FROM leads
                        WHERE ai_verdict IS NULL
                          AND ai_score IS NULL
                          AND source = ANY(%s)
                          AND created_at >= NOW() - make_interval(hours => %s)
                        GROUP BY source
                        """,
                        (sources, int(hours)),
                    )
                    for row in cur.fetchall():
                        bucket = _source_bucket(str(row[0] or ""))
                        if bucket in out:
                            out[bucket] += int(row[1] or 0)
            return out
        except Exception as exc:
            msg = f"pg:count_l1_by_source:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return out

    def l1_backlog_age_buckets(
        self,
        *,
        errors: list[str] | None = None,
    ) -> dict[str, int]:
        """Без L1 — bucket по возрасту (O64 report)."""
        buckets = {"0-24h": 0, "1-2d": 0, "2-7d": 0, ">7d": 0}
        if not self.enabled:
            return buckets
        sources = sorted(public_feed_sources())
        if not sources:
            return buckets
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                          CASE
                            WHEN created_at >= NOW() - INTERVAL '24 hours' THEN '0-24h'
                            WHEN created_at >= NOW() - INTERVAL '2 days' THEN '1-2d'
                            WHEN created_at >= NOW() - INTERVAL '7 days' THEN '2-7d'
                            ELSE '>7d'
                          END AS bucket,
                          COUNT(*)
                        FROM leads
                        WHERE ai_verdict IS NULL
                          AND ai_score IS NULL
                          AND source = ANY(%s)
                        GROUP BY 1
                        """,
                        (sources,),
                    )
                    for row in cur.fetchall():
                        key = str(row[0] or "")
                        if key in buckets:
                            buckets[key] = int(row[1] or 0)
            return buckets
        except Exception as exc:
            msg = f"pg:l1_age_buckets:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return buckets

    def l1_backlog_sample_ids(
        self,
        *,
        limit: int = 5,
        errors: list[str] | None = None,
    ) -> list[int]:
        if not self.enabled:
            return []
        sources = sorted(public_feed_sources())
        if not sources:
            return []
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id
                        FROM leads
                        WHERE ai_verdict IS NULL
                          AND ai_score IS NULL
                          AND source = ANY(%s)
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (sources, int(limit)),
                    )
                    return [int(r[0]) for r in cur.fetchall()]
        except Exception as exc:
            msg = f"pg:l1_sample:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return []

    def fetch_visible_unnotified_legacy(
        self,
        *,
        limit: int = 40,
        errors: list[str] | None = None,
    ) -> list[NeonLeadRow]:
        """Visible leads ещё не отправленные в @FLPARSINGBOT (O66)."""
        if not self.enabled:
            return []
        sources = sorted(public_feed_sources())
        if not sources:
            return []
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, source, external_id, title, body, url,
                               budget_text, COALESCE(category, '')
                        FROM leads
                        WHERE is_visible = TRUE
                          AND legacy_notified_at IS NULL
                          AND source = ANY(%s)
                        ORDER BY id ASC
                        LIMIT %s
                        """,
                        (sources, limit),
                    )
                    rows = cur.fetchall()
            return [
                NeonLeadRow(
                    lead_id=int(r[0]),
                    source=str(r[1]),
                    external_id=str(r[2]),
                    title=str(r[3] or ""),
                    body=str(r[4] or ""),
                    url=str(r[5] or ""),
                    budget_text=str(r[6] or ""),
                    category=str(r[7] or ""),
                )
                for r in rows
            ]
        except Exception as exc:
            msg = f"pg:fetch_legacy_visible:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return []

    def mark_legacy_notified(
        self,
        lead_id: int,
        *,
        errors: list[str] | None = None,
    ) -> None:
        if not self.enabled:
            return
        err = errors if errors is not None else []
        notified_at = datetime.now(timezone.utc)
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE leads
                        SET legacy_notified_at = %s
                        WHERE id = %s
                        """,
                        (notified_at, int(lead_id)),
                    )
        except Exception as exc:
            msg = f"pg:legacy_notify:id={lead_id}:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)

    def legacy_visible_lag_sec(
        self,
        errors: list[str] | None = None,
    ) -> int | None:
        """Секунды с created_at самого старого visible без legacy_notified_at."""
        if not self.enabled:
            return None
        sources = sorted(public_feed_sources())
        if not sources:
            return None
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT EXTRACT(EPOCH FROM (NOW() - MIN(created_at)))
                        FROM leads
                        WHERE is_visible = TRUE
                          AND legacy_notified_at IS NULL
                          AND source = ANY(%s)
                        """,
                        (sources,),
                    )
                    row = cur.fetchone()
                    if not row or row[0] is None:
                        return None
                    return int(float(row[0]))
        except Exception as exc:
            msg = f"pg:legacy_lag:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return None

    def hide_feed_older_than(
        self,
        *,
        days: int = FEED_VISIBILITY_DAYS,
        limit: int = 200,
        errors: list[str] | None = None,
    ) -> int:
        """O75: скрыть из ленты лиды старше days (не DELETE)."""
        if not self.enabled:
            return 0
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE leads
                        SET is_visible = FALSE,
                            delist_reason = 'feed_retention_7d'
                        WHERE id IN (
                            SELECT id FROM leads
                            WHERE is_visible = TRUE
                              AND created_at < NOW() - make_interval(days => %s)
                            ORDER BY created_at ASC
                            LIMIT %s
                        )
                        """,
                        (int(days), int(limit)),
                    )
                    return int(cur.rowcount or 0)
        except Exception as exc:
            msg = f"pg:hide_feed_age:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return 0

    def fetch_visible_for_source_recheck(
        self,
        *,
        limit: int = 20,
        errors: list[str] | None = None,
    ) -> list[tuple[int, str, str]]:
        """(id, source, url) visible leads для delist batch (O65)."""
        if not self.enabled:
            return []
        sources = sorted(public_feed_sources())
        if not sources:
            return []
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, source, url
                        FROM leads
                        WHERE is_visible = TRUE
                          AND delist_reason IS NULL
                          AND source = ANY(%s)
                          AND url <> ''
                          AND created_at >= NOW() - make_interval(days => %s)
                        ORDER BY last_source_check_at NULLS FIRST, created_at DESC
                        LIMIT %s
                        """,
                        (sources, FEED_VISIBILITY_DAYS, int(limit)),
                    )
                    return [
                        (int(r[0]), str(r[1]), str(r[2] or ""))
                        for r in cur.fetchall()
                    ]
        except Exception as exc:
            msg = f"pg:fetch_recheck:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return []

    def mark_source_checked(self, lead_id: int, *, errors: list[str] | None = None) -> None:
        if not self.enabled:
            return
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE leads
                        SET last_source_check_at = NOW()
                        WHERE id = %s
                        """,
                        (int(lead_id),),
                    )
        except Exception as exc:
            msg = f"pg:source_check:id={lead_id}:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)

    def delist_lead(
        self,
        lead_id: int,
        *,
        reason: str = "source_gone",
        errors: list[str] | None = None,
    ) -> bool:
        if not self.enabled:
            return False
        err = errors if errors is not None else []
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE leads
                        SET is_visible = FALSE,
                            delist_reason = %s,
                            last_source_check_at = NOW()
                        WHERE id = %s AND is_visible = TRUE
                        """,
                        (reason, int(lead_id)),
                    )
                    return cur.rowcount > 0
        except Exception as exc:
            msg = f"pg:delist:id={lead_id}:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            err.append(msg)
            return False

    def mark_notified(
        self,
        project: ListingProject,
        *,
        errors: list[str],
    ) -> None:
        """После TG: только notified_at (L1-поля ленты не трогаем)."""
        if not self.enabled:
            return
        notified_at = datetime.now(timezone.utc)
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE leads
                        SET notified_at = %s
                        WHERE source = %s AND external_id = %s
                        """,
                        (
                            notified_at,
                            project.source,
                            str(project.project_id),
                        ),
                    )
        except Exception as exc:
            msg = (
                f"pg:notify:{project.source}:id={project.project_id}:"
                f"{_short_pg_err(exc)}"
            )
            logger.warning("%s", msg)
            errors.append(msg)


def pg_storage_from_config(cfg: Config) -> NeonLeadStorage | None:
    """None — только SQLite (DATABASE_URL пуст)."""
    if not cfg.database_url:
        return None
    return NeonLeadStorage(cfg.database_url)


def owner_user_id() -> str:
    """Фиксированный UUID владельца (seed users id=#1)."""
    return _OWNER_USER_ID
