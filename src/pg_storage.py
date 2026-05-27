"""Neon Postgres: дубль лидов (опционально, если задан DATABASE_URL)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import psycopg
from contextlib import contextmanager

from ai_analyze import AiLiteAnalysis
from config import Config
from lead_category import category_for_listing
from listing import ListingProject
from public_feed import is_public_feed_source, public_feed_sources

if TYPE_CHECKING:
    from ai_analyze import AiAnalysis

logger = logging.getLogger(__name__)

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


def _ai_score_stub(analysis: AiAnalysis | None) -> int | None:
    if analysis is None:
        return None
    return _VERDICT_SCORE.get(analysis.verdict.strip().casefold(), 50)


def _ai_score_lite(lite: AiLiteAnalysis | None) -> int | None:
    if lite is None:
        return None
    return _VERDICT_SCORE.get(lite.verdict.strip().casefold(), 50)


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
    if lite.verdict.strip().casefold() in ("мимо", "пропустить"):
        return False
    score = _ai_score_lite(lite)
    cat = category.strip().casefold()
    threshold = (
        _MIN_AI_SCORE_VISIBLE_NONTECH
        if cat in ("design", "marketing", "text")
        else _MIN_AI_SCORE_VISIBLE
    )
    return score is not None and score >= threshold


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


class NeonLeadStorage:
    """Запись лидов в Postgres; ошибки не пробрасываются наружу."""

    def __init__(self, database_url: str) -> None:
        self._url = database_url.strip()

    @contextmanager
    def connection(self):
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
        category = category_for_listing(
            project.source,
            listing_category=project.listing_category,
            title=project.title,
            snippet=body_text,
        )
        params = (
            project.source,
            str(project.project_id),
            project.title,
            body_text,
            project.url,
            project.budget_text,
            json.dumps([], ensure_ascii=False),
            False,
            category,
        )
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    if h:
                        cur.execute(
                            """
                            INSERT INTO leads (
                                source, external_id, title, body, url, budget_text,
                                lead_tags, is_visible, content_hash, category
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                            ON CONFLICT (content_hash) DO NOTHING
                            RETURNING id
                            """,
                            (*params, h),
                        )
                    else:
                        cur.execute(
                            """
                            INSERT INTO leads (
                                source, external_id, title, body, url, budget_text,
                                lead_tags, is_visible, content_hash, category
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, NULL, %s)
                            ON CONFLICT (source, external_id) DO NOTHING
                            RETURNING id
                            """,
                            params,
                        )
                    inserted = cur.fetchone() is not None
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
        ai_verdict = lite.verdict if lite is not None else None
        ai_score = _ai_score_lite(lite)
        task_summary = lite.task_summary.strip() if lite is not None else None
        lead_tags = _lite_tags_json(lite)
        reasons = _lite_reasons_json(lite)
        category = category_for_listing(
            project.source,
            listing_category=project.listing_category,
            title=project.title,
            snippet=snippet,
        )
        is_visible = _is_visible_lite(lite, category) and is_public_feed_source(project.source)
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
                            category = COALESCE(NULLIF(category, ''), %s)
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
        reply = (premium.reply_draft or "").strip()
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
        errors: list[str] | None = None,
    ) -> list[NeonLeadRow]:
        """Site replay: строки без L1 из PUBLIC_FEED_SOURCES."""
        if not self.enabled:
            return []
        sources = sorted(public_feed_sources())
        if not sources:
            return []
        err = errors if errors is not None else []
        lim = max(1, min(int(limit), 500))
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, source, external_id, title, body, url,
                               budget_text, COALESCE(category, '')
                        FROM leads
                        WHERE ai_verdict IS NULL
                          AND ai_score IS NULL
                          AND source = ANY(%s)
                        ORDER BY id ASC
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
