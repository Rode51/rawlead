#!/usr/bin/env python3
"""Lead smoke O52 on prod."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

CMDS = [
    "systemctl is-active rawlead-api rawlead-radar",
    "grep -c strip_tg_draft_price_deadline /opt/rawlead/src/match_push.py",
    "grep -c 'rl-badge--replied' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js",
    "grep -c 'rl-cabinet-notif__chips' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/page-cabinet.php",
    "grep -c ':has(.rl-lead-card.is-expanded)' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/css/rawlead.css || echo 0",
    "grep \"RAWLEAD_CHILD_VERSION\" /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
    "curl -s -o /dev/null -w 'feed:%{http_code}' 'http://127.0.0.1:8000/v1/feed?limit=1'",
]

if __name__ == "__main__":
    for c in CMDS:
        print("===", c[:70])
        _, o, _ = ssh.run(c, check=False)
        sys.stdout.buffer.write((o or "").strip().encode("utf-8", errors="replace") + b"\n")
