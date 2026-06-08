#!/usr/bin/env python3
"""Hotfix O157: YouDo xhr allow + HC UA — deploy to VPS."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "src/exchange_browser_fetch.py",
    "src/healthchecks.py",
)

CLEAR = (
    "cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src "
    ".venv/bin/python - <<'PY'\n"
    "from config import load_config\n"
    "from storage import ProjectStorage\n"
    "st = ProjectStorage(load_config().sqlite_path)\n"
    "st.set_setting('youdo_cooldown_until', '0')\n"
    "st.set_setting('youdo_fetch_cycle_n', '0')\n"
    "print('youdo_gates_reset')\n"
    "PY\n"
)


def main() -> int:
    remotes = []
    for rel in _FILES:
        remote = f"/opt/rawlead/{rel.replace(chr(92), '/')}"
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(CLEAR, check=False)
    print(out or "")
    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 3 && systemctl is-active rawlead-radar && "
        "grep -c 'youdo.com.*xhr' /opt/rawlead/src/exchange_browser_fetch.py && "
        "echo hotfix_ok",
        check=False,
    )
    print(out or "")
    return 0 if "hotfix_ok" in (out or "") and "active" in (out or "") else 1


if __name__ == "__main__":
    raise SystemExit(main())
