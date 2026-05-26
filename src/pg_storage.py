"""Neon Postgres: дубль лидов (опционально, если задан DATABASE_URL)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import psycopg

from config import Config
from lead_category import category_for_listing
from listing import ListingProject
from public_feed import is_public_feed_source
if TYPE_CHECKING:
    from ai_analyze import AiAnalysis

logger = logging.getLogger(__name__)

_OWNER_USER_ID = "00000000-0000-0000-0000-000000000001"
_MIN_AI_SCORE_VISIBLE = 40

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


class NeonLeadStorage:
    """Запись лидов в Postgres; ошибки не пробрасываются наружу."""

    def __init__(self, database_url: str) -> None:
        self._url = database_url.strip()

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
            with psycopg.connect(self._url) as conn:
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
                conn.commit()
                return inserted
        except Exception as exc:
            msg = f"pg:record:{project.source}:id={project.project_id}:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            errors.append(msg)
            return True

    def update_on_notify(
        self,
        project: ListingProject,
        *,
        analysis: AiAnalysis | None,
        errors: list[str],
        body: str = "",
    ) -> None:
        """После отправки в TG — ИИ-поля, is_visible, время уведомления."""
        if not self.enabled:
            return
        ai_verdict = analysis.verdict if analysis is not None else None
        ai_score = _ai_score_stub(analysis)
        is_visible = _is_visible_stub(analysis) and is_public_feed_source(
            project.source
        )
        lead_tags = _lead_tags_json(analysis)
        body_text = (body or project.listing_snippet or project.title or "").strip()
        category = category_for_listing(
            project.source,
            listing_category=project.listing_category,
            title=project.title,
            snippet=body_text,
        )
        notified_at = datetime.now(timezone.utc)
        try:
            with psycopg.connect(self._url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE leads
                        SET title = %s,
                            body = %s,
                            url = %s,
                            budget_text = %s,
                            ai_verdict = %s,
                            ai_score = %s,
                            lead_tags = %s::jsonb,
                            is_visible = %s,
                            notified_at = %s,
                            category = COALESCE(NULLIF(category, ''), %s)
                        WHERE source = %s AND external_id = %s
                        """,
                        (
                            project.title,
                            body_text,
                            project.url,
                            project.budget_text,
                            ai_verdict,
                            ai_score,
                            lead_tags,
                            is_visible,
                            notified_at,
                            category,
                            project.source,
                            str(project.project_id),
                        ),
                    )
                conn.commit()
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
