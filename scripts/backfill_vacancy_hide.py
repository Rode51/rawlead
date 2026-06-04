"""O114: скрыть уже видимые лиды с маркерами вакансии в Neon (без regen).

  python scripts/backfill_vacancy_hide.py --dry-run
  python scripts/backfill_vacancy_hide.py --limit 500
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

import psycopg  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from vacancy_filter import is_staff_vacancy  # noqa: E402

_SELECT = """
SELECT id, title, body
FROM leads
WHERE is_visible = TRUE
  AND LOWER(TRIM(COALESCE(ai_verdict, ''))) NOT IN ('мимо', 'пропустить', 'skip', '')
ORDER BY id DESC
"""

_UPDATE = """
UPDATE leads
SET is_visible = FALSE,
    ai_verdict = 'МИМО',
    ai_score = 0,
    task_summary = 'вакансии, не фриланс-заказ',
    lead_tags = '[]'::jsonb
WHERE id = ANY(%s)
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="O114 Neon backfill: hide staff vacancies")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="max rows to scan (0=all visible)")
    args = parser.parse_args()

    load_dotenv(_ROOT / ".env")
    import os

    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url:
        print("DATABASE_URL не задан", file=sys.stderr)
        return 2

    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            sql = _SELECT
            if args.limit > 0:
                sql += f" LIMIT {int(args.limit)}"
            cur.execute(sql)
            rows = cur.fetchall()

        hits: list[tuple[int, str]] = []
        for lead_id, title, body in rows:
            t = (title or "").strip()
            b = (body or "").strip()
            if is_staff_vacancy(t, b):
                hits.append((int(lead_id), t[:80]))

        print(f"scanned={len(rows)} vacancy_hits={len(hits)}")
        for lid, preview in hits[:20]:
            print(f"  #{lid} {preview!r}")
        if len(hits) > 20:
            print(f"  ... +{len(hits) - 20} more")

        if args.dry_run or not hits:
            return 0

        ids = [h[0] for h in hits]
        with conn.cursor() as cur:
            cur.execute(_UPDATE, (ids,))
        conn.commit()
        print(f"updated={len(ids)} is_visible=false ai_verdict=МИМО")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
