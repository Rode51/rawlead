#!/usr/bin/env python3
"""Fix CRLF on deploy/*.sh and restart radar."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

CMDS = [
    r"find /opt/rawlead/deploy -name '*.sh' -exec sed -i 's/\r$//' {} \;",
    "chmod +x /opt/rawlead/deploy/*.sh",
    "systemctl restart rawlead-radar",
    "sleep 8",
    "systemctl is-active rawlead-radar",
    "ps aux | grep -E 'main.py|tg_main' | grep site | grep -v grep",
    "tail -8 /opt/rawlead/data/radar_site.log",
]

if __name__ == "__main__":
    for c in CMDS:
        print("===", c)
        _, o, e = ssh.run(c, check=False)
        sys.stdout.buffer.write((o or e or "(empty)\n").encode("utf-8", errors="replace"))
