#!/usr/bin/env python3
"""Quick E2 status on VPS (UTF-8 safe)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

CMDS = [
    "systemctl is-active rawlead-api rawlead-radar rawlead-radar-legacy",
    "wc -l /opt/rawlead/data/radar_site.log 2>/dev/null || echo no_site_log",
    "tail -12 /opt/rawlead/data/radar_site.log 2>/dev/null",
    "tail -6 /opt/rawlead/data/radar_legacy.log 2>/dev/null",
    "curl -s http://127.0.0.1:8000/health",
    "curl -s 'http://127.0.0.1:8000/v1/feed?limit=1'",
    "ps aux | grep -E 'main.py|tg_main|neon_legacy|uvicorn' | grep -v grep",
    "curl -s -o /dev/null -w '%{http_code}' https://rawlead.ru/lenta/",
    "curl -s -o /dev/null -w '%{http_code}' https://api.rawlead.ru/health",
    "systemctl is-active nginx",
    "ss -tlnp | grep -E ':80|:443' || true",
    "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/lenta/",
]

if __name__ == "__main__":
    for cmd in CMDS:
        print("===", cmd)
        _, out, err = ssh.run(cmd, check=False)
        sys.stdout.buffer.write((out or err or "").encode("utf-8", errors="replace"))
        if not (out or err or "").endswith("\n"):
            print()
