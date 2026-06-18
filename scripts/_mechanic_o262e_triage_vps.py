#!/usr/bin/env python3
"""O262e Mechanic triage: fetch_end, debug HTML, PG youdo visibility on VPS."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

REMOTE = r"""
echo '=== fetch_end last 12 ==='
grep 'youdo:trace stage=fetch_end' /opt/rawlead/data/radar_site.log 2>/dev/null | tail -12

echo '=== fetch:youdo last 8 ==='
grep 'fetch:youdo' /opt/rawlead/data/radar_site.log 2>/dev/null | tail -8

echo '=== proxy state ==='
cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
import sqlite3
from pathlib import Path
from exchange_proxy import youdo_dc_alive_urls, exchange_primary_proxy_url

db = Path("/opt/rawlead/data/projects.db")
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM exchange_proxy_bans WHERE pool_key LIKE 'youdo%'")
print("youdo_bans", cur.fetchone()[0])
cur.execute(
    "SELECT pool_key, reason, banned_at FROM exchange_proxy_bans WHERE pool_key LIKE 'youdo%' ORDER BY banned_at DESC LIMIT 8"
)
for row in cur.fetchall():
    print(" ban", row[0], row[1][:60] if row[1] else "")
conn.close()
print("dc_alive", len(youdo_dc_alive_urls()), "/4")
prim = exchange_primary_proxy_url("youdo") or ""
print("primary_hint", prim.split("@")[-1][:50] if prim else "none")
PY

echo '=== debug html latest ==='
cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
import glob
from pathlib import Path
files = sorted(glob.glob("/opt/rawlead/data/debug_listings/youdo_antibot_*.html"))
if not files:
    print("no debug html")
else:
    p = Path(files[-1])
    h = p.read_text(encoding="utf-8", errors="replace")
    print("file", p.name, "len", len(h))
    keys = [
        "servicepipe", "exhkqyad", "spinner", "robot", "Показать списком",
        "data-id", "__NEXT", "tasks-all", "antibot", "captcha",
    ]
    for k in keys:
        print(f"  {k!r}:", h.lower().count(k.lower()))
    print("head:", h[:600].replace("\n", " ")[:600])
PY

echo '=== 14:29 success context ==='
grep '2026-06-17 14:2' /opt/rawlead/data/radar_site.log | grep -E 'youdo|fetch:youdo' | head -35

echo '=== list_view traces ==='
grep 'youdo:trace stage=list_view' /opt/rawlead/data/radar_site.log | tail -6

echo '=== PG youdo visibility ==='
cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
import os
from dotenv import load_dotenv
load_dotenv("/opt/rawlead/.env.site")
load_dotenv("/opt/rawlead/.env")
dsn = os.environ.get("DATABASE_URL") or os.environ.get("NEON_DATABASE_URL")
if not dsn:
    print("no DATABASE_URL")
else:
    import psycopg
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM leads WHERE source='youdo'")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM leads WHERE source='youdo' AND is_visible=TRUE")
            vis = cur.fetchone()[0]
            cur.execute(
                "SELECT COUNT(*) FROM leads WHERE source='youdo' AND is_visible=TRUE "
                "AND created_at > NOW() - INTERVAL '48 hours'"
            )
            vis48 = cur.fetchone()[0]
            cur.execute(
                "SELECT id, is_visible, created_at, LEFT(COALESCE(title,''),40) "
                "FROM leads WHERE source='youdo' ORDER BY created_at DESC LIMIT 8"
            )
            rows = cur.fetchall()
            print("total", total, "visible", vis, "visible_48h", vis48)
            for r in rows:
                print(" ", r)
PY

echo '=== feed API youdo count ==='
curl -fsS -m 20 'https://rawlead.ru/wp-json/rawlead/v1/feed?limit=100' 2>/dev/null | sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
import json, sys
try:
    data = json.load(sys.stdin)
    items = data if isinstance(data, list) else data.get('items') or data.get('leads') or []
    youdo = [x for x in items if (x.get('source') or '') == 'youdo']
    print('feed_items', len(items), 'youdo_in_page', len(youdo))
    if youdo:
        print('sample', youdo[0].get('id'), (youdo[0].get('title') or '')[:40])
except Exception as e:
    print('parse_err', e)
PY
"""


def main() -> int:
    _, out, err = ssh.run(REMOTE.strip(), check=False)
    text = (out or err or "").replace("\r\n", "\n")
    out_path = Path(__file__).resolve().parents[1] / "data" / "_mechanic_o262e_triage.txt"
    try:
        out_path.write_text(text, encoding="utf-8")
    except OSError:
        pass
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
