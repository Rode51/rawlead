#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh

remote = """
grep YOUDO_O191_DC_SLOTS /opt/rawlead/.env.site | tail -1
grep YOUDO_DC_PROXY_URLS /opt/rawlead/.env.site || echo YOUDO_DC_PROXY_URLS=unset
tail -5000 /opt/rawlead/data/radar_site.log | grep fetch:youdo | tail -5
tail -5000 /opt/rawlead/data/radar_site.log | grep youdo:trace | tail -5
tail -5000 /opt/rawlead/data/radar_site.log | grep youdo:ingest | tail -5
tail -5000 /opt/rawlead/data/radar_site.log | grep 'YouDo ' | tail -3
systemctl is-active rawlead-radar
"""
_, out, _ = ssh.run(remote.strip(), check=False)
text = (out or "").replace("\r\n", "\n")
print(text)
print("---")
print("tier=ru:", "tier=ru" in text)
print("ingest50:", "youdo:ingest done=50" in text)
