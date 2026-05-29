"""Параллельный L1 для hot path Site (O34): Neon → analyze_lite → visible → push."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, Future

from ai_analyze import analyze_lite
from config import Config
from lead_category import category_for_listing
from listing import ListingProject
from match_push import lead_tags_from_lite, push_match_for_lead
from pg_storage import NeonLeadStorage, _is_visible_lite
from public_feed import is_public_feed_source
from radar_cycle_log import log_pipeline_line, note_site_rollup_after_lite


class L1Pool:
    """Thread pool на один цикл main/tg; drain() в конце."""

    def __init__(
        self,
        cfg: Config,
        pg: NeonLeadStorage,
        *,
        errors: list[str],
        stats=None,
    ) -> None:
        self._cfg = cfg
        self._pg = pg
        self._errors = errors
        self._stats = stats
        self._max_workers = cfg.l1_max_workers
        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        self._futures: list[Future[None]] = []
        self._lock = threading.Lock()
        self._submit_count = 0

    def submit(self, project: ListingProject, *, ingest_snippet: str) -> None:
        with self._lock:
            self._submit_count += 1
            slot = ((self._submit_count - 1) % self._max_workers) + 1
        future = self._executor.submit(
            _l1_worker,
            self._cfg,
            self._pg,
            project,
            ingest_snippet,
            self._errors,
            self._lock,
            slot,
            self._max_workers,
            self._stats,
        )
        self._futures.append(future)

    def drain(self) -> int:
        from lead_pipeline import short_err

        done = 0
        for future in self._futures:
            try:
                future.result()
                done += 1
            except Exception as exc:
                msg = f"pipeline:L1 worker:{short_err(exc)}"
                with self._lock:
                    self._errors.append(msg)
                log_pipeline_line(self._cfg.radar_log_path, msg)
        self._futures.clear()
        self._executor.shutdown(wait=False)
        return done

    def __enter__(self) -> L1Pool:
        return self

    def __exit__(self, *args) -> None:
        self.drain()


def _l1_worker(
    cfg: Config,
    pg: NeonLeadStorage,
    project: ListingProject,
    ingest_snippet: str,
    errors: list[str],
    lock: threading.Lock,
    worker_slot: int,
    max_workers: int,
    stats,
) -> None:
    snippet = (ingest_snippet or project.listing_snippet or project.title or "").strip()
    log_prefix = f"{project.source}:id={project.project_id} pipeline:"
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
        line = (
            f"pipeline:L1 {project.source}:id={project.project_id} "
            f"visible=0 worker={worker_slot}/{max_workers} l1_failed"
        )
        with lock:
            errors.append(line)
        log_pipeline_line(cfg.radar_log_path, line)
        if stats is not None:
            stats.note_skip("skip:l1_failed")
        return

    pg.update_after_lite(
        project,
        lite=lite,
        errors=errors,
        body_snippet=snippet,
    )
    if cfg.radar_profile == "site":
        category = category_for_listing(
            project.source,
            listing_category=project.listing_category,
            title=project.title,
            snippet=snippet,
        )
        note_site_rollup_after_lite(
            lite,
            category=category,
            source_public=is_public_feed_source(project.source),
        )
        visible = _is_visible_lite(lite, category) and is_public_feed_source(
            project.source
        )
    else:
        visible = _is_visible_lite(lite, "")

    line = (
        f"pipeline:L1 {project.source}:id={project.project_id} "
        f"visible={1 if visible else 0} worker={worker_slot}/{max_workers}"
    )
    with lock:
        errors.append(line)
    log_pipeline_line(cfg.radar_log_path, line)

    if lite.is_skip_verdict():
        reason = f"skip:ai:{lite.verdict}"
        with lock:
            errors.append(f"{project.source}:id={project.project_id} {reason}")
        if stats is not None:
            stats.note_skip(reason)
        return

    if (
        cfg.match_push_enabled
        and visible
        and is_public_feed_source(project.source)
    ):
        lead_id = pg.fetch_lead_id(project.source, str(project.project_id), errors)
        if lead_id is not None:
            push_match_for_lead(
                cfg,
                lead_id,
                title=project.title,
                task_summary=lite.task_summary,
                lead_tags=lead_tags_from_lite(lite),
                errors=errors,
            )
