#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh

for n in (300, 500, 1000):
    remote = f"tail -{n} /opt/rawlead/data/radar_site.log | grep -E 'fetch_start|fetch:youdo|fetch_end|ingest done=5'"
    _, out, _ = ssh.run(remote.strip(), check=False)
    text = (out or "").replace("\r\n", "\n").strip()
    print(f"=== tail {n} ===")
    print(text or "(empty)")
    print()
