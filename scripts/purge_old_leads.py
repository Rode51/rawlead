"""RETENTION-2D: удалить leads старше N дней (users/user_tags/subscriptions не трогаем).

O181: второй проход — DELETE delisted rows (is_visible=false + delist_reason) после
DELIST_PURGE_DAYS (env, default 1). FK child tables ON DELETE CASCADE.

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

_DEFAULT_DAYS = 2
_DEFAULT_DELIST_PURGE_DAYS = 1


def _delist_purge_days() -> int:
    import os

    raw = (os.getenv("DELIST_PURGE_DAYS") or "").strip()
    if not raw:
        return _DEFAULT_DELIST_PURGE_DAYS
    try:
        return max(1, int(raw))
    except ValueError:
        return _DEFAULT_DELIST_PURGE_DAYS


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


def _count_and_delete_delisted(*, apply: bool, days: int) -> int:
    """DELETE hidden leads with delist_reason set (drafts/replies cascade)."""
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
                WHERE is_visible = FALSE
                  AND delist_reason IS NOT NULL
                  AND COALESCE(last_source_check_at, created_at)
                      < NOW() - make_interval(days => %s)
                """,
                (int(days),),
            )
            row = cur.fetchone()
            count = int(row[0]) if row else 0
            if apply and count > 0:
                cur.execute(
                    """
                    DELETE FROM leads
                    WHERE is_visible = FALSE
                      AND delist_reason IS NOT NULL
                      AND COALESCE(last_source_check_at, created_at)
                          < NOW() - make_interval(days => %s)
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

    apply = bool(args.apply)
    count = _count_and_delete(apply=apply, days=args.days)
    verb = "deleted" if apply else "would delete"
    print(f"purge_old_leads: {verb} {count} row(s) older than {args.days} day(s)")

    delist_days = _delist_purge_days()
    delist_count = _count_and_delete_delisted(apply=apply, days=delist_days)
    delist_verb = "deleted" if apply else "would delete"
    print(
        f"purge_delisted: {delist_verb} {delist_count} row(s) "
        f"hidden with delist_reason older than {delist_days} day(s)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
