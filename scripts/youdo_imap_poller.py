#!/usr/bin/env python3
"""YouDo IMAP poller — model B: last N + PG dedup (§ YOUDO-IMAP-ONLY).

Usage:
    .venv/Scripts/python scripts/youdo_imap_poller.py [--once]

Env: YOUDO_IMAP_ENABLED=1, YOUDO_IMAP_FETCH_LAST=30, YOUDO_LISTING_FETCH=0
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

from config import load_config, load_radar_env  # noqa: E402
from listing import SOURCE_YOUDO, ListingProject  # noqa: E402
from storage import ProjectStorage  # noqa: E402
from youdo_imap import (
    poll_youdo_imap,
    youdo_imap_enabled,
    _imap_config,
    _IMAP_LISTING_SNIPPET_MAX,
)  # noqa: E402
from radar_cycle_log import log_pipeline_line  # noqa: E402


def _storage_for_cfg(cfg) -> ProjectStorage:
    return ProjectStorage(cfg.database_url)


def _ingest_imap_task(
    task: dict,
    cfg,
    storage: ProjectStorage,
    pg=None,
) -> bool:
    """Feed one IMAP-discovered task into the pipeline.

    Returns True if lead was recorded (new or existing).
    """
    from lead_pipeline import process_new_listing
    from filters import default_listing_filter

    ext_id = str(task["project_id"])
    url = task.get("url", f"https://youdo.com/t{ext_id}")
    subject = task.get("subject", "")
    body = task.get("body", "")
    detail_ok = task.get("detail_ok", False)

    project = ListingProject(
        project_id=int(ext_id),
        title=subject,
        budget_text="",
        url=url,
        published_at="",
        listing_snippet=(body[: _IMAP_LISTING_SNIPPET_MAX] if body else subject),
        source=SOURCE_YOUDO,
        listing_category="",
    )

    word_filter = default_listing_filter()

    # Cache email body as detail (bypasses browser fetch)
    if detail_ok and body:
        try:
            from youdo_parser import _click_detail_cache_put

            _click_detail_cache_put(ext_id, body, True)
        except Exception:
            pass

    try:
        was_new, _notified = process_new_listing(
            project,
            storage,
            word_filter,
            cfg,
            errors=[],
            pg=pg,
        )
        return was_new
    except Exception as exc:
        log_pipeline_line(
            cfg.radar_log_path,
            f"youdo:imap ingest_fail id={ext_id} err={exc}",
        )
        return False


def run_poll_once(cfg=None) -> int:
    """Single IMAP poll. Returns count of newly discovered tasks."""
    if not youdo_imap_enabled():
        return 0

    if cfg is None:
        load_radar_env()
        cfg = load_config()

    from pg_storage import pg_storage_from_config

    storage = _storage_for_cfg(cfg)
    pg = pg_storage_from_config(cfg)
    tasks = poll_youdo_imap(storage)

    # PG dedup: skip visible + invisible already L1'd; refresh only invisible w/o L1
    new_tasks = []
    skip_count = 0
    skip_l1_count = 0
    refresh_count = 0
    for task in tasks:
        ext_id = str(task["project_id"])
        if pg is not None:
            try:
                skip = pg.lead_imap_poll_skip(SOURCE_YOUDO, ext_id, [])
                if skip == "visible":
                    skip_count += 1
                    log_pipeline_line(
                        cfg.radar_log_path,
                        f"youdo:imap skip_exists={ext_id}",
                    )
                    continue
                if skip == "l1_done":
                    skip_l1_count += 1
                    log_pipeline_line(
                        cfg.radar_log_path,
                        f"youdo:imap skip_l1_done={ext_id}",
                    )
                    continue
                if pg.lead_exists(SOURCE_YOUDO, ext_id, []):
                    refresh_count += 1
                    storage.clear_neon_dup_synced(SOURCE_YOUDO, int(ext_id))
                    log_pipeline_line(
                        cfg.radar_log_path,
                        f"youdo:imap refresh_invisible={ext_id}",
                    )
            except Exception:
                pass
        new_tasks.append(task)

    new_count = 0
    for task in new_tasks:
        ok = _ingest_imap_task(task, cfg, storage, pg=pg)
        if ok:
            new_count += 1
            log_pipeline_line(
                cfg.radar_log_path,
                f"youdo:imap new_id={task['project_id']}",
            )

    if new_count > 0 or skip_count > 0 or skip_l1_count > 0 or refresh_count > 0:
        log_pipeline_line(
            cfg.radar_log_path,
            f"youdo:imap cycle discovered={len(tasks)} new={new_count} skip_exists={skip_count} skip_l1_done={skip_l1_count} refresh_invisible={refresh_count}",
        )

    return new_count


def run_poll_loop() -> None:
    """Continuous poll loop with configurable interval."""
    load_radar_env()
    cfg = load_config()
    poll_sec = _imap_config()["poll_sec"]

    log_pipeline_line(cfg.radar_log_path, f"youdo:imap loop_start poll_sec={poll_sec}")

    while True:
        try:
            run_poll_once(cfg)
        except Exception as exc:
            log_pipeline_line(cfg.radar_log_path, f"youdo:imap loop_error err={exc}")
        time.sleep(poll_sec)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="YouDo IMAP discovery poller")
    parser.add_argument("--once", action="store_true", help="Single poll, then exit")
    args = parser.parse_args()

    if args.once:
        n = run_poll_once()
        print(f"discovered={n}")
        return 0

    run_poll_loop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
