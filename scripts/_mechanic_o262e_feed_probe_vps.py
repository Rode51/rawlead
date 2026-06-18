#!/usr/bin/env python3
"""O262e: PG feed visibility + PUBLIC_FEED_SOURCES on VPS."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

REMOTE = r"""
cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src RADAR_PROFILE=site .venv/bin/python - <<'PY'
import os
from dotenv import load_dotenv
load_dotenv("/opt/rawlead/.env.site")
load_dotenv("/opt/rawlead/.env")

print("PUBLIC_FEED_SOURCES", os.getenv("PUBLIC_FEED_SOURCES", "")[:120])

from public_feed import is_public_feed_source, public_feed_sources, FEED_VISIBILITY_DAYS
print("feed_sources", sorted(public_feed_sources()))
print("youdo_public", is_public_feed_source("youdo"))
print("FEED_VISIBILITY_DAYS", FEED_VISIBILITY_DAYS)

dsn = os.environ.get("DATABASE_URL") or os.environ.get("NEON_DATABASE_URL")
import psycopg
with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM leads WHERE source='youdo' AND is_visible=TRUE "
            "AND created_at > NOW() - make_interval(days => %s)",
            (FEED_VISIBILITY_DAYS,),
        )
        vis7 = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM leads WHERE source='youdo' AND is_visible=TRUE "
            "AND created_at > NOW() - INTERVAL '24 hours'"
        )
        vis24 = cur.fetchone()[0]
        cur.execute(
            "SELECT id, created_at, LEFT(COALESCE(title,''),35), delist_reason "
            "FROM leads WHERE source='youdo' AND is_visible=TRUE "
            "ORDER BY created_at DESC LIMIT 5"
        )
        vis_rows = cur.fetchall()
        cur.execute(
            "SELECT id, created_at, is_visible, LEFT(COALESCE(title,''),35), "
            "COALESCE(delist_reason,''), COALESCE(category,'') "
            "FROM leads WHERE source='youdo' "
            "AND created_at > NOW() - INTERVAL '24 hours' "
            "ORDER BY created_at DESC LIMIT 10"
        )
        recent = cur.fetchall()
        print("visible_in_feed_window", vis7, "visible_24h", vis24)
        print("latest_visible:")
        for r in vis_rows:
            print(" ", r)
        print("recent_24h:")
        for r in recent:
            print(" ", r)
PY

echo '=== api feed youdo ==='
curl -fsS -m 25 'https://rawlead.ru/v1/feed?limit=50&source=youdo' -H 'Accept: application/json' 2>/dev/null | head -c 400 || echo curl_fail
"""


def main() -> int:
    _, out, err = ssh.run(REMOTE.strip(), check=False)
    print((out or err or "").replace("\r\n", "\n"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
