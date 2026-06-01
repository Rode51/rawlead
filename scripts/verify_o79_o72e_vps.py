#!/usr/bin/env python3
"""Post-deploy smoke: O79 proxy log + O72e ai_analyze line count."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    cmds = [
        "wc -l /opt/rawlead/src/exchange_proxy.py /opt/rawlead/src/ai_analyze.py",
        'grep -c "fetch:fl proxy=" /opt/rawlead/data/radar_site.log || true',
        'grep "fetch:fl proxy=" /opt/rawlead/data/radar_site.log | tail -8 || true',
        "grep FL_PROXY_URLS /opt/rawlead/.env | cut -c1-40",
        "grep KWORK_PROXY_URLS /opt/rawlead/.env | cut -c1-40",
        "systemctl is-active rawlead-radar",
        "grep -n fetch:fl /opt/rawlead/src/fl_parser.py | head -3",
        'grep fetch: /opt/rawlead/data/radar_site.log | tail -5 || true',
    ]
    for cmd in cmds:
        print("---", cmd)
        _, out, _ = ssh.run(cmd, check=False)
        print((out or "").encode("ascii", errors="replace").decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
