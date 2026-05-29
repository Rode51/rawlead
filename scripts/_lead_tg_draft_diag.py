#!/usr/bin/env python3
"""Lead diag: TG draft callback path on prod."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

CMDS = [
    "systemctl is-active rawlead-bot-poll rawlead-radar",
    "grep MATCH_PUSH /opt/rawlead/.env.site | head -1",
    "grep -c handle_tg_draft_callback /opt/rawlead/src/match_push.py",
    "journalctl -u rawlead-bot-poll -n 8 --no-pager 2>/dev/null | tail -8",
    "grep tg:draft /opt/rawlead/data/radar_site.log 2>/dev/null | tail -5 || echo 'no tg:draft in radar log'",
    r"cd /opt/rawlead && python3 -c \"import sys; sys.path.insert(0,'src'); from config import load_config, load_radar_env, apply_profile_argv; apply_profile_argv(); load_radar_env(); c=load_config(); import requests; r=requests.get('https://api.telegram.org/bot'+c.telegram_bot_token+'/getWebhookInfo',timeout=15); print(r.text[:400])\"",
]

if __name__ == "__main__":
    for c in CMDS:
        print("===", c[:72])
        _, o, _ = ssh.run(c, check=False)
        sys.stdout.buffer.write((o or "").strip().encode("utf-8", errors="replace") + b"\n")
