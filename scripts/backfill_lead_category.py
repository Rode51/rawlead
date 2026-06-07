"""Backfill leads.category в Neon через resolve_lead_category (O126).

Не трогает dogfood PROFILE / ai_analyze — только колонка category.

Запуск:
  python scripts/backfill_lead_category.py --dry-run
  python scripts/backfill_lead_category.py --reconcile-visible
  python scripts/backfill_lead_category.py --reconcile-visible --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

import psycopg  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from lead_category import CATEGORIES, OTHER_CATEGORY, infer_lead_category, resolve_lead_category  # noqa: E402

_SELECT_NULL = """
SELECT id, title, body, lead_tags
FROM leads
WHERE category IS NULL OR TRIM(category) = ''
ORDER BY id
"""

_SELECT_RECONCILE = """
SELECT id, title, body, lead_tags, category
FROM leads
WHERE is_visible = TRUE
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


def _write_sql_log(path: Path, updates: list[tuple[int, str, str]]) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"-- backfill_lead_category reconcile {ts}",
        f"-- rows: {len(updates)}",
        "",
    ]
    for lead_id, old_cat, new_cat in updates[:50]:
        lines.append(
            f"UPDATE leads SET category = '{new_cat}' WHERE id = {lead_id};"
            f" -- was {old_cat or 'NULL'}"
        )
    if len(updates) > 50:
        lines.append(f"-- ... and {len(updates) - 50} more")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
        help="Макс. строк (0 = все)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Размер батча UPDATE",
    )
    parser.add_argument(
        "--reconcile-visible",
        action="store_true",
        help="O126: visible leads — stored := resolve_lead_category(title, body, tags)",
    )
    parser.add_argument(
        "--sql-log",
        type=str,
        default="data/backfill_o126_category.sql",
        help="Путь к SQL log (относительно repo root)",
    )
    args = parser.parse_args()

    load_dotenv(_ROOT / ".env")
    import os

    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url:
        raise SystemExit("DATABASE_URL не задан (см. .env)")

    batch_size = max(1, args.batch_size)
    limit = max(0, args.limit)
    reconcile = args.reconcile_visible

    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            if reconcile:
                cur.execute("SELECT COUNT(*) FROM leads WHERE is_visible = TRUE")
                pending = int(cur.fetchone()[0])
                print(f"Visible leads для reconcile: {pending}")
                sql = _SELECT_RECONCILE
            else:
                cur.execute(
                    "SELECT COUNT(*) FROM leads WHERE category IS NULL OR TRIM(category) = ''"
                )
                pending = int(cur.fetchone()[0])
                print(f"Строк без category: {pending}")
                sql = _SELECT_NULL

            if pending == 0:
                return

            if limit:
                sql += f" LIMIT {limit}"

            cur.execute(sql)
            rows = cur.fetchall()

        updates: list[tuple[int, str]] = []
        log_rows: list[tuple[int, str, str]] = []
        counts: Counter[str] = Counter()

        for row in rows:
            if reconcile:
                lead_id, title, body, lead_tags_raw, stored = row
                tags = _parse_tags(lead_tags_raw)
                cat = resolve_lead_category(stored, title or "", body or "", tags)
                old = (stored or "").strip() or "NULL"
                if cat == (stored or "").strip():
                    continue
                updates.append((lead_id, cat))
                log_rows.append((lead_id, old, cat))
                counts[cat] += 1
            else:
                lead_id, title, body, lead_tags_raw = row
                tags = _parse_tags(lead_tags_raw)
                cat = infer_lead_category(title or "", body or "", tags)
                updates.append((lead_id, cat))
                log_rows.append((lead_id, "NULL", cat))
                counts[cat] += 1

        print(f"Будет обновлено: {len(updates)}")
        for cat in (*CATEGORIES, OTHER_CATEGORY):
            if counts[cat]:
                print(f"  {cat}: {counts[cat]}")

        if updates[:3]:
            sample = updates[:3]
            print("Примеры:", ", ".join(f"id={i}->{c}" for i, c in sample))

        if log_rows:
            log_path = _ROOT / args.sql_log
            _write_sql_log(log_path, log_rows)
            print(f"SQL log: {log_path}")

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

        if reconcile:
            print("Reconcile visible: готово.")
        else:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM leads WHERE category IS NULL OR TRIM(category) = ''"
                )
                left = int(cur.fetchone()[0])
            print(f"Готово. Осталось без category: {left}")


if __name__ == "__main__":
    main()
