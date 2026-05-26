"""Backfill leads.category в Neon через infer_lead_category (P7).

Не трогает dogfood PROFILE / ai_analyze — только колонка category.

Запуск:
  python scripts/backfill_lead_category.py --dry-run
  python scripts/backfill_lead_category.py
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

import psycopg  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from lead_category import CATEGORIES, infer_lead_category  # noqa: E402

_SELECT = """
SELECT id, title, body, lead_tags
FROM leads
WHERE category IS NULL OR TRIM(category) = ''
ORDER BY id
"""


def _parse_tags(raw: object) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(t).strip() for t in raw if str(t).strip()]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [str(t).strip() for t in parsed if str(t).strip()]
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill leads.category в Neon")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только подсчёт и примеры, без UPDATE",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Макс. строк (0 = все NULL)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Размер батча UPDATE",
    )
    args = parser.parse_args()

    load_dotenv(_ROOT / ".env")
    import os

    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url:
        raise SystemExit("DATABASE_URL не задан (см. .env)")

    batch_size = max(1, args.batch_size)
    limit = max(0, args.limit)

    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM leads WHERE category IS NULL OR TRIM(category) = ''")
            pending = int(cur.fetchone()[0])
            print(f"Строк без category: {pending}")

            if pending == 0:
                return

            sql = _SELECT
            if limit:
                sql += f" LIMIT {limit}"

            cur.execute(sql)
            rows = cur.fetchall()

        updates: list[tuple[int, str]] = []
        counts: Counter[str] = Counter()

        for lead_id, title, body, lead_tags_raw in rows:
            tags = _parse_tags(lead_tags_raw)
            cat = infer_lead_category(title or "", body or "", tags)
            updates.append((lead_id, cat))
            counts[cat] += 1

        print(f"Будет обновлено: {len(updates)}")
        for cat in (*CATEGORIES, "other"):
            if counts[cat]:
                print(f"  {cat}: {counts[cat]}")

        if updates[:3]:
            sample = updates[:3]
            print("Примеры:", ", ".join(f"id={i}->{c}" for i, c in sample))

        if args.dry_run:
            print("dry-run: UPDATE не выполнен")
            return

        updated = 0
        with conn.cursor() as cur:
            for i in range(0, len(updates), batch_size):
                chunk = updates[i : i + batch_size]
                cur.executemany(
                    "UPDATE leads SET category = %s WHERE id = %s",
                    [(cat, lid) for lid, cat in chunk],
                )
                updated += len(chunk)
                conn.commit()
                print(f"commit: {updated}/{len(updates)}")

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM leads WHERE category IS NULL OR TRIM(category) = ''")
            left = int(cur.fetchone()[0])
        print(f"Готово. Осталось без category: {left}")


if __name__ == "__main__":
    main()
