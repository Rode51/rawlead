#!/usr/bin/env python3
"""Lead smoke O53 on prod."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

CMDS = [
    "grep -c 'formatBudgetDisplay' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js",
    "grep -c 'formatBudgetDisplay' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-cabinet.js",
    "grep -c 'is-expanded' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/css/rawlead.css",
    "grep -c 'grid-column: 1 / -1' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/css/rawlead.css || echo 0",
    "grep -A3 'rl-lead-card.is-expanded' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/css/rawlead.css | grep grid-column || echo 'no grid-column on expanded'",
    "grep -c 'rl-feed-card__head' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-cabinet.js",
    "python3 -c \"import re; t=open('/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-cabinet.js').read(); m=re.search(r'function renderCard[\\s\\S]*?viewsHeadHtml', t); print('cabinet renderCard uses views:', bool(m))\"",
    "grep \"RAWLEAD_CHILD_VERSION\" /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
    "curl -s -o /dev/null -w 'lenta:%{http_code}' 'https://rawlead.ru/lenta/'",
    "curl -s -o /dev/null -w 'cabinet:%{http_code}' 'https://rawlead.ru/cabinet/'",
]

if __name__ == "__main__":
    for c in CMDS:
        print("===", c[:72])
        _, o, _ = ssh.run(c, check=False)
        sys.stdout.buffer.write((o or "").strip().encode("utf-8", errors="replace") + b"\n")
