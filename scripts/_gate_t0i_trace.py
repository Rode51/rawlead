#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deploy_vps_ssh as ssh  # noqa: E402

_, out, _ = ssh.run(
    "grep 'youdo:trace' /opt/rawlead/data/radar_site.log | tail -20; "
    "echo ===; "
    "grep -E 'fetch_start|fetch_end|subprocess|youdo_fetch' /opt/rawlead/data/radar_site.log | tail -15",
    check=False,
)
print((out or "").encode("ascii", errors="replace").decode("ascii"))
