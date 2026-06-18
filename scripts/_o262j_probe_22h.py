#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh

remote = """
tail -15000 /opt/rawlead/data/radar_site.log | grep '2026-06-17 22:' | grep -E 'fetch_start|fetch:youdo|fetch_end|tier=ru|ingest done' | tail -30
"""
_, out, _ = ssh.run(remote.strip(), check=False)
print((out or "").replace("\r\n", "\n"))
