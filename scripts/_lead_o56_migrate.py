#!/usr/bin/env python3
"""Run lead_draft_jobs migration on VPS."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

REMOTE = r"""cd /opt/rawlead && /opt/rawlead/.venv/bin/python << 'PY'
import sys
sys.path.insert(0, "src")
from config import load_config, load_radar_env, apply_profile_argv
from draft_async import _ensure_draft_tables
apply_profile_argv()
load_radar_env()
c = load_config()
_ensure_draft_tables(c.database_url)
print("draft_jobs OK")
PY"""

if __name__ == "__main__":
    _, out, err = ssh.run(REMOTE, check=False)
    text = (out or err or "").strip()
    print(text)
    sys.exit(0 if "draft_jobs OK" in text or "OK" in text else 1)
