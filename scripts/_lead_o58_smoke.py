#!/usr/bin/env python3
"""Lead smoke O58: WP GET draft route on prod."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

CMDS = [
    "grep RAWLEAD_CHILD_VERSION /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
    "grep -c wp_remote_get /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/rawlead-api.php",
    "grep -c draft_proxy /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/rawlead-api.php",
    "curl -s -o /dev/null -w 'wp_draft_get:%{http_code}' 'https://rawlead.ru/wp-json/rawlead/v1/me/leads/1/draft'",
    "curl -s 'https://rawlead.ru/wp-json/rawlead/v1/me/leads/1/draft' | head -c 120",
]

if __name__ == "__main__":
    for c in CMDS:
        print("===", c[:72])
        _, o, _ = ssh.run(c, check=False)
        sys.stdout.buffer.write((o or "").strip().encode("utf-8", errors="replace") + b"\n")
