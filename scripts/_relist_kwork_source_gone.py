"""One-off: вернуть в ленту ложно delist Kwork (source_gone)."""
import os
import sys

import psycopg

sql = """
UPDATE leads
SET is_visible = TRUE, delist_reason = NULL
WHERE source = 'kwork'
  AND delist_reason = 'source_gone'
  AND l1_completed_at >= NOW() - INTERVAL '14 days'
"""

def main() -> int:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("DATABASE_URL missing", file=sys.stderr)
        return 1
    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            n = cur.rowcount
        conn.commit()
    print(f"relisted_kwork_source_gone={n}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
