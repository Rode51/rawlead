#!/usr/bin/env python3
"""Lead smoke after PRE-STRESS-PACK deploy."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

CMDS = [
    "systemctl is-active rawlead-api rawlead-radar",
    "curl -s -o /dev/null -w 'feed:%{http_code}' 'http://127.0.0.1:8000/v1/feed?limit=1'",
    "curl -s -o /dev/null -w ' ops:%{http_code}' 'http://127.0.0.1:8000/ops/'",
    "grep -n 'location /ops' /etc/nginx/sites-enabled/rawlead.ru 2>/dev/null || "
    "grep -n 'location /ops' /etc/nginx/sites-available/rawlead.ru 2>/dev/null || echo NO_OPS_BLOCK",
    "grep MATCH_PUSH /opt/rawlead/.env.site || echo NO_MATCH_PUSH",
    "test -f /opt/rawlead/src/owner_admin.py && echo owner_admin_OK",
    "grep 'F2:' /opt/rawlead/src/rank.py | head -1",
]

if __name__ == "__main__":
    rc = 0
    for c in CMDS:
        print("===", c[:72])
        _, o, e = ssh.run(c, check=False)
        line = (o or e or "(empty)").strip()
        sys.stdout.buffer.write(line.encode("utf-8", errors="replace") + b"\n")
        if "NO_OPS_BLOCK" in line:
            rc = 1
        if "feed:200" not in line and c.startswith("curl") and "feed" in c:
            if "feed:" in line and "feed:200" not in line:
                rc = 1
    raise SystemExit(rc)
