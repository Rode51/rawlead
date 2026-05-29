#!/usr/bin/env python3
"""Lead smoke after Wave-2 deploy."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

CMDS = [
    "systemctl is-active rawlead-api rawlead-radar",
    "grep -c sanitize_l1_cms_tags /opt/rawlead/src/skills_catalog.py",
    "grep -c 'callback_data.*draft:' /opt/rawlead/src/match_push.py",
    "grep -c draft_rate_limit /opt/rawlead/src/match_push.py",
    "grep -c 'Повторить' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js",
    "grep 'grid-template-columns: repeat(2' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/css/rawlead.css | wc -l",
    "curl -s -o /dev/null -w 'feed:%{http_code}' 'http://127.0.0.1:8000/v1/feed?limit=1'",
    "curl -s -o /dev/null -w ' ops:%{http_code}' 'http://127.0.0.1:8000/ops/'",
    "systemctl is-active rawlead-bot 2>/dev/null || ps aux | grep bot_poll | grep -v grep | head -1",
]

if __name__ == "__main__":
    rc = 0
    for c in CMDS:
        print("===", c[:72])
        _, o, e = ssh.run(c, check=False)
        line = (o or e or "(empty)").strip()
        sys.stdout.buffer.write(line.encode("utf-8", errors="replace") + b"\n")
        if "active" in c and "rawlead-api" in c and "active" not in line:
            rc = 1
        if c.startswith("curl") and "feed:200" in c and "feed:200" not in line:
            rc = 1
    raise SystemExit(rc)
