"""Общий путь: новый лид → SQLite → фильтр → [ИИ] → Telegram (биржи и TG-чаты)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ai_analyze import AiAnalysis, analyze
from budget import meets_min_budget
from config import Config
from filters import ListingWordFilter
from fl_parser import fetch_project_description
from listing import SOURCE_FL, ListingProject
from listing_dedup import listing_content_hash
from pg_storage import NeonLeadStorage
from storage import ProjectStorage
from radar_cycle_log import SourceCycleStats
from telegram_notify import TelegramNotifyError, send_project_notification_from_config

_TELEGRAM_BOT_IN_PATH = re.compile(r"(/bot)[^/\s]+(/)")

__all__ = [
    "short_err",
    "process_new_listing",
    "process_new_listing_from_tg",
    "ListingNotifyPlan",
]


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


@dataclass(frozen=True)
class ListingNotifyPlan:
    """Готово к уведомлению (фильтр и ИИ пройдены)."""

    project: ListingProject
    analysis: AiAnalysis | None
    ai_unavailable: bool
    task_fallback_text: str
    tg_acc_label: str = ""


def plan_new_listing(
    project: ListingProject,
    storage: ProjectStorage,
    word_filter: ListingWordFilter,
    cfg: Config,
    *,
    errors: list[str],
    pg: NeonLeadStorage | None = None,
    stats: SourceCycleStats | None = None,
) -> tuple[bool, ListingNotifyPlan | None]:
    """Возвращает (was_new, plan). plan — только если нужно слать уведомление."""
    try:
        inserted = storage.try_record_new(project.source, project.project_id)
    except Exception as exc:
        errors.append(
            f"{project.source}:id={project.project_id} db:{short_err(exc)}"
        )
        return False, None

    if not inserted:
        return False, None

    if not word_filter.accepts_listing(project, wide=cfg.filter_wide):
        errors.append(f"{project.source}:id={project.project_id} skip:filter")
        if stats is not None:
            stats.note_skip("skip:filter")
        return True, None

    fingerprint = listing_content_hash(
        project.title, project.listing_snippet or project.title
    )
    if fingerprint and not storage.try_record_content_fingerprint(
        fingerprint, source=project.source
    ):
        errors.append(f"{project.source}:id={project.project_id} skip:dup_content")
        if stats is not None:
            stats.note_skip("skip:dup_content")
        return True, None

    if pg is not None:
        ingest_body = (project.listing_snippet or project.title or "").strip()
        if not pg.record_new_lead(
            project,
            errors,
            content_hash=fingerprint,
            body=ingest_body,
        ):
            errors.append(f"{project.source}:id={project.project_id} skip:dup_content")
            if stats is not None:
                stats.note_skip("skip:dup_content")
            return True, None

    analysis = None
    ai_unavailable = False
    task_fallback_text = (project.listing_snippet or project.title).strip()

    if cfg.ai_active:
        if not meets_min_budget(project.budget_text, cfg.min_budget_rub):
            errors.append(f"{project.source}:id={project.project_id} skip:budget")
            if stats is not None:
                stats.note_skip("skip:budget")
            return True, None

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
            reason = f"skip:ai:{analysis.verdict}"
            errors.append(f"{project.source}:id={project.project_id} {reason}")
            if stats is not None:
                stats.note_skip(reason)
            return True, None

    return True, ListingNotifyPlan(
        project=project,
        analysis=analysis,
        ai_unavailable=ai_unavailable,
        task_fallback_text=task_fallback_text,
    )


def send_listing_notification(
    plan: ListingNotifyPlan,
    cfg: Config,
    *,
    errors: list[str],
    pg: NeonLeadStorage | None = None,
) -> bool:
    project = plan.project
    try:
        send_project_notification_from_config(
            project,
            cfg,
            analysis=plan.analysis,
            ai_unavailable=plan.ai_unavailable,
            task_fallback_text=plan.task_fallback_text,
            tg_acc_label=plan.tg_acc_label,
        )
        if pg is not None:
            pg.update_on_notify(
                project,
                analysis=plan.analysis,
                errors=errors,
                body=plan.task_fallback_text.strip(),
            )
        return True
    except TelegramNotifyError as exc:
        errors.append(
            f"{project.source}:id={project.project_id} tg:{short_err(exc)}"
        )
    except Exception as exc:
        errors.append(
            f"{project.source}:id={project.project_id} tg:{short_err(exc)}"
        )
    return False


def process_new_listing(
    project: ListingProject,
    storage: ProjectStorage,
    word_filter: ListingWordFilter,
    cfg: Config,
    *,
    errors: list[str],
    pg: NeonLeadStorage | None = None,
    stats: SourceCycleStats | None = None,
) -> tuple[bool, bool]:
    """Возвращает (was_new, notified). Дубликат в SQLite → (False, False)."""
    was_new, plan = plan_new_listing(
        project, storage, word_filter, cfg, errors=errors, pg=pg, stats=stats
    )
    if plan is None:
        return was_new, False
    return was_new, send_listing_notification(plan, cfg, errors=errors, pg=pg)


async def process_new_listing_from_tg(
    message,
    client,
    project: ListingProject,
    storage: ProjectStorage,
    word_filter: ListingWordFilter,
    cfg: Config,
    *,
    errors: list[str],
    pg: NeonLeadStorage | None = None,
    stats: SourceCycleStats | None = None,
    account: str = "",
    chat_title: str = "",
) -> tuple[bool, bool]:
    """TG: acc→бот (Telethon), карточка ИИ; relay владельцу — sync или poll."""
    from tg_forward import format_tg_acc_label, forward_listing_to_owner

    was_new, plan = plan_new_listing(
        project, storage, word_filter, cfg, errors=errors, pg=pg, stats=stats
    )
    if plan is None:
        return was_new, False

    acc_label = format_tg_acc_label(account, chat_title) if account else ""
    forwarded_ok = await forward_listing_to_owner(
        client,
        message,
        cfg,
        errors=errors,
        account=account,
        chat_title=chat_title,
    )
    if not forwarded_ok:
        return was_new, False
    if acc_label:
        plan = ListingNotifyPlan(
            project=plan.project,
            analysis=plan.analysis,
            ai_unavailable=plan.ai_unavailable,
            task_fallback_text=plan.task_fallback_text,
            tg_acc_label=acc_label,
        )
    return was_new, send_listing_notification(plan, cfg, errors=errors, pg=pg)
