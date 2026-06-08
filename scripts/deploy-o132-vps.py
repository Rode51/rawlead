#!/usr/bin/env python3
"""O132-STABILITY: radar MemoryMax + browser serialize + orphan chrome cleanup."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_SRC_FILES = (
    "src/exchange_browser_fetch.py",
    "src/main.py",
)
_SYSTEMD = "deploy/systemd/rawlead-radar.service"


def main() -> int:
    print("=== O132 deploy: radar stability (MemoryMax + browser cleanup) ===")
    remotes: list[str] = []
    for rel in _SRC_FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)

    unit_local = _ROOT / _SYSTEMD
    unit_remote = "/opt/rawlead/" + _SYSTEMD.replace("\\", "/")
    ssh.upload(unit_local, unit_remote)
    print("up", _SYSTEMD)

    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    _, out, _ = ssh.run(
        "cp /opt/rawlead/deploy/systemd/rawlead-radar.service /etc/systemd/system/ && "
        "systemctl daemon-reload && "
        "systemctl restart rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-radar && "
        "grep -c MemoryMax=1400M /etc/systemd/system/rawlead-radar.service && "
        "grep -c cleanup_stale_browser_processes /opt/rawlead/src/exchange_browser_fetch.py && "
        "grep -c close_all_browser_contexts /opt/rawlead/src/main.py && "
        "free -h && "
        "echo o132_ok",
        check=False,
    )
    print(out.strip())
    if "o132_ok" not in (out or "") or "active" not in (out or ""):
        print("DEPLOY CHECK — verify manually")
        return 1
    print("DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
