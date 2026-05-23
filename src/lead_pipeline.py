"""Общий путь: новый лид → SQLite → фильтр → [ИИ] → Telegram (биржи и TG-чаты)."""

from __future__ import annotations

import re

from ai_analyze import AiAnalysis, analyze
from budget import meets_min_budget
from config import Config
from filters import ListingWordFilter
from fl_parser import fetch_project_description
from listing import SOURCE_FL, ListingProject
from pg_storage import NeonLeadStorage
from storage import ProjectStorage
from telegram_notify import TelegramNotifyError, send_project_notification_from_config

_TELEGRAM_BOT_IN_PATH = re.compile(r"(/bot)[^/\s]+(/)")

__all__ = ["short_err", "process_new_listing"]


def short_err(exc: BaseException, *, max_len: int = 240) -> str:
    s = _TELEGRAM_BOT_IN_PATH.sub(
        r"\1***MASKED***\2",
        f"{type(exc).__name__}: {exc}".replace("\n", " ").strip(),
    )
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


def _resolve_description(
    project: ListingProject,
    cfg: Config,
    errors: list[str],
) -> str:
    if project.source == SOURCE_FL:
        desc, ok = fetch_project_description(
            project.url,
            cfg,
            fallback_snippet=project.listing_snippet,
        )
        if not ok:
            errors.append(
                f"{project.source}:id={project.project_id} ai:detail:fallback"
            )
        return desc
    return project.listing_snippet or project.title


def _should_notify_after_ai(cfg: Config, analysis: AiAnalysis | None) -> bool:
    if analysis is None:
        return True
    if analysis.is_skip_verdict() and not cfg.ai_notify_skip:
        return False
    return True


def process_new_listing(
    project: ListingProject,
    storage: ProjectStorage,
    word_filter: ListingWordFilter,
    cfg: Config,
    *,
    errors: list[str],
    pg: NeonLeadStorage | None = None,
) -> tuple[bool, bool]:
    """Возвращает (was_new, notified). Дубликат в SQLite → (False, False)."""
    try:
        inserted = storage.try_record_new(project.source, project.project_id)
    except Exception as exc:
        errors.append(
            f"{project.source}:id={project.project_id} db:{short_err(exc)}"
        )
        return False, False

    if not inserted:
        return False, False

    if pg is not None:
        pg.record_new_lead(project, errors)

    if not word_filter.accepts_listing(project, wide=cfg.filter_wide):
        errors.append(f"{project.source}:id={project.project_id} skip:filter")
        return True, False

    analysis = None
    ai_unavailable = False
    task_fallback_text = (project.listing_snippet or project.title).strip()

    if cfg.ai_active:
        if not meets_min_budget(project.budget_text, cfg.min_budget_rub):
            errors.append(f"{project.source}:id={project.project_id} skip:budget")
            return True, False

        description = _resolve_description(project, cfg, errors)
        task_fallback_text = description or task_fallback_text
        log_prefix = f"{project.source}:id={project.project_id} "
        analysis = analyze(
            cfg,
            title=project.title,
            budget_text=project.budget_text,
            description=description,
            url=project.url,
            errors=errors,
            log_prefix=log_prefix,
        )
        if analysis is None:
            ai_unavailable = True
        elif not _should_notify_after_ai(cfg, analysis):
            errors.append(
                f"{project.source}:id={project.project_id} skip:ai:{analysis.verdict}"
            )
            return True, False

    try:
        send_project_notification_from_config(
            project,
            cfg,
            analysis=analysis,
            ai_unavailable=ai_unavailable,
            task_fallback_text=task_fallback_text,
        )
        if pg is not None:
            pg.update_on_notify(project, analysis=analysis, errors=errors)
        return True, True
    except TelegramNotifyError as exc:
        errors.append(
            f"{project.source}:id={project.project_id} tg:{short_err(exc)}"
        )
    except Exception as exc:
        errors.append(
            f"{project.source}:id={project.project_id} tg:{short_err(exc)}"
        )
    return True, False
