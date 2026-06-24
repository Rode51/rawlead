"""Delist feed rows that should never be public: physical services + ai_verdict МИМО.

Usage:
  python scripts/backfill_feed_hygiene_vps.py --dry-run
  python scripts/backfill_feed_hygiene_vps.py

VPS:
  sudo -u rawlead env RADAR_PROFILE=site PYTHONPATH=/opt/rawlead/src \\
    /opt/rawlead/.venv/bin/python /opt/rawlead/scripts/backfill_feed_hygiene_vps.py
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

import psycopg  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from vacancy_filter import is_physical_service_job  # noqa: E402

_SELECT_VISIBLE = """
SELECT id, external_id, source, title, body, ai_verdict
FROM leads
WHERE is_visible = TRUE
ORDER BY id
"""


def _should_delist(*, title: str, body: str, ai_verdict: str | None) -> str | None:
    if (ai_verdict or "").strip() == "МИМО":
        return "mimo_verdict"
    if is_physical_service_job(title, body):
        return "o245_physical_visit"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Hide physical / МИМО rows from public feed")
    parser.add_argument("--dry-run", action="store_true", help="Only print matches")
    parser.add_argument("--limit", type=int, default=0, help="Max rows (0 = all)")
    args = parser.parse_args()

    load_dotenv(_ROOT / ".env")
    load_dotenv(_ROOT / ".env.site", override=True)
    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url:
        raise SystemExit("DATABASE_URL not set")

    matches: list[tuple[int, str, str, str, str]] = []
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(_SELECT_VISIBLE)
            rows = cur.fetchall()
        for row in rows:
            lead_id, external_id, source, title, body, ai_verdict = row
            title_s = (title or "").strip()
            body_s = (body or "").strip()
            reason = _should_delist(title=title_s, body=body_s, ai_verdict=ai_verdict)
            if reason is None:
                continue
            matches.append(
                (lead_id, str(source or ""), str(external_id or ""), reason, title_s[:80])
            )
            if args.limit and len(matches) >= args.limit:
                break

        print(f"feed_hygiene_matches={len(matches)} dry_run={args.dry_run}")
        for lead_id, source, external_id, reason, title_preview in matches[:40]:
            print(
                f"  id={lead_id} source={source} external_id={external_id} "
                f"reason={reason} title={title_preview!r}"
            )
        if len(matches) > 40:
            print(f"  ... and {len(matches) - 40} more")

        if args.dry_run or not matches:
            return 0

        from pg_storage import NeonLeadStorage  # noqa: E402

        pg = NeonLeadStorage(url)
        delisted = 0
        for lead_id, _, _, reason, _ in matches:
            if pg.delist_lead(lead_id, reason=reason):
                delisted += 1
        print(f"delisted={delisted}/{len(matches)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
