"""§ BACKLOG-CLEAR / BACKLOG-TAIL-CLEAR-O40: пометить хвост без L1 без OpenRouter.

Legacy (без --by-age):
  .venv\\Scripts\\python.exe scripts\\clear_l1_backlog.py --profile site --dry-run
  .venv\\Scripts\\python.exe scripts\\clear_l1_backlog.py --profile site --apply

Age-mode (O40):
  .venv\\Scripts\\python.exe scripts\\clear_l1_backlog.py --profile site --by-age --days-old 7 --dry-run
  .venv\\Scripts\\python.exe scripts\\clear_l1_backlog.py --profile site --by-age --days-old 7 --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import apply_profile_argv, load_config, load_radar_env
from pg_storage import pg_storage_from_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Clear old L1 backlog without AI")
    parser.add_argument("--profile", default="site", help="legacy|site")
    parser.add_argument("--dry-run", action="store_true", help="Only count, no UPDATE")
    parser.add_argument("--apply", action="store_true", help="Apply UPDATE to Neon")
    parser.add_argument("--hours-protect", type=int, default=48)
    parser.add_argument("--top-ids-protect", type=int, default=100)
    parser.add_argument(
        "--by-age",
        action="store_true",
        help="Age mode (O40): clear only rows older than --days-old; "
             "top_ids_protect ignored",
    )
    parser.add_argument(
        "--days-old",
        type=int,
        default=7,
        help="With --by-age: clear rows older than N days (default 7)",
    )
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
        print("DATABASE_URL не задан — нечего чистить", file=sys.stderr)
        return 1

    errors: list[str] = []
    stats = pg.clear_l1_backlog_tail(
        hours_protect=args.hours_protect,
        top_ids_protect=args.top_ids_protect,
        dry_run=dry_run,
        errors=errors,
        days_old=args.days_old if args.by_age else None,
        by_age=args.by_age,
    )
    mode = "dry-run" if dry_run else "apply"
    print(f"[clear_l1_backlog] mode={mode} profile={args.profile} by_age={args.by_age}")
    print(f"  missing_before={stats['missing_before']}")
    if args.by_age:
        print(f"  older_than_{args.days_old}d={stats['older_than_Nd']}")
        print(f"  protected_48h={stats['protected']}")
    else:
        print(f"  protected={stats['protected']} (48h + top {args.top_ids_protect} id DESC)")
    print(f"  to_clear={stats['to_clear']}")
    if not dry_run:
        print(f"  cleared={stats['cleared']}")
    print(f"  missing_after={stats['missing_after']}")
    if errors:
        for e in errors:
            print(f"  error: {e}", file=sys.stderr)
        return 1
    if not dry_run and stats["missing_after"] >= 100:
        print(
            f"  warn: missing_after={stats['missing_after']} >= 100 — проверьте очередь",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
