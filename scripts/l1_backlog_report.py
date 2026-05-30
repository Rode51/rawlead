"""O64: отчёт по хвосту без L1 — breakdown source + age + sample ids."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import apply_profile_argv, load_config, load_radar_env
from pg_storage import pg_storage_from_config


def main() -> int:
    parser = argparse.ArgumentParser(description="L1 backlog report (O64)")
    parser.add_argument("--profile", default="site", help="legacy|site")
    parser.add_argument("--hours", type=int, default=48)
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    if args.profile:
        sys.argv = [sys.argv[0], "--profile", args.profile.strip()] + [
            a for a in sys.argv[1:] if a not in ("--profile", args.profile.strip())
        ]
    apply_profile_argv()
    load_radar_env()

    cfg = load_config()
    pg = pg_storage_from_config(cfg)
    if pg is None or not pg.enabled:
        print("DATABASE_URL не задан", file=sys.stderr)
        return 1

    errors: list[str] = []
    by_source = pg.count_l1_backlog_by_source(hours=args.hours, errors=errors)
    age = pg.l1_backlog_age_buckets(errors=errors)
    sample = pg.l1_backlog_sample_ids(limit=5, errors=errors)
    missing_recent = pg.count_leads_missing_l1_recent(hours=args.hours, errors=errors)
    missing_total = pg.count_leads_missing_l1(errors=errors)
    tail = max(0, (missing_total or 0) - (missing_recent or 0))

    report = {
        "hours": args.hours,
        "by_source_48h": by_source,
        "age_buckets": age,
        "sample_ids": sample,
        "hot_path": missing_recent,
        "tail": tail,
        "missing_total": missing_total,
    }

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        src_line = " ".join(f"{k}:{by_source.get(k, 0)}" for k in ("fl", "kwork", "tg"))
        age_line = " · ".join(f"{k}={age.get(k, 0)}" for k in ("0-24h", "1-2d", "2-7d", ">7d"))
        print(f"[l1_backlog_report] profile={args.profile} hours={args.hours}")
        print(f"  L1 {args.hours}h: {src_line}")
        print(f"  hot path: {missing_recent} · tail: {tail} · total: {missing_total}")
        print(f"  age: {age_line}")
        print(f"  sample: {sample}")

    if errors:
        for e in errors:
            print(f"  error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
