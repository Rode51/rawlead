"""Общий путь: новый лид → SQLite → фильтр → [ИИ] → Telegram (биржи и TG-чаты)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ai_analyze import (
    AiAnalysis,
    AiLiteAnalysis,
    analyze_lite,
    analyze_premium,
    analyze_project,
)
from budget import meets_min_budget
from config import Config
from filters import ListingWordFilter
from fl_parser import fetch_project_description
from listing import SOURCE_FL, ListingProject
from lead_category import category_for_listing
from listing_dedup import listing_content_hash
from pg_storage import NeonLeadRow, NeonLeadStorage
from public_feed import is_public_feed_source
from storage import ProjectStorage
from radar_cycle_log import (
    SourceCycleStats,
    log_pipeline_line,
    note_dup_fast_skip,
    note_neon_dup_skip,
    note_neon_insert,
    note_neon_replay,
    note_neon_sqlite_resync,
    note_site_rollup_after_lite,
)
from telegram_notify import TelegramNotifyError, send_project_notification_from_config

_TELEGRAM_BOT_IN_PATH = re.compile(r"(/bot)[^/\s]+(/)")

__all__ = [
    "short_err",
    "ingest_with_l1",
    "process_new_listing",
    "process_new_listing_from_tg",
    "ListingNotifyPlan",
    "drain_l1_backlog",
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


def _should_notify_bot_lite(
    cfg: Config,
    lite: AiLiteAnalysis | None,
    *,
    ai_unavailable: bool,
) -> bool:
    """SITE L1: бот только при «Брать»; при сбое L1 — только по opt-in флагу."""
    if not cfg.ai_active:
        return True
    if ai_unavailable or lite is None:
        return cfg.site_notify_on_ai_unavailable
    if lite.is_skip_verdict() and not cfg.ai_notify_skip:
        return False
    return lite.is_take_verdict()


def _should_notify_bot_legacy(
    cfg: Config,
    analysis: AiAnalysis | None,
    *,
    ai_unavailable: bool,
) -> bool:
    """LEGACY: один полный разбор; «Пропустить»/«Мимо» не шлём (кроме AI_NOTIFY_SKIP)."""
    if not cfg.ai_active:
        return True
    if ai_unavailable or analysis is None:
        return False
    if not (analysis.reply_draft or "").strip():
        return False
    if analysis.is_skip_verdict() and not cfg.ai_notify_skip:
        return False
    return True


@dataclass(frozen=True)
class ListingNotifyPlan:
    """Готово к уведомлению (фильтр и L1 пройдены; L2 — в send)."""

    project: ListingProject
    lite_analysis: AiLiteAnalysis | None
    analysis: AiAnalysis | None
    ai_unavailable: bool
    task_fallback_text: str
    tg_acc_label: str = ""


def _neon_needs_l1_replay(
    pg: NeonLeadStorage,
    *,
    content_hash: str,
    project: ListingProject,
    errors: list[str],
) -> bool:
    state = pg.fetch_lead_lite_state(
        content_hash=content_hash,
        source=project.source,
        external_id=str(project.project_id),
        errors=errors,
    )
    if state is None:
        return False
    return not state.has_l1


def _neon_resync_tag(project: ListingProject, tag: str) -> str:
    return f"{project.source}:id={project.project_id} {tag}"


def _rollup_after_lite(
    cfg: Config,
    project: ListingProject,
    lite: AiLiteAnalysis | None,
    *,
    ingest_snippet: str,
) -> None:
    if cfg.radar_profile != "site":
        return
    category = category_for_listing(
        project.source,
        listing_category=project.listing_category,
        title=project.title,
        snippet=ingest_snippet,
    )
    note_site_rollup_after_lite(
        lite,
        category=category,
        source_public=is_public_feed_source(project.source),
    )


def _neon_dup_skip_return(
    project: ListingProject,
    *,
    inserted: bool,
    errors: list[str],
    stats: SourceCycleStats | None,
    reason: str = "neon_dup_skip",
) -> tuple[bool, None]:
    errors.append(f"{project.source}:id={project.project_id} skip:{reason}")
    note_neon_dup_skip()
    if stats is not None:
        stats.note_skip(f"skip:{reason}")
    return inserted, None


def _neon_dup_fast_skip_return(
    project: ListingProject,
    *,
    inserted: bool,
    errors: list[str],
    stats: SourceCycleStats | None,
) -> tuple[bool, None]:
    errors.append(f"{project.source}:id={project.project_id} skip:dup_fast_skip")
    note_dup_fast_skip()
    if stats is not None:
        stats.note_skip("skip:dup_fast_skip")
    return inserted, None


def _insert_neon_after_gates(
    project: ListingProject,
    pg: NeonLeadStorage,
    *,
    fingerprint: str,
    ingest_body: str,
    inserted: bool,
    exchange_neon: bool,
    errors: list[str],
    stats: SourceCycleStats | None,
) -> tuple[bool, bool, bool, bool]:
    """INSERT Neon после filter/budget. Четвёртый флаг — dup_abort (вернуть dup skip)."""
    neon_replay = False
    neon_sqlite_resync = False
    ext_id = str(project.project_id)

    def _mark_sqlite_resync() -> None:
        nonlocal neon_sqlite_resync
        note_neon_sqlite_resync()
        neon_sqlite_resync = True
        errors.append(_neon_resync_tag(project, "neon_resync_insert"))

    in_neon = pg.lead_exists(project.source, ext_id, errors)
    if in_neon:
        if _neon_needs_l1_replay(
            pg, content_hash=fingerprint, project=project, errors=errors
        ):
            neon_replay = True
            note_neon_replay()
        return True, neon_replay, neon_sqlite_resync, False

    neon_inserted = pg.record_new_lead(
        project,
        errors,
        content_hash=fingerprint,
        body=ingest_body,
    )
    if neon_inserted:
        note_neon_insert()
        if not inserted:
            _mark_sqlite_resync()
        return True, neon_replay, neon_sqlite_resync, False

    if not pg.lead_exists(project.source, ext_id, errors):
        if exchange_neon:
            neon_inserted = pg.record_new_lead(
                project,
                errors,
                content_hash="",
                body=ingest_body,
            )
            if neon_inserted:
                note_neon_insert()
                if not inserted:
                    _mark_sqlite_resync()
                return True, neon_replay, neon_sqlite_resync, False
            if _neon_needs_l1_replay(
                pg,
                content_hash=fingerprint,
                project=project,
                errors=errors,
            ):
                neon_replay = True
                note_neon_replay()
                errors.append(
                    _neon_resync_tag(project, "neon_resync_skip:hash_dup_needs_l1")
                )
                return False, neon_replay, neon_sqlite_resync, False
            errors.append(
                _neon_resync_tag(project, "neon_resync_skip:insert_failed")
            )
        elif _neon_needs_l1_replay(
            pg, content_hash=fingerprint, project=project, errors=errors
        ):
            neon_replay = True
            note_neon_replay()
        else:
            return False, False, False, True
    elif _neon_needs_l1_replay(
        pg, content_hash=fingerprint, project=project, errors=errors
    ):
        neon_replay = True
        note_neon_replay()
    elif exchange_neon:
        errors.append(_neon_resync_tag(project, "neon_resync_skip:hash_race"))
    else:
        return False, False, False, True

    return (
        pg.lead_exists(project.source, ext_id, errors),
        neon_replay,
        neon_sqlite_resync,
        False,
    )


def _run_l1_inline_site(
    project: ListingProject,
    cfg: Config,
    pg: NeonLeadStorage,
    *,
    ingest_snippet: str,
    errors: list[str],
    stats: SourceCycleStats | None,
) -> None:
    """Fallback L1 без pool (тесты / одиночный вызов)."""
    from l1_pool import L1Pool

    with L1Pool(cfg, pg, errors=errors, stats=stats) as pool:
        pool.submit(project, ingest_snippet=ingest_snippet)


def ingest_with_l1(
    project: ListingProject,
    storage: ProjectStorage,
    word_filter: ListingWordFilter,
    cfg: Config,
    *,
    errors: list[str],
    pg: NeonLeadStorage | None = None,
    stats: SourceCycleStats | None = None,
    l1_pool=None,
) -> tuple[bool, ListingNotifyPlan | None]:
    """Hot path O34: dedup → filter → budget → Neon → L1 (pool)."""
    return plan_new_listing(
        project,
        storage,
        word_filter,
        cfg,
        errors=errors,
        pg=pg,
        stats=stats,
        l1_pool=l1_pool,
    )


def plan_new_listing(
    project: ListingProject,
    storage: ProjectStorage,
    word_filter: ListingWordFilter,
    cfg: Config,
    *,
    errors: list[str],
    pg: NeonLeadStorage | None = None,
    stats: SourceCycleStats | None = None,
    l1_pool=None,
) -> tuple[bool, ListingNotifyPlan | None]:
    """Возвращает (was_new, plan). plan — только если нужно слать уведомление."""
    try:
        inserted = storage.try_record_new(project.source, project.project_id)
    except Exception as exc:
        errors.append(
            f"{project.source}:id={project.project_id} db:{short_err(exc)}"
        )
        return False, None

    fingerprint = listing_content_hash(
        project.title, project.listing_snippet or project.title
    )
    ingest_body = (project.listing_snippet or project.title or "").strip()
    neon_wide = cfg.neon_ingest_wide and pg is not None
    exchange_neon = neon_wide and is_public_feed_source(project.source)
    neon_replay = False
    neon_sqlite_resync = False
    ext_id = str(project.project_id)

    in_neon = False
    if neon_wide and pg is not None:
        if (
            not inserted
            and exchange_neon
            and storage.is_neon_dup_fast_path(
                project.source, project.project_id, fingerprint
            )
        ):
            return _neon_dup_fast_skip_return(
                project, inserted=inserted, errors=errors, stats=stats
            )

        in_neon = pg.lead_exists(project.source, ext_id, errors)
        if in_neon and _neon_needs_l1_replay(
            pg, content_hash=fingerprint, project=project, errors=errors
        ):
            storage.clear_neon_dup_synced(project.source, project.project_id)
            neon_replay = True
        elif in_neon and not inserted:
            if exchange_neon:
                prev_hash = storage.get_neon_synced_hash(
                    project.source, project.project_id
                )
                if prev_hash and prev_hash != fingerprint:
                    storage.clear_neon_dup_synced(project.source, project.project_id)
                    neon_replay = True
                else:
                    storage.mark_neon_dup_synced(
                        project.source, project.project_id, fingerprint
                    )
                    errors.append(
                        _neon_resync_tag(project, "neon_resync_skip:sqlite_dup_neon_ok")
                    )
                    return _neon_dup_skip_return(
                        project, inserted=inserted, errors=errors, stats=stats
                    )
            else:
                return _neon_dup_skip_return(
                    project, inserted=inserted, errors=errors, stats=stats
                )
        elif not in_neon and not inserted and not exchange_neon:
            return False, None
        elif not in_neon and not inserted and exchange_neon:
            errors.append(_neon_resync_tag(project, "neon_resync_check"))
    elif not inserted:
        return False, None

    if not word_filter.accepts_listing(project, wide=cfg.filter_wide):
        line = f"pipeline:skip filter {project.source}:id={ext_id}"
        errors.append(line)
        log_pipeline_line(cfg.radar_log_path, line)
        if stats is not None:
            stats.note_skip("skip:filter")
        return inserted or neon_replay or neon_sqlite_resync, None

    skip_content_dup = (
        exchange_neon
        and pg is not None
        and not pg.lead_exists(project.source, ext_id, errors)
    )
    if (
        fingerprint
        and not neon_replay
        and not neon_sqlite_resync
        and not skip_content_dup
        and not storage.try_record_content_fingerprint(
            fingerprint, source=project.source
        )
    ):
        errors.append(f"{project.source}:id={project.project_id} skip:dup_content")
        if stats is not None:
            stats.note_skip("skip:dup_content")
        return inserted or neon_replay or neon_sqlite_resync, None

    if cfg.ai_active and not meets_min_budget(project.budget_text, cfg.min_budget_rub):
        errors.append(f"{project.source}:id={project.project_id} skip:budget")
        if stats is not None:
            stats.note_skip("skip:budget")
        return inserted or neon_replay or neon_sqlite_resync, None

    if neon_wide and pg is not None and not in_neon:
        in_neon, neon_replay, neon_sqlite_resync, dup_abort = _insert_neon_after_gates(
            project,
            pg,
            fingerprint=fingerprint,
            ingest_body=ingest_body,
            inserted=inserted,
            exchange_neon=exchange_neon,
            errors=errors,
            stats=stats,
        )
        if dup_abort:
            return _neon_dup_skip_return(
                project, inserted=inserted, errors=errors, stats=stats
            )
    elif pg is not None and not neon_wide:
        if not pg.record_new_lead(
            project,
            errors,
            content_hash=fingerprint,
            body=ingest_body,
        ):
            if _neon_needs_l1_replay(
                pg, content_hash=fingerprint, project=project, errors=errors
            ):
                neon_replay = True
                note_neon_replay()
            else:
                return _neon_dup_skip_return(
                    project, inserted=inserted, errors=errors, stats=stats
                )
        else:
            note_neon_insert()
            in_neon = True

    was_new = inserted or neon_replay or neon_sqlite_resync
    ingest_snippet = ingest_body

    if (
        cfg.radar_profile == "site"
        and is_public_feed_source(project.source)
        and cfg.ai_active
        and cfg.ai_uses_l1_l2
        and pg is not None
        and (in_neon or neon_replay)
    ):
        if l1_pool is not None:
            l1_pool.submit(project, ingest_snippet=ingest_snippet)
        else:
            _run_l1_inline_site(
                project,
                cfg,
                pg,
                ingest_snippet=ingest_snippet,
                errors=errors,
                stats=stats,
            )
        return was_new, None

    lite_analysis: AiLiteAnalysis | None = None
    full_analysis: AiAnalysis | None = None
    ai_unavailable = False
    task_fallback_text = ingest_snippet

    if cfg.ai_active:
        log_prefix = f"{project.source}:id={project.project_id} "

        if cfg.ai_uses_l1_l2:
            lite_analysis = analyze_lite(
                cfg,
                title=project.title,
                budget_text=project.budget_text,
                snippet=ingest_snippet,
                url=project.url,
                errors=errors,
                log_prefix=log_prefix,
            )
            if lite_analysis is None:
                if pg is not None:
                    pg.mark_l1_failed(project, errors, body_snippet=ingest_snippet)
                ai_unavailable = True
                reason = "skip:ai_unavailable"
                errors.append(f"{project.source}:id={project.project_id} {reason}")
                if stats is not None:
                    stats.note_skip(reason)
                return was_new, None
            if lite_analysis.is_skip_verdict():
                reason = f"skip:ai:{lite_analysis.verdict}"
                errors.append(f"{project.source}:id={project.project_id} {reason}")
                if stats is not None:
                    stats.note_skip(reason)
                if pg is not None:
                    pg.update_after_lite(
                        project,
                        lite=lite_analysis,
                        errors=errors,
                        body_snippet=ingest_snippet,
                    )
                    _rollup_after_lite(
                        cfg, project, lite_analysis, ingest_snippet=ingest_snippet
                    )
                return was_new, None

            if pg is not None:
                pg.update_after_lite(
                    project,
                    lite=lite_analysis,
                    errors=errors,
                    body_snippet=ingest_snippet,
                )
                _rollup_after_lite(
                    cfg, project, lite_analysis, ingest_snippet=ingest_snippet
                )

            if not _should_notify_bot_lite(
                cfg, lite_analysis, ai_unavailable=ai_unavailable
            ):
                reason = f"skip:ai:{lite_analysis.verdict}"
                errors.append(f"{project.source}:id={project.project_id} {reason}")
                if stats is not None:
                    stats.note_skip(reason)
                return was_new, None
        else:
            description = _resolve_description(project, cfg, errors)
            task_fallback_text = description or task_fallback_text
            full_analysis = analyze_project(
                cfg,
                title=project.title,
                budget_text=project.budget_text,
                description=description,
                url=project.url,
                errors=errors,
                log_prefix=log_prefix,
                model=cfg.ai_model,
            )
            if full_analysis is None:
                ai_unavailable = True
            elif full_analysis.is_skip_verdict():
                reason = f"skip:ai:{full_analysis.verdict}"
                errors.append(f"{project.source}:id={project.project_id} {reason}")
                if stats is not None:
                    stats.note_skip(reason)
                return was_new, None

            if not _should_notify_bot_legacy(
                cfg, full_analysis, ai_unavailable=ai_unavailable
            ):
                if ai_unavailable or full_analysis is None:
                    reason = "skip:ai_unavailable_no_draft"
                elif not (full_analysis.reply_draft or "").strip():
                    reason = "skip:ai:no_reply_draft"
                else:
                    reason = f"skip:ai:{full_analysis.verdict}"
                errors.append(f"{project.source}:id={project.project_id} {reason}")
                if stats is not None:
                    stats.note_skip(reason)
                return was_new, None

    if cfg.radar_profile == "site" and is_public_feed_source(project.source):
        return was_new, None

    return was_new, ListingNotifyPlan(
        project=project,
        lite_analysis=lite_analysis,
        analysis=full_analysis,
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
    if cfg.radar_profile == "site" and is_public_feed_source(project.source):
        errors.append(
            f"{project.source}:id={project.project_id} skip:site_exchange_no_owner_bot"
        )
        return False
    if cfg.radar_profile == "site" and not cfg.site_notify_owner:
        errors.append(f"{project.source}:id={project.project_id} skip:site_owner_notify_off")
        return False

    premium = plan.analysis
    task_text = plan.task_fallback_text

    if cfg.radar_profile == "legacy":
        # Legacy @FLPARSINGBOT: never send a card without reply_draft.
        if plan.ai_unavailable or premium is None:
            errors.append(
                f"{project.source}:id={project.project_id} "
                "skip:ai_unavailable_no_draft"
            )
            return False
        if not (premium.reply_draft or "").strip():
            verdict = (premium.verdict or "").strip() or "—"
            errors.append(
                f"{project.source}:id={project.project_id} "
                f"skip:ai:no_reply_draft verdict={verdict}"
            )
            return False

    if cfg.ai_active and premium is None and cfg.ai_uses_l1_l2:
        log_prefix = f"{project.source}:id={project.project_id} "
        if plan.lite_analysis is not None and plan.lite_analysis.is_take_verdict():
            description = _resolve_description(project, cfg, errors)
            task_text = description or task_text
            premium = analyze_premium(
                cfg,
                title=project.title,
                budget_text=project.budget_text,
                description=description,
                url=project.url,
                lite=plan.lite_analysis,
                errors=errors,
                log_prefix=log_prefix,
            )
        elif plan.lite_analysis is None:
            description = _resolve_description(project, cfg, errors)
            task_text = description or task_text
            premium = analyze_premium(
                cfg,
                title=project.title,
                budget_text=project.budget_text,
                description=description,
                url=project.url,
                lite=None,
                errors=errors,
                log_prefix=log_prefix,
            )

    try:
        send_project_notification_from_config(
            project,
            cfg,
            analysis=premium,
            ai_unavailable=plan.ai_unavailable and premium is None,
            task_fallback_text=task_text,
            tg_acc_label=plan.tg_acc_label,
        )
        if pg is not None:
            if premium is not None:
                pg.update_after_premium(project, premium=premium, errors=errors)
            pg.mark_notified(project, errors=errors)
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
    l1_pool=None,
) -> tuple[bool, bool]:
    """Возвращает (was_new, notified). Дубликат в SQLite → (False, False)."""
    was_new, plan = ingest_with_l1(
        project,
        storage,
        word_filter,
        cfg,
        errors=errors,
        pg=pg,
        stats=stats,
        l1_pool=l1_pool,
    )
    if plan is None:
        return was_new, False
    return was_new, send_listing_notification(plan, cfg, errors=errors, pg=pg)


def _listing_from_neon_row(row: NeonLeadRow) -> ListingProject:
    pid = int(row.external_id) if str(row.external_id).isdigit() else hash(row.external_id) % (2**31)
    return ListingProject(
        project_id=pid,
        title=row.title,
        budget_text=row.budget_text,
        url=row.url,
        published_at="",
        listing_snippet=(row.body or row.title or "").strip(),
        source=row.source,
        listing_category=row.category or "",
    )


def drain_l1_backlog(
    cfg: Config,
    pg: NeonLeadStorage,
    word_filter: ListingWordFilter,
    *,
    errors: list[str],
    limit: int = 40,
) -> int:
    """Конвейер: L1 для строк Neon без ai_verdict (свежие id первыми)."""
    if not cfg.ai_active or not pg.enabled:
        return 0
    rows = pg.fetch_leads_missing_l1(limit=limit, order_desc=True, errors=errors)
    if not rows:
        return 0
    from ai_analyze import analyze_lite
    from lead_category import category_for_listing
    from match_push import lead_tags_from_lite, push_match_for_lead
    from pg_storage import _is_visible_lite
    from public_feed import is_public_feed_source

    done = 0
    for row in rows:
        project = _listing_from_neon_row(row)
        snippet = (project.listing_snippet or project.title or "").strip()
        if not word_filter.accepts_listing(project, wide=cfg.filter_wide):
            errors.append(f"{row.source}:id={row.external_id} skip:filter:backlog")
            continue
        log_prefix = f"{row.source}:id={row.external_id} conveyor:"
        lite = analyze_lite(
            cfg,
            title=project.title,
            budget_text=project.budget_text,
            snippet=snippet,
            url=project.url,
            errors=errors,
            log_prefix=log_prefix,
        )
        if lite is None:
            pg.mark_l1_failed(project, errors, body_snippet=snippet)
            errors.append(f"{row.source}:id={row.external_id} skip:l1_failed:backlog")
            continue
        pg.update_after_lite(
            project,
            lite=lite,
            errors=errors,
            body_snippet=snippet,
        )
        category = category_for_listing(
            project.source,
            listing_category=project.listing_category,
            title=project.title,
            snippet=snippet,
        )
        if (
            cfg.match_push_enabled
            and lite is not None
            and _is_visible_lite(lite, category)
            and is_public_feed_source(project.source)
        ):
            push_match_for_lead(
                cfg,
                row.lead_id,
                title=project.title,
                task_summary=lite.task_summary,
                lead_tags=lead_tags_from_lite(lite),
                errors=errors,
            )
        done += 1
    return done


def process_legacy_neon_listing(
    project: ListingProject,
    storage: ProjectStorage,
    word_filter: ListingWordFilter,
    cfg: Config,
    *,
    errors: list[str],
) -> tuple[bool, bool]:
    """
  Legacy consumer: Neon → FILTERS_LEGACY → ИИ → @FLPARSINGBOT.
  SQLite — дедуп «уже слал в бот»; Neon не пишем.
    """
    try:
        # Важно: legacy consumer читает лиды из Neon, которые уже мог видеть Site.
        # Дедуп Legacy должен означать «уже слали в legacy-бот», а не «уже видели на Site».
        sqlite_source = f"legacy:{project.source}"
        inserted = storage.try_record_new(sqlite_source, project.project_id)
    except Exception as exc:
        errors.append(
            f"{project.source}:id={project.project_id} db:{short_err(exc)}"
        )
        return False, False

    if not inserted:
        errors.append(
            f"{project.source}:id={project.project_id} skip:legacy_sqlite_dup"
        )
        return False, False

    if not word_filter.accepts_listing(project, wide=cfg.filter_wide):
        errors.append(f"{project.source}:id={project.project_id} skip:filter")
        return True, False

    full_analysis: AiAnalysis | None = None
    ai_unavailable = False
    task_fallback_text = (project.listing_snippet or project.title).strip()

    if cfg.ai_active:
        if not meets_min_budget(project.budget_text, cfg.min_budget_rub):
            errors.append(f"{project.source}:id={project.project_id} skip:budget")
            return True, False

        log_prefix = f"{project.source}:id={project.project_id} "
        description = _resolve_description(project, cfg, errors)
        task_fallback_text = description or task_fallback_text
        full_analysis = analyze_project(
            cfg,
            title=project.title,
            budget_text=project.budget_text,
            description=description,
            url=project.url,
            errors=errors,
            log_prefix=log_prefix,
            model=cfg.ai_model,
        )
        if full_analysis is None:
            ai_unavailable = True
            errors.append(
                f"{project.source}:id={project.project_id} "
                "skip:ai_unavailable_no_draft"
            )
            return True, False
        elif full_analysis.is_skip_verdict():
            errors.append(
                f"{project.source}:id={project.project_id} "
                f"skip:ai:{full_analysis.verdict}"
            )
            return True, False
        elif not (full_analysis.reply_draft or "").strip():
            errors.append(
                f"{project.source}:id={project.project_id} "
                f"skip:ai:no_reply_draft verdict={full_analysis.verdict}"
            )
            return True, False

        if not _should_notify_bot_legacy(
            cfg, full_analysis, ai_unavailable=ai_unavailable
        ):
            reason = (
                "skip:ai_unavailable_no_draft"
                if ai_unavailable or full_analysis is None
                else (
                    f"skip:ai:no_reply_draft verdict={full_analysis.verdict}"
                    if not (full_analysis.reply_draft or "").strip()
                    else f"skip:ai:{full_analysis.verdict}"
                )
            )
            errors.append(f"{project.source}:id={project.project_id} {reason}")
            return True, False

    plan = ListingNotifyPlan(
        project=project,
        lite_analysis=None,
        analysis=full_analysis,
        ai_unavailable=ai_unavailable,
        task_fallback_text=task_fallback_text,
    )
    return True, send_listing_notification(plan, cfg, errors=errors, pg=None)


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

    from l1_pool import L1Pool

    if pg is not None:
        with L1Pool(cfg, pg, errors=errors, stats=stats) as pool:
            was_new, plan = ingest_with_l1(
                project,
                storage,
                word_filter,
                cfg,
                errors=errors,
                pg=pg,
                stats=stats,
                l1_pool=pool,
            )
    else:
        was_new, plan = ingest_with_l1(
            project,
            storage,
            word_filter,
            cfg,
            errors=errors,
            pg=pg,
            stats=stats,
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
            lite_analysis=plan.lite_analysis,
            analysis=plan.analysis,
            ai_unavailable=plan.ai_unavailable,
            task_fallback_text=plan.task_fallback_text,
            tg_acc_label=acc_label,
        )
    return was_new, send_listing_notification(plan, cfg, errors=errors, pg=pg)
