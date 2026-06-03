#!/usr/bin/env python3
"""O104: exchange health — radar + API /ops/ + watchdog."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_SRC = (
    "exchange_health.py",
    "main.py",
    "radar_status.py",
    "owner_admin.py",
    "api_server.py",
    "health_check.py",
)

_SCRIPTS = ("ingest_watchdog.py",)


def main() -> int:
    print("=== O104 deploy (health + /ops/ + FLPARSING alerts) ===")
    remote_src = "/opt/rawlead/src"
    for name in _SRC:
        local = _ROOT / "src" / name
        remote = f"{remote_src}/{name}"
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up src/{name}")

    remote_scripts = "/opt/rawlead/scripts"
    for name in _SCRIPTS:
        local = _ROOT / "scripts" / name
        remote = f"{remote_scripts}/{name}"
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up scripts/{name}")

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-api rawlead-radar && "
        "test -f /opt/rawlead/src/exchange_health.py && echo o104_ok",
        check=False,
    )
    print((out or "").strip())
    text = out or ""
    ok = text.count("active") >= 2 and "o104_ok" in text
    print("DEPLOY OK" if ok else "DEPLOY CHECK — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
