#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh

CMDS = [
    "systemctl status rawlead-radar --no-pager -l | head -20",
    "systemctl is-active rawlead-radar rawlead-api",
    "test -f /opt/rawlead/src/l1_pool.py && wc -l /opt/rawlead/src/l1_pool.py",
    "grep L1_BACKLOG_DRAIN /opt/rawlead/.env.site || echo default_drain",
    "ps aux | grep -E 'main.py|tg_main' | grep -v grep",
    "tail -15 /opt/rawlead/data/radar_site.log",
]

for c in CMDS:
    print("===", c[:60])
    _, o, e = ssh.run(c, check=False)
    sys.stdout.buffer.write((o or e or b"").encode("utf-8") if isinstance(o or e, bytes) else (o or e or "(empty)\n").encode("utf-8", errors="replace"))
