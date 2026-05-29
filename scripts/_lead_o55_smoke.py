#!/usr/bin/env python3
"""Lead smoke O55 on prod."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

CMDS = [
    "grep RAWLEAD_CHILD_VERSION /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
    "grep -c 'O55a' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/template-parts/rawlead/live-preview.php",
    "grep -c 'rl-lead-card--demo-hero' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/css/rawlead.css",
    "grep -c 'state.expandedId = null' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js",
    "grep -c ensure_bot_polling_mode /opt/rawlead/src/telegram_control.py",
    "grep -c 'tg:draft:callback' /opt/rawlead/src/match_push.py",
    "systemctl is-active rawlead-api rawlead-bot-poll",
    "curl -s -o /dev/null -w 'home:%{http_code}' 'https://rawlead.ru/'",
    "curl -s 'https://rawlead.ru/' | grep -c 'Совместимость 100%' || echo 0",
    "curl -s 'https://rawlead.ru/' | grep -c 'ИДЕАЛЬНО' || echo 0",
    "curl -s 'https://rawlead.ru/' | grep -c 'Совместимость 42%' || echo 0",
]

if __name__ == "__main__":
    ok = True
    for c in CMDS:
        print("===", c[:72])
        _, o, _ = ssh.run(c, check=False)
        line = (o or "").strip()
        sys.stdout.buffer.write(line.encode("utf-8", errors="replace") + b"\n")
        if "home:200" in line or line == "active":
            pass
        elif "home:" in c and "200" not in line:
            ok = False
    sys.exit(0 if ok else 1)
