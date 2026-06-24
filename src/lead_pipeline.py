"""Общий путь: новый лид → SQLite → фильтр → [ИИ] → Telegram (биржи и TG-чаты)."""

from __future__ import annotations

import os
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
from exchange_detail import fetch_project_detail, is_web_detail_source
from listing import SOURCE_FL, SOURCE_KWORK, SOURCE_YOUDO, ListingProject
from lead_category import category_for_listing
from listing_dedup import listing_content_hash
from pg_storage import NeonLeadRow, NeonLeadStorage
from public_feed import is_public_feed_source
from storage import ProjectStorage
from youdo_imap import _IMAP_MIN_DETAIL_LEN
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


def _youdo_detail_min_chars() -> int:
    return max(0, int(os.getenv("YOUDO_DETAIL_MIN_CHARS", "300")))


def _youdo_detail_fetch_enabled() -> bool:
    return os.getenv("YOUDO_DETAIL_FETCH", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _resolve_ingest_body(
    project: ListingProject,
    cfg: Config,
    errors: list[str],
) -> tuple[str, dict | None, bool | None]:
    """Полный текст ТЗ для ingest/L1/L2: detail page + O108 вложения.

    Третий элемент — detail fetch ok для YouDo (None если fetch не вызывался).
    """
    base = (project.listing_snippet or project.title or "").strip()
    html = ""
    ext_id = str(project.project_id)
    source = project.source
    detail_ok: bool | None = None

    if is_web_detail_source(source):
        if source == SOURCE_YOUDO:
            # Model B: email body in snippet is already detail — skip browser
            if len(base) >= _IMAP_MIN_DETAIL_LEN:
                return base, None, True
            if not _youdo_detail_fetch_enabled():
                return base, None, None
            # Check click-through cache first (§ YOUDO-DETAIL-BREAKTHROUGH)
            try:
                from exchange_browser_fetch import youdo_click_detail_enabled
                from youdo_parser import _click_detail_cache_get

                if youdo_click_detail_enabled():
                    cached = _click_detail_cache_get(ext_id)
                    if cached is not None:
                        cached_body, cached_ok = cached
                        if cached_ok and len(cached_body) > len(base):
                            return cached_body, None, True
            except Exception:
                pass
        text, html, ok = fetch_project_detail(
            source,
            project.url,
            cfg,
            fallback_snippet=base,
        )
        if source == SOURCE_YOUDO:
            detail_ok = ok
        if ok and text:
            base = text
        elif not ok:
            errors.append(f"{source}:id={ext_id} ai:detail:fallback")
    else:
        return base, None, None

    if source not in (SOURCE_FL, SOURCE_KWORK) or not html.strip():
        return base, None, detail_ok

    from tz_attachments import enrich_body_with_attachments, tz_attachments_enabled

    if not tz_attachments_enabled():
        return base, None, detail_ok

    result = enrich_body_with_attachments(
        project.source,
        html,
        base,
        cfg,
        page_url=project.url,
        errors=errors,
    )
    tz_dict = result.tz_attachment.to_dict() if result.tz_attachment else None
    if result.tz_attachment:
        st = result.tz_attachment.status
        errors.append(f"{project.source}:id={ext_id} tz_attachment:{st}")
    return result.body, tz_dict, detail_ok


def _resolve_description(
    project: ListingProject,
    cfg: Config,
    errors: list[str],
) -> str:
    if is_web_detail_source(project.source):
        body, _, _ = _resolve_ingest_body(project, cfg, errors)
        return body or (project.listing_snippet or project.title)
    return project.listing_snippet or project.title


def _youdo_detail_short_skips_l1(
    project: ListingProject,
    body: str,
    detail_ok: bool | None,
) -> bool:
    """YOUDO-SOURCE-GATE rev2: only detail_ok matters.

    detail_ok=True → pass (any length TZ is fine).
    detail_ok≠True → delist, reason=youdo_no_detail.
    """
    if project.source != SOURCE_YOUDO:
        return False
    return detail_ok is not True


def _apply_physical_pre_l1(
    project: ListingProject,
    *,
    ingest_body: str,
    cfg: Config,
    pg: NeonLeadStorage | None,
    errors: list[str],
    stats: SourceCycleStats | None,
    tz_attachment_meta: dict | None,
) -> bool:
    """O223: физуслуга без OpenRouter — Neon + rollup. True если обработано."""
    from vacancy_filter import physical_service_lite_analysis

    lite = physical_service_lite_analysis(title=project.title, body=ingest_body)
    if lite is None:
        return False
    reason = "skip:physical_service"
    errors.append(f"{project.source}:id={project.project_id} {reason}")
    if stats is not None:
        stats.note_skip(reason)
    if pg is not None:
        pg.update_after_lite(
            project,
            lite=lite,
            errors=errors,
            body_snippet=ingest_body,
            tz_attachment=tz_attachment_meta,
        )
        _rollup_after_lite(cfg, project, lite, ingest_snippet=ingest_body)
    return True


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
        # O252: same normalized text, new TG message.id — abort; never content_hash=""
        if fingerprint and pg.fetch_lead_lite_state(
            content_hash=fingerprint, errors=errors
        ) is not None:
            return False, False, False, True
        if exchange_neon:
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
    filter_ok = word_filter.accepts_listing(project, wide=cfg.filter_wide)

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

        if not inserted and not filter_ok:
            line = f"pipeline:skip filter {project.source}:id={ext_id}"
            errors.append(line)
            log_pipeline_line(cfg.radar_log_path, line)
            if stats is not None:
                stats.note_skip("skip:filter")
            return False, None

        in_neon = pg.lead_exists(project.source, ext_id, errors)
        if in_neon and _neon_needs_l1_replay(
            pg, content_hash=fingerprint, project=project, errors=errors
        ):
            storage.clear_neon_dup_synced(project.source, project.project_id)
            neon_replay = True
        elif in_neon and not inserted:
            if exchange_neon:
                lite_state = pg.fetch_lead_lite_state(
                    source=project.source,
                    external_id=ext_id,
                    errors=errors,
                )
                if lite_state is not None and lite_state.has_l1:
                    storage.mark_neon_dup_synced(
                        project.source, project.project_id, fingerprint
                    )
                    return _neon_dup_skip_return(
                        project, inserted=inserted, errors=errors, stats=stats
                    )
                prev_hash = storage.get_neon_synced_hash(
                    project.source, project.project_id
                )
                if prev_hash and prev_hash == fingerprint:
                    storage.mark_neon_dup_synced(
                        project.source, project.project_id, fingerprint
                    )
                    errors.append(
                        _neon_resync_tag(project, "neon_resync_skip:sqlite_dup_neon_ok")
                    )
                    return _neon_dup_skip_return(
                        project, inserted=inserted, errors=errors, stats=stats
                    )
                if prev_hash and prev_hash != fingerprint:
                    storage.clear_neon_dup_synced(project.source, project.project_id)
                neon_replay = True
            else:
                return _neon_dup_skip_return(
                    project, inserted=inserted, errors=errors, stats=stats
                )
        elif not in_neon and not inserted and not exchange_neon:
            return False, None
    elif not inserted:
        return False, None

    if not filter_ok:
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

    ingest_body, tz_attachment_meta, detail_ok = _resolve_ingest_body(project, cfg, errors)

    # Clear pending flag on success (§ YOUDO-CLICK-RETRY)
    if project.source == SOURCE_YOUDO and detail_ok is True:
        try:
            storage.set_setting(f"youdo_detail_pending:{ext_id}", "0")
        except Exception:
            pass

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

    if pg is not None and (in_neon or neon_replay):
        if _apply_physical_pre_l1(
            project,
            ingest_body=ingest_snippet,
            cfg=cfg,
            pg=pg,
            errors=errors,
            stats=stats,
            tz_attachment_meta=tz_attachment_meta,
        ):
            return was_new, None

        if _youdo_detail_short_skips_l1(project, ingest_snippet, detail_ok):
            line = f"pipeline:skip youdo:id={ext_id} no_detail"
            errors.append(line)
            log_pipeline_line(cfg.radar_log_path, line)
            if stats is not None:
                stats.note_skip("skip:youdo_no_detail")
            # Mark pending for click-through retry (§ YOUDO-CLICK-RETRY)
            try:
                storage.set_setting(f"youdo_detail_pending:{ext_id}", "1")
            except Exception:
                pass
            if pg is not None:
                lead_id = pg.fetch_lead_id(project.source, ext_id, errors)
                if lead_id is not None:
                    pg.delist_lead(
                        lead_id,
                        reason="youdo_no_detail",
                        errors=errors,
                    )
            return was_new, None

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
                        tz_attachment=tz_attachment_meta,
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
                    tz_attachment=tz_attachment_meta,
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


def _youdo_stuck_l1_since() -> str:
    return os.getenv("YOUDO_STUCK_L1_SINCE", "2026-06-15").strip() or "2026-06-15"


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
    lim = max(1, int(limit))
    youdo_budget = min(20, lim)
    youdo_rows = pg.fetch_youdo_invisible_missing_l1(
        since=_youdo_stuck_l1_since(),
        limit=youdo_budget,
        errors=errors,
    )
    seen_ids = {row.lead_id for row in youdo_rows}
    rest_limit = max(0, lim - len(youdo_rows))
    rest_rows = (
        pg.fetch_leads_missing_l1(limit=rest_limit or lim, order_desc=True, errors=errors)
        if rest_limit > 0
        else []
    )
    rows = youdo_rows + [r for r in rest_rows if r.lead_id not in seen_ids][:lim]
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
        if (
            row.source == SOURCE_YOUDO
            and _youdo_detail_min_chars() > 0
            and len(snippet) < _youdo_detail_min_chars()
        ):
            errors.append(
                f"youdo:id={row.external_id} pipeline:skip detail:short:backlog"
            )
            continue
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


def _tools_lite_for_row(row: NeonLeadRow) -> tuple[ListingProject, AiLiteAnalysis]:
    project = _listing_from_neon_row(row)
    snippet = (project.listing_snippet or project.title or "").strip()
    lite = AiLiteAnalysis(
        feed_visible=True,
        task_summary=snippet[:400],
        lead_tags=(),
        ai_reasons=(),
    )
    return project, lite


def replay_tools_for_rows(
    cfg: Config,
    pg: NeonLeadStorage,
    rows: list[NeonLeadRow],
    *,
    errors: list[str],
) -> int:
    """O98: L2 tools-only + persist для выбранных Neon rows."""
    if not cfg.ai_active or not pg.enabled or not rows:
        return 0
    from ai_analyze import analyze_lead_tools

    done = 0
    for row in rows:
        project, lite = _tools_lite_for_row(row)
        snippet = (project.listing_snippet or project.title or "").strip()
        log_prefix = f"{row.source}:id={row.external_id} tools:"
        tools = analyze_lead_tools(
            cfg,
            title=project.title,
            budget_text=project.budget_text,
            description=snippet,
            lite=lite,
            errors=errors,
            log_prefix=log_prefix,
        )
        if not tools:
            errors.append(f"{row.source}:id={row.external_id} skip:tools_failed")
            continue
        if pg.update_tools_required(
            project.source,
            str(project.project_id),
            list(tools),
            errors=errors,
        ):
            done += 1
            errors.append(
                f"{row.source}:id={row.external_id} tools:ok n={len(tools)}"
            )
    return done


def drain_tools_backlog(
    cfg: Config,
    pg: NeonLeadStorage,
    *,
    errors: list[str],
    limit: int = 8,
) -> int:
    """Site: L2 tools-only для visible leads без tools_required."""
    if not cfg.ai_active or not pg.enabled:
        return 0
    if cfg.radar_profile != "site":
        return 0
    rows = pg.fetch_leads_missing_tools(limit=limit, errors=errors)
    if not rows:
        return 0
    return replay_tools_for_rows(cfg, pg, rows, errors=errors)


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
        neon_body = (project.listing_snippet or "").strip()
        if is_web_detail_source(project.source) and len(neon_body) < 300:
            body, _, _ = _resolve_ingest_body(project, cfg, errors)
            description = body or neon_body or project.title
        else:
            description = neon_body or project.title
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
    """TG: ingest → L1 → карточка владельцу только при gate feed_visible+public_feed.

    Raw Telethon forward убран (O163-DoD2).
    Gate (O163-DoD1): слать только если лид прошёл бы в /lenta/:
        _is_visible_lite(lite) AND is_public_feed_source(source).
    Пока TG ∉ PUBLIC_FEED_SOURCES — никакого уведомления владельцу.
    """
    from pg_storage import _is_visible_lite
    from tg_spam_filter import is_tg_spam

    from l1_pool import L1Pool

    # Pre-L1: отсечь promo-бот рекламу, CV «ищу проект», партнёрки
    snippet = (project.listing_snippet or project.title or "").strip()
    if is_tg_spam(project.title, snippet):
        errors.append(
            f"{project.source}:id={project.project_id} skip:tg_spam"
        )
        return False, False

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

    # Gate: owner notify только если лид попал бы в ленту
    lite = plan.lite_analysis
    if not (_is_visible_lite(lite) and is_public_feed_source(plan.project.source)):
        errors.append(
            f"{plan.project.source}:id={plan.project.project_id} "
            "skip:tg_gate_not_public_feed"
        )
        return was_new, False

    # Форматированная карточка (без raw Telethon forward)
    from tg_forward import format_tg_acc_label

    acc_label = format_tg_acc_label(account, chat_title) if account else ""
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
