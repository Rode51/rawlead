"""Neon Postgres: дубль лидов (опционально, если задан DATABASE_URL)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import psycopg

from config import Config
from listing import ListingProject

if TYPE_CHECKING:
    from ai_analyze import AiAnalysis

logger = logging.getLogger(__name__)


def _short_pg_err(exc: BaseException, *, max_len: int = 200) -> str:
    s = f"{type(exc).__name__}: {exc}".replace("\n", " ").strip()
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


class NeonLeadStorage:
    """Запись лидов в Postgres; ошибки не пробрасываются наружу."""

    def __init__(self, database_url: str) -> None:
        self._url = database_url.strip()

    @property
    def enabled(self) -> bool:
        return bool(self._url)

    def record_new_lead(self, project: ListingProject, errors: list[str]) -> None:
        """После успешного SQLite try_record_new — INSERT ON CONFLICT DO NOTHING."""
        if not self.enabled:
            return
        try:
            with psycopg.connect(self._url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO leads (source, external_id, title, url, budget_text)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (source, external_id) DO NOTHING
                        """,
                        (
                            project.source,
                            str(project.project_id),
                            project.title,
                            project.url,
                            project.budget_text,
                        ),
                    )
                conn.commit()
        except Exception as exc:
            msg = f"pg:record:{project.source}:id={project.project_id}:{_short_pg_err(exc)}"
            logger.warning("%s", msg)
            errors.append(msg)

    def update_on_notify(
        self,
        project: ListingProject,
        *,
        analysis: AiAnalysis | None,
        errors: list[str],
    ) -> None:
        """После отправки в TG — вердикт ИИ и время уведомления."""
        if not self.enabled:
            return
        ai_verdict = analysis.verdict if analysis is not None else None
        notified_at = datetime.now(timezone.utc)
        try:
            with psycopg.connect(self._url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE leads
                        SET title = %s,
                            url = %s,
                            budget_text = %s,
                            ai_verdict = %s,
                            notified_at = %s
                        WHERE source = %s AND external_id = %s
                        """,
                        (
                            project.title,
                            project.url,
                            project.budget_text,
                            ai_verdict,
                            notified_at,
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
