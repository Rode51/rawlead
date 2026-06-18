#!/usr/bin/env python3
"""O206-t3b: acc1 handler deaf — watchdog + membership probe on VPS."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "src/tg_monitor.py",
    "scripts/probe_tg_test_group_membership.py",
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
    print("=== O206-t3b deploy: acc1 handler watchdog ===")
    remotes = _upload(_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 10 && "
        "systemctl is-active rawlead-radar && "
        "grep -c handler_ok /opt/rawlead/src/tg_monitor.py && "
        "grep -c test_group /opt/rawlead/src/tg_monitor.py && "
        "grep -E 'handler_ok|test_group|acc1: ready' "
        "/opt/rawlead/data/radar_site.log | tail -12 && "
        "echo t3b_ok",
        check=False,
    )
    print(out.strip())
    ok = "t3b_ok" in (out or "") and "active" in (out or "")
    if ok:
        print("DEPLOY OK — owner: post in test group, grep acc1")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
