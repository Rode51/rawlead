#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh

for c in [
    "journalctl -u rawlead-api --no-pager -n 200",
    "grep -E 'lenta:draft:7019|7051|AiAnalyze|ai_fail' /opt/rawlead/data/radar_site.log 2>/dev/null | tail -20",
]:
    print("===", c[:70])
    _, o, _ = ssh.run(c, check=False)
    text = o or ""
    for line in text.splitlines():
        if any(k in line for k in ("7019", "7051", "draft", "AiAnalyze", "ai_fail", "503", "ERROR", "reply_draft")):
            print(line)
