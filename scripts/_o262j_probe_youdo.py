#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh

remote = """
tail -8000 /opt/rawlead/data/radar_site.log | grep -E 'fetch_start|fetch:youdo|fetch_end|youdo:ingest|YouDo ' | tail -25
"""
_, out, _ = ssh.run(remote.strip(), check=False)
print((out or "").replace("\r\n", "\n"))
