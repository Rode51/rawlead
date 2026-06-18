"""O216b: one-off audit script — export quiz-eligible leads per niche to CSV/JSON.

Usage (VPS or local with .env):
    python scripts/quiz_pool_audit.py [--out data/quiz_pool_candidates.csv]

Queries leads WHERE is_visible=TRUE AND ai_score>=60 AND category IN quiz niches,
outputs id/category/title/task_summary/lead_tags for manual curation.
Does NOT write quiz_pool_allowlist.json — that is maintained manually.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

QUIZ_NICHES = ("dev", "design", "marketing", "text")
DEFAULT_OUT = _ROOT / "data" / "quiz_pool_candidates.csv"


def _get_conn():
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("RAWLEAD_DATABASE_URL")
    if not db_url:
        env_file = _ROOT / ".env.site"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    db_url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")
    import psycopg2  # type: ignore
    return psycopg2.connect(db_url)


def export_candidates(out_path: Path, min_score: int = 60) -> list[dict]:
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, category, ai_score, title, task_summary, lead_tags
                FROM leads
                WHERE is_visible = TRUE
                  AND ai_score >= %s
                  AND category = ANY(%s)
                  AND task_summary IS NOT NULL
                  AND task_summary != ''
                ORDER BY category, ai_score DESC, created_at DESC
                LIMIT 400
                """,
                (min_score, list(QUIZ_NICHES)),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    records = [
        {
            "id": row[0],
            "category": row[1],
            "ai_score": row[2],
            "title": row[3] or "",
            "task_summary": (row[4] or "").strip(),
            "lead_tags": row[5] if row[5] else [],
        }
        for row in rows
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "category", "ai_score", "title", "task_summary", "lead_tags"])
        writer.writeheader()
        for rec in records:
            writer.writerow({**rec, "lead_tags": json.dumps(rec["lead_tags"], ensure_ascii=False)})

    print(f"Exported {len(records)} candidates → {out_path}")
    per_niche = {}
    for rec in records:
        per_niche.setdefault(rec["category"], 0)
        per_niche[rec["category"]] += 1
    for niche, cnt in sorted(per_niche.items()):
        print(f"  {niche}: {cnt}")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Export quiz pool candidates for curation")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output CSV path")
    parser.add_argument("--min-score", type=int, default=60, help="Minimum ai_score (default 60)")
    args = parser.parse_args()
    export_candidates(Path(args.out), min_score=args.min_score)


if __name__ == "__main__":
    main()
