#!/usr/bin/env python3
"""Lead smoke O54 on prod."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

CMDS = [
    "grep -c 'align-items: start' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/css/rawlead.css",
    "grep -A5 'rl-feed-list .rl-lead-card {' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/css/rawlead.css | grep -c 'height: auto'",
    "test -f /opt/rawlead/src/reply_draft_strip.py && echo reply_draft_strip:yes || echo reply_draft_strip:no",
    "grep -c strip_reply_draft_price_deadline /opt/rawlead/src/api_server.py",
    "grep -c 'без срока' /opt/rawlead/src/ai_analyze.py",
    "python3 -c \"import sys; sys.path.insert(0,'/opt/rawlead/src'); from reply_draft_strip import strip_reply_draft_price_deadline as s; t='Добрый день. Python и Neon. Ориентировочный срок — 2 недели, стоимость — от 45 000 руб.'; o=s(t); print('strip_ok:', '45 000' not in o and 'Python' in o)\"",
    "grep \"RAWLEAD_CHILD_VERSION\" /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
    "systemctl is-active rawlead-api",
    "curl -s -o /dev/null -w 'lenta:%{http_code}' 'https://rawlead.ru/lenta/'",
]

if __name__ == "__main__":
    for c in CMDS:
        print("===", c[:72])
        _, o, _ = ssh.run(c, check=False)
        sys.stdout.buffer.write((o or "").strip().encode("utf-8", errors="replace") + b"\n")
