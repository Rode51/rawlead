#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh

REMOTE = r"""
cd /opt/rawlead && sudo -u rawlead .venv/bin/python << 'PY'
import os, json
import psycopg
from dotenv import load_dotenv
load_dotenv("/opt/rawlead/.env.site")
with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    with conn.cursor() as cur:
        for lid in (7051, 7019):
            cur.execute(
                "SELECT id, left(title,80), ai_verdict, lead_tags, body, tools_required FROM leads WHERE id=%s",
                (lid,),
            )
            r = cur.fetchone()
            print("LEAD", lid, json.dumps(r, ensure_ascii=False, default=str))
PY
"""

if __name__ == "__main__":
    _, o, e = ssh.run(REMOTE.strip(), check=False)
    sys.stdout.buffer.write((o or e or "").encode("utf-8", errors="replace"))
