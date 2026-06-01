#!/usr/bin/env python3
"""Backfill tools_required via L2 tools-only (Sonnet/premium)."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import apply_profile_argv, load_config, load_radar_env  # noqa: E402
from lead_pipeline import drain_tools_backlog  # noqa: E402
from pg_storage import NeonLeadStorage  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill leads.tools_required")
    parser.add_argument("--profile", default="site", choices=("site", "legacy"))
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--sleep", type=float, default=1.5)
    args = parser.parse_args()

    apply_profile_argv()
    load_radar_env()
    cfg = load_config()
    if not cfg.database_url.strip():
        print("DATABASE_URL empty")
        return 1

    pg = NeonLeadStorage(cfg.database_url)
    errors: list[str] = []
    total = 0
    remaining = max(1, args.limit)
    while remaining > 0:
        batch = min(8, remaining)
        n = drain_tools_backlog(cfg, pg, errors=errors, limit=batch)
        total += n
        print(f"batch ok={n}")
        if n == 0:
            break
        remaining -= n
        if args.sleep > 0:
            time.sleep(args.sleep)

    print(f"done total={total} errors={len(errors)}")
    for e in errors[-10:]:
        print(" ", e)
    return 0 if total > 0 or not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
