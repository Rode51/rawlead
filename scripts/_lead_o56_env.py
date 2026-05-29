#!/usr/bin/env python3
"""Set OPENROUTER_MODEL_SHARED_DRAFT on VPS + restart API."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

KEY = "OPENROUTER_MODEL_SHARED_DRAFT"
VAL = "google/gemini-2.5-pro"

CMD = (
    f"grep -q '^{KEY}=' /opt/rawlead/.env.site && "
    f"sed -i 's/^{KEY}=.*/{KEY}={VAL}/' /opt/rawlead/.env.site || "
    f"echo '{KEY}={VAL}' >> /opt/rawlead/.env.site && "
    f"grep '^{KEY}=' /opt/rawlead/.env.site && "
    "systemctl restart rawlead-api && sleep 2 && systemctl is-active rawlead-api"
)

if __name__ == "__main__":
    _, out, _ = ssh.run(CMD, check=False)
    print((out or "").strip())
