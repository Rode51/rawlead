#!/usr/bin/env python3
"""O155 external pulse + O156 YouDo humanization."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_RADAR_FILES = (
    "src/healthchecks.py",
    "src/main.py",
    "src/exchange_browser_fetch.py",
    "src/youdo_parser.py",
    "src/exchange_proxy.py",
)


def main() -> int:
    print("=== O155+O156 deploy: pulse + YouDo human ===")
    remotes: list[str] = []
    for rel in _RADAR_FILES:
        p = _ROOT / rel
        if not p.is_file():
            print("skip (not yet)", rel)
            continue
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(p, remote)
        remotes.append(remote)
        print("up", rel)

    if not remotes:
        print("No files to deploy — run after Coder commits O155/O156")
        return 1

    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-radar && "
        "systemctl is-enabled rawlead-ingest-watchdog.timer && "
        "echo o155_o156_radar_ok",
        check=False,
    )
    print(out.strip())
    if "o155_o156_radar_ok" not in (out or "") or "active" not in (out or ""):
        print("RADAR DEPLOY CHECK — verify manually")
        return 1
    print("DEPLOY OK")
    print("Owner: set HEALTHCHECKS_SITE_URL in .env · create check grace 15m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
