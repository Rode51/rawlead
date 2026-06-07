#!/usr/bin/env python3
"""Apply sql/020_trial_subscription.sql (O107 trial columns)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.site", override=False)

import psycopg  # noqa: E402


def main() -> int:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("NO DATABASE_URL")
        return 1
    sql_path = _ROOT / "sql" / "020_trial_subscription.sql"
    sql = sql_path.read_text(encoding="utf-8")
    with psycopg.connect(url) as conn:
        conn.execute(sql)
        conn.commit()
    print("NEON-020 OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
