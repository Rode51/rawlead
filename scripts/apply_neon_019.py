#!/usr/bin/env python3
"""Apply sql/019_support_tickets.sql (Neon support threads)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)
load_dotenv("/opt/rawlead/.env.site", override=False)

import psycopg  # noqa: E402


def main() -> int:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("NO DATABASE_URL")
        return 1
    sql_path = Path("/opt/rawlead/sql/019_support_tickets.sql")
    if not sql_path.is_file():
        sql_path = _ROOT / "sql" / "019_support_tickets.sql"
    sql = sql_path.read_text(encoding="utf-8")
    with psycopg.connect(url) as conn:
        conn.execute(sql)
        conn.commit()
    print("NEON-019 OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
