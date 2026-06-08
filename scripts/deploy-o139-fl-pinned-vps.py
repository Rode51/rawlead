#!/usr/bin/env python3
"""O139-FL-PINNED-FRESH: skip known FL pins, filter unseen listing."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_RADAR_FILES = (
    "src/listing_fresh.py",
    "src/fl_parser.py",
)


def _upload(files: tuple[str, ...]) -> list[str]:
    remotes: list[str] = []
    for rel in files:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    return remotes


def main() -> int:
    print("=== O139 deploy: FL pinned fresh filter ===")
    radar_remotes = _upload(_RADAR_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(radar_remotes))

    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-radar && "
        "grep -c skipped_known /opt/rawlead/src/listing_fresh.py && "
        "grep -c 'pinned known do not stop' /opt/rawlead/src/fl_parser.py && "
        "echo o139_radar_ok",
        check=False,
    )
    print(out.strip())
    if "o139_radar_ok" not in (out or "") or "active" not in (out or ""):
        print("RADAR DEPLOY CHECK — verify manually")
        return 1
    print("RADAR DEPLOY OK")
    print("DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
