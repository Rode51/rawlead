#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh

cmd = (
    "awk '/2026-06-19 02:1[5-9]|2026-06-19 02:2[0-9]/' /opt/rawlead/data/radar_site.log "
    "| grep -iE 'fetch:youdo|sticky_goto|html_len=17|outcome=|ingest done|profile_wiped|hard_reset|cooldown|cycle_decision'"
)
_, out, err = ssh.run(cmd, check=False)
text = (out or err or "(empty)").strip()
print(text[-8000:] if len(text) > 8000 else text)
