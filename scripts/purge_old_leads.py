"""RETENTION-7D: удалить leads старше N дней (users/user_tags/subscriptions не трогаем).

  .venv\\Scripts\\python.exe scripts\\purge_old_leads.py --dry-run
  .venv\\Scripts\\python.exe scripts\\purge_old_leads.py --apply

VPS cron (после stress): daily @03:15 — см. deploy/systemd/rawlead-purge-leads.*
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    enc = getattr(_stream, "encoding", None) or ""
    if enc.lower() != "utf-8":
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import load_radar_env

_DEFAULT_DAYS = 7


def _count_and_delete(*, apply: bool, days: int) -> int:
    load_radar_env()
    import os

    import psycopg

    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise SystemExit("DATABASE_URL not set")

    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)::int
                FROM leads
                WHERE created_at < NOW() - make_interval(days => %s)
                """,
                (int(days),),
            )
            row = cur.fetchone()
            count = int(row[0]) if row else 0
            if apply and count > 0:
                cur.execute(
                    """
                    DELETE FROM leads
                    WHERE created_at < NOW() - make_interval(days => %s)
                    """,
                    (int(days),),
                )
            conn.commit()
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Purge leads older than N days")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="only count rows to delete")
    mode.add_argument("--apply", action="store_true", help="DELETE old leads")
    parser.add_argument("--days", type=int, default=_DEFAULT_DAYS, help=f"retention window (default {_DEFAULT_DAYS})")
    args = parser.parse_args()

    count = _count_and_delete(apply=bool(args.apply), days=args.days)
    verb = "deleted" if args.apply else "would delete"
    print(f"purge_old_leads: {verb} {count} row(s) older than {args.days} day(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
