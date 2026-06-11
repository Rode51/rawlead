#!/usr/bin/env python3
"""O176: structured youdo:trace logging in radar_site.log."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    "src/youdo_parser.py",
    "src/exchange_browser_fetch.py",
    "src/exchange_health.py",
    "src/main.py",
)


def main() -> int:
    print("=== O176 deploy: youdo:trace ===")
    remotes: list[str] = []
    for rel in _UPLOADS:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "grep -c 'youdo:trace stage=' /opt/rawlead/src/youdo_parser.py && "
        "grep -c _log_youdo_browser_trace /opt/rawlead/src/exchange_browser_fetch.py && "
        "grep -c parse_empty /opt/rawlead/src/exchange_health.py && "
        "grep -c log_youdo_fetch_end /opt/rawlead/src/main.py && "
        "systemctl restart rawlead-radar && sleep 4 && systemctl is-active rawlead-radar && "
        "echo o176_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text)
    if "o176_deploy_ok" not in text or "active" not in text:
        print("O176 DEPLOY CHECK FAILED")
        return 1
    print("O176 DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
