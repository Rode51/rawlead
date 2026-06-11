#!/usr/bin/env python3
"""O182: YouDo in-progress / SBR delist markers."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    "src/youdo_parser.py",
    "scripts/run-delist-backfill.py",
)


def main() -> int:
    print("=== O182 deploy: YouDo in-progress / SBR delist ===")
    remotes: list[str] = []
    for rel in _UPLOADS:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "grep -c 'зарезервировано' /opt/rawlead/src/youdo_parser.py && "
        "grep -c 'isInProcess' /opt/rawlead/src/youdo_parser.py && "
        "systemctl restart rawlead-radar && sleep 4 && systemctl is-active rawlead-radar && "
        "echo o182_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text)
    if "o182_deploy_ok" not in text or "active" not in text:
        print("O182 DEPLOY CHECK FAILED")
        return 1
    print("O182 DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
