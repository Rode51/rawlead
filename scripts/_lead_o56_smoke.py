#!/usr/bin/env python3
"""Lead smoke O56+O57 on prod."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

CMDS = [
    "grep RAWLEAD_CHILD_VERSION /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
    "test -f /opt/rawlead/src/draft_async.py && echo draft_async:yes",
    "grep -c materialize_shared_draft_for_user /opt/rawlead/src/match_push.py",
    "grep -c analyze_shared_reply_draft /opt/rawlead/src/ai_analyze.py",
    "grep OPENROUTER_MODEL_SHARED /opt/rawlead/.env.site 2>/dev/null || echo SHARED_MODEL:not_set",
    "systemctl is-active rawlead-api rawlead-bot-poll",
    "curl -s -o /dev/null -w 'feed:%{http_code}' 'http://127.0.0.1:8000/v1/feed?limit=1'",
    "grep -c 'listEl.addEventListener' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js",
    "grep -c 'min-height: 240px' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/css/rawlead.css",
    r"cd /opt/rawlead && /opt/rawlead/.venv/bin/python -c \"import sys; sys.path.insert(0,'src'); import psycopg; from config import load_config,load_radar_env,apply_profile_argv; apply_profile_argv(); load_radar_env(); c=load_config(); conn=psycopg.connect(c.database_url); cur=conn.cursor(); cur.execute(\\\"SELECT to_regclass('public.lead_draft_jobs')\\\"); print('lead_draft_jobs:', cur.fetchone()[0])\"",
]

if __name__ == "__main__":
    for c in CMDS:
        print("===", c[:72])
        _, o, _ = ssh.run(c, check=False)
        sys.stdout.buffer.write((o or "").strip().encode("utf-8", errors="replace") + b"\n")
