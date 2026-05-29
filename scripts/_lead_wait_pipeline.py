#!/usr/bin/env python3
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh

time.sleep(150)
_, o, _ = ssh.run(
    "grep pipeline:L1 /opt/rawlead/data/radar_site.log | tail -5; "
    "echo '---'; tail -12 /opt/rawlead/data/radar_site.log",
    check=False,
)
sys.stdout.buffer.write((o or "(empty)").encode("utf-8", errors="replace"))
