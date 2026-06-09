#!/usr/bin/env python3
"""O160 deploy: per-source locks, wall-clock ingest, cycle watchdog, systemd notify."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_RADAR_SRC = (
    "exchange_browser_fetch.py",
    "fl_parser.py",
    "youdo_parser.py",
    "main.py",
    "healthchecks.py",
)

_SYSTEMD = "deploy/systemd/rawlead-radar.service"


def main() -> int:
    print("=== O160 deploy: radar ingest stability ===")
    remotes: list[str] = []
    for name in _RADAR_SRC:
        local = _ROOT / "src" / name
        remote = f"/opt/rawlead/src/{name}"
        ssh.upload(local, remote)
        remotes.append(remote)
        print(f"up src/{name}")

    unit_local = _ROOT / _SYSTEMD
    unit_remote = "/etc/systemd/system/rawlead-radar.service"
    ssh.upload(unit_local, unit_remote)
    print(f"up {_SYSTEMD}")

    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    ssh.run("systemctl daemon-reload")

    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-radar && "
        "grep -c WatchdogSec=660 /etc/systemd/system/rawlead-radar.service && "
        "grep -c _fetch_lock /opt/rawlead/src/exchange_browser_fetch.py && "
        "grep -c ping_cycle_overrun /opt/rawlead/src/healthchecks.py && "
        "echo o160_radar_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    ok = "active" in text and "o160_radar_ok" in text
    if ok:
        print("DEPLOY OK")
        print("Owner: tail radar log — ── Цикл ── every ~2-5 min · HC fail URL on overrun")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
