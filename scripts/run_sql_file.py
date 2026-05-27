"""Выполнить один .sql файл в Neon (DATABASE_URL из .env)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

import psycopg  # noqa: E402
from dotenv import load_dotenv  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sql_file", type=Path, help="Путь к .sql от корня репо")
    args = parser.parse_args()

    load_dotenv(_ROOT / ".env")
    import os

    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url:
        raise SystemExit("DATABASE_URL не задан (см. .env)")

    path = args.sql_file
    if not path.is_absolute():
        path = _ROOT / path
    sql = path.read_text(encoding="utf-8")

    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()

    print(f"OK: {path.name}")


if __name__ == "__main__":
    main()
