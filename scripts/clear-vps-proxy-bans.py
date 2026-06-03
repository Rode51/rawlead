#!/usr/bin/env python3
"""Сбросить exchange_proxy_bans_v1/v2 на VPS (после тестов / ложных банов)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

CMD = (
    "cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src "
    ".venv/bin/python - <<'PY'\n"
    "from config import load_config\n"
    "from storage import ProjectStorage\n"
    "c = load_config()\n"
    "st = ProjectStorage(c.sqlite_path)\n"
    "st.set_setting('exchange_proxy_bans_v1', '{}')\n"
    "st.set_setting('exchange_proxy_bans_v2', '{}')\n"
    "print('bans_cleared')\n"
    "PY\n"
    "systemctl restart rawlead-radar && sleep 2 && systemctl is-active rawlead-radar"
)

if __name__ == "__main__":
    _, out, err = ssh.run(CMD, check=False)
    print(out or err)
