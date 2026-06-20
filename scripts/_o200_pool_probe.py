#!/usr/bin/env python3
"""O200: probe regen/judge pool sizes (run on VPS or local with DATABASE_URL)."""
from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from dotenv import load_dotenv

load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.site", override=True)

import psycopg  # noqa: E402


def main() -> int:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        print("DATABASE_URL missing")
        return 2
    host = url.split("@")[1].split("/")[0] if "@" in url else "?"
    print(f"db_host={host}")
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM leads")
            print(f"leads_total={cur.fetchone()[0]}")
            cur.execute(
                """
                SELECT COUNT(*) FROM leads
                WHERE is_visible=TRUE
                  AND COALESCE(NULLIF(TRIM(reply_draft), ''), '') <> ''
                """
            )
            print(f"visible_with_draft={cur.fetchone()[0]}")
            cur.execute(
                """
                SELECT category, COUNT(*) FROM leads
                WHERE is_visible=TRUE
                  AND COALESCE(NULLIF(TRIM(reply_draft), ''), '') <> ''
                  AND created_at >= '2026-06-01'
                GROUP BY category ORDER BY 1
                """
            )
            print("fresh_draft_by_cat:", dict(cur.fetchall()))
            cur.execute(
                """
                SELECT category, COUNT(*) FROM leads
                WHERE is_visible=TRUE
                  AND COALESCE(NULLIF(TRIM(task_summary), ''), '') <> ''
                  AND LOWER(TRIM(ai_verdict)) IN ('брать','брат','take','ok','сомнительно','maybe')
                GROUP BY category ORDER BY 1
                """
            )
            print("regen_pool_by_cat:", dict(cur.fetchall()))
            cur.execute(
                """
                SELECT COUNT(*) FROM leads
                WHERE is_visible=TRUE
                  AND COALESCE(NULLIF(TRIM(task_summary), ''), '') <> ''
                  AND LOWER(TRIM(ai_verdict)) IN ('брать','брат','take','ok','сомнительно','maybe')
                """
            )
            print(f"regen_pool_total={cur.fetchone()[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
