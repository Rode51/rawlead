"""O202: export TG spam corpus count + last N rows for owner review."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from dotenv import load_dotenv

from tg_spam_corpus import fetch_corpus_summary


def main() -> int:
    load_dotenv(_ROOT / ".env")
    parser = argparse.ArgumentParser(description="TG spam corpus export (count + recent)")
    parser.add_argument("--limit", type=int, default=20, help="recent rows (default 20)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    db_url = (os.getenv("DATABASE_URL") or "").strip()
    if not db_url:
        print("DATABASE_URL missing", file=sys.stderr)
        return 1

    summary = fetch_corpus_summary(db_url, limit=args.limit)
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    print(f"tg_spam_corpus count={summary['count']}")
    for row in summary.get("recent") or []:
        title = (row.get("title") or "").replace("\n", " ")[:80]
        cat = row.get("category") or "—"
        print(
            f"  #{row.get('lead_id')} {row.get('source')} [{cat}] "
            f"{row.get('marked_at')} — {title}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
