#!/usr/bin/env python3
"""One-shot YouDo fetch smoke on VPS."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

REMOTE = r"""
cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src RADAR_PROFILE=site EXCHANGE_LISTING_BROWSER=1 .venv/bin/python - <<'PY'
from config import load_config
from youdo_parser import fetch_listing_projects

cfg = load_config()
try:
    projects = fetch_listing_projects(cfg, timeout_sec=90.0)
    print("OK count=", len(projects))
    if projects:
        p = projects[0]
        print("sample id=", p.project_id, "title=", p.title[:80])
except Exception as e:
    print("FAIL", type(e).__name__, str(e)[:800])
PY
"""

if __name__ == "__main__":
    _, out, err = ssh.run(REMOTE.strip(), check=False)
    print(out or err)
