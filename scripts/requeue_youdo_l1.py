"""O262g: re-trigger L1 for YouDo leads stuck invisible after detail:short.

Dry-run (diag + count):
  .venv\\Scripts\\python.exe scripts\\requeue_youdo_l1.py --profile site --dry-run

Apply reset (ai_verdict/score → NULL):
  .venv\\Scripts\\python.exe scripts\\requeue_youdo_l1.py --profile site --apply

VPS:
  sudo -u rawlead env RADAR_PROFILE=site PYTHONPATH=/opt/rawlead/src \\
    /opt/rawlead/.venv/bin/python /opt/rawlead/scripts/requeue_youdo_l1.py --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import apply_profile_argv, load_config, load_radar_env  # noqa: E402
from pg_storage import pg_storage_from_config  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="O262g: requeue YouDo stuck L1")
    parser.add_argument("--profile", default="site", help="legacy|site")
    parser.add_argument("--dry-run", action="store_true", help="Diag only, no UPDATE")
    parser.add_argument("--apply", action="store_true", help="Reset ai_verdict/score")
    parser.add_argument(
        "--since",
        default="2026-06-15",
        help="created_at >= date (default 2026-06-15)",
    )
    parser.add_argument("--limit", type=int, default=500, help="Max rows to requeue")
    args = parser.parse_args()

    if args.apply and args.dry_run:
        print("Укажите только --dry-run или --apply", file=sys.stderr)
        return 2
    dry_run = not args.apply

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
    diag = pg.youdo_stuck_invisible_diag(since=args.since, errors=errors)
    missing_l1 = int(diag.get("missing_l1", 0) or 0)
    total = int(diag.get("total_invisible", 0) or 0)
    has_verdict = int(diag.get("has_verdict", 0) or 0)

    print(f"[requeue_youdo_l1] mode={'dry-run' if dry_run else 'apply'} since={args.since}")
    print(f"  invisible_total={total} missing_l1={missing_l1} has_verdict={has_verdict}")
    by_verdict = diag.get("by_verdict") or []
    if by_verdict:
        print("  by_verdict:")
        for verdict, count in by_verdict:
            print(f"    {verdict}: {count}")
    if has_verdict > 0:
        print(
            "  note: backlog skips rows with ai_verdict set "
            "(e.g. backlog_cleared → Пропущено); --apply resets them"
        )
    elif missing_l1 > 0:
        print(
            "  note: missing_l1>0 — drain_l1_backlog prioritizes youdo invisible "
            "(YOUDO_DETAIL_FETCH=0 for new ingest)"
        )

    stats = pg.requeue_youdo_stuck_l1(
        since=args.since,
        dry_run=dry_run,
        limit=args.limit,
        errors=errors,
    )
    print(f"  requeue_candidates={stats.get('candidates', 0)}")
    if not dry_run:
        print(f"  requeued={stats.get('requeued', 0)}")

    if errors:
        for e in errors:
            print(f"  error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
