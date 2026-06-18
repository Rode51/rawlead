#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deploy_vps_ssh as ssh  # noqa: E402

_, out, _ = ssh.run(
    "grep -c youdo_fetch_worker /opt/rawlead/src/exchange_browser_fetch.py; "
    "echo ---; "
    "grep fetch_end /opt/rawlead/data/radar_site.log | tail -5; "
    "echo ---; "
    "grep -i asyncio /opt/rawlead/data/radar_site.log | tail -3",
    check=False,
)
print((out or "").encode("ascii", errors="replace").decode("ascii"))
