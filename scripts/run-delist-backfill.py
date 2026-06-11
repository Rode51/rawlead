#!/usr/bin/env python3
"""O180: drain delist backlog (loop batches until --limit or empty queue)."""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import apply_profile_argv, load_config, load_radar_env  # noqa: E402
from delist_checker import (  # noqa: E402
    delist_batch_limit,
    run_delist_batch,
    save_delist_run,
)
from pg_storage import NeonLeadStorage  # noqa: E402
from storage import ProjectStorage  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="O180 delist backlog backfill")
    parser.add_argument("--limit", type=int, default=300, help="max URLs to check")
    parser.add_argument("--profile", default="site", choices=("site", "legacy"))
    args = parser.parse_args()
    os.environ["RADAR_PROFILE"] = args.profile
    apply_profile_argv()
    load_radar_env()
    cfg = load_config()
    if cfg.radar_profile != "site":
        print("radar profile must be site", file=sys.stderr)
        return 2
    if not (cfg.database_url or "").strip():
        print("DATABASE_URL empty", file=sys.stderr)
        return 2

    pg = NeonLeadStorage(cfg.database_url)
    if not pg.enabled:
        print("Neon storage disabled", file=sys.stderr)
        return 2

    storage = ProjectStorage(cfg.sqlite_path)
    errors: list[str] = []
    remaining = max(1, int(args.limit))
    totals = {"checked": 0, "delisted": 0, "skipped": 0}

    while remaining > 0:
        batch = min(delist_batch_limit(), remaining)
        stats = run_delist_batch(cfg, pg, limit=batch, errors=errors)
        for key in totals:
            totals[key] += int(stats.get(key) or 0)
        remaining -= int(stats.get("checked") or 0)
        print(
            f"delist: checked={stats['checked']} delisted={stats['delisted']} "
            f"skipped={stats['skipped']}"
        )
        if stats["checked"] == 0:
            break
        time.sleep(0.5)

    save_delist_run(storage, totals)
    print(
        f"delist: checked={totals['checked']} delisted={totals['delisted']} "
        f"skipped={totals['skipped']} total"
    )
    if errors:
        print(f"errors={len(errors)} (see logs)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
