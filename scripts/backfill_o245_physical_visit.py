"""O245: delist visible leads matching is_physical_service_job (onsite / logistics).

Usage:
  python scripts/backfill_o245_physical_visit.py --dry-run
  python scripts/backfill_o245_physical_visit.py
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
SELECT id, external_id, source, title, body
FROM leads
WHERE is_visible = TRUE
ORDER BY id
"""

_YOUDO_T14858651 = 14858651


def main() -> int:
    parser = argparse.ArgumentParser(description="O245 physical/onsite backfill delist")
    parser.add_argument("--dry-run", action="store_true", help="Only print matches")
    parser.add_argument("--limit", type=int, default=0, help="Max rows (0 = all)")
    args = parser.parse_args()

    load_dotenv(_ROOT / ".env")
    load_dotenv(_ROOT / ".env.site", override=True)
    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url:
        raise SystemExit("DATABASE_URL not set")

    matches: list[tuple[int, str, str, str]] = []
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(_SELECT_VISIBLE)
            rows = cur.fetchall()
        for row in rows:
            lead_id, external_id, source, title, body = row
            title_s = (title or "").strip()
            body_s = (body or "").strip()
            if not is_physical_service_job(title_s, body_s):
                continue
            matches.append((lead_id, str(source or ""), str(external_id or ""), title_s[:80]))
            if args.limit and len(matches) >= args.limit:
                break

        print(f"physical_matches={len(matches)} dry_run={args.dry_run}")
        for lead_id, source, external_id, title_preview in matches[:30]:
            print(f"  id={lead_id} source={source} external_id={external_id} title={title_preview!r}")
        if len(matches) > 30:
            print(f"  ... and {len(matches) - 30} more")

        t14858651 = [
            m for m in matches if m[2] == str(_YOUDO_T14858651) or m[2] == _YOUDO_T14858651
        ]
        if t14858651:
            print(f"t14858651_matched={t14858651[0][0]}")
        else:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, is_visible, delist_reason
                    FROM leads
                    WHERE source = 'youdo' AND external_id = %s
                    """,
                    (str(_YOUDO_T14858651),),
                )
                row = cur.fetchone()
            print(f"t14858651_neon={row}")

        if args.dry_run or not matches:
            return 0

        from pg_storage import NeonLeadStorage  # noqa: E402

        pg = NeonLeadStorage(url)
        delisted = 0
        for lead_id, _, _, _ in matches:
            if pg.delist_lead(lead_id, reason="o245_physical_visit"):
                delisted += 1
        print(f"delisted={delisted}/{len(matches)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
