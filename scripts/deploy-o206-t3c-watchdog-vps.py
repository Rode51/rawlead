#!/usr/bin/env python3
"""O206-t3c: watchdog sync is_connected + per-acc reconnect (no mass disconnect)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = ("src/tg_monitor.py",)


def _upload(files: tuple[str, ...]) -> list[str]:
    remotes: list[str] = []
    for rel in files:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    return remotes


def main() -> int:
    print("=== O206-t3c deploy: watchdog zombie fix ===")
    remotes = _upload(_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 10 && "
        "systemctl is-active rawlead-radar && "
        "grep -c _reconnect_session /opt/rawlead/src/tg_monitor.py && "
        "grep -c _force_reconnect_all /opt/rawlead/src/tg_monitor.py || true && "
        "grep -E 'handler_ok|пульс|sync ok' "
        "/opt/rawlead/data/radar_site.log | tail -15 && "
        "echo t3c_ok",
        check=False,
    )
    print(out.strip())
    ok = "t3c_ok" in (out or "") and "active" in (out or "")
    if ok:
        print("DEPLOY OK — owner: wait 3 min, grep пульс connected=1, post test group")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
