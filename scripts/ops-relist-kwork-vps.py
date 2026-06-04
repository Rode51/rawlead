#!/usr/bin/env python3
"""Run kwork source_gone relist on VPS Neon."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh

REMOTE = r"""
cd /opt/rawlead && sudo -u rawlead .venv/bin/python << 'PY'
import os
import psycopg
from dotenv import load_dotenv

load_dotenv("/opt/rawlead/.env.site")
sql = '''
UPDATE leads
SET is_visible = TRUE, delist_reason = NULL
WHERE source = 'kwork'
  AND delist_reason = 'source_gone'
  AND l1_completed_at >= NOW() - INTERVAL '14 days'
'''
with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    with conn.cursor() as cur:
        cur.execute(sql)
        n = cur.rowcount
    conn.commit()
print(f"relisted_kwork_source_gone={n}")
PY
"""

if __name__ == "__main__":
    _, out, err = ssh.run(REMOTE.strip(), check=False)
    print(out or err or "")
