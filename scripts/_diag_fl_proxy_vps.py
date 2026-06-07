#!/usr/bin/env python3
"""One-shot: FL proxy bans + recent ingest on VPS."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

REMOTE = r"""
echo '=== services ==='
systemctl is-active rawlead-radar rawlead-api 2>/dev/null || true
echo '=== fl log (fetch/proxy/ban/403) last 35 ==='
grep -E 'fetch:fl|fl_listing|proxy|403|banned|pool_exhausted|alive=' /opt/rawlead/data/radar_site.log 2>/dev/null | tail -35
echo '=== exchange proxy pools ==='
cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
import json
from config import load_radar_env
load_radar_env()
from exchange_proxy import exchange_alive_proxy_urls, _urls_for_source
from storage import ProjectStorage
from config import load_config

for src in ("fl", "kwork", "youdo"):
    total = len(_urls_for_source(src))
    alive = exchange_alive_proxy_urls(src)
    print(f"{src}: alive={len(alive)}/{total}")

c = load_config()
st = ProjectStorage(c.sqlite_path)
raw = st.get_setting("exchange_proxy_bans_v2") or "{}"
bans = json.loads(raw) if raw else {}
fl_bans = {k: v for k, v in bans.items() if str(k).startswith("fl:")}
print("fl_bans_count", len(fl_bans))
for k, v in list(fl_bans.items())[:10]:
    print(" ", k, str(v)[:140])
PY
echo '=== neon fl ingest ==='
cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
import os
import psycopg
from dotenv import load_dotenv

load_dotenv("/opt/rawlead/.env.site")
load_dotenv("/opt/rawlead/.env")
url = os.environ.get("DATABASE_URL", "").strip()
if not url:
    print("no DATABASE_URL")
    raise SystemExit(0)
with psycopg.connect(url) as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT count(*), max(created_at) FROM leads "
            "WHERE source='fl' AND created_at >= now() - interval '2 hours'"
        )
        print("fl_inserts_2h count,max_ts=", cur.fetchone())
        cur.execute(
            "SELECT count(*) FROM leads "
            "WHERE source='fl' AND created_at >= now() - interval '24 hours'"
        )
        print("fl_inserts_24h=", cur.fetchone()[0])
PY
"""

if __name__ == "__main__":
    _, out, err = ssh.run(REMOTE.strip(), check=False)
    sys.stdout.buffer.write((out or err or "").encode("utf-8", errors="replace"))
