#!/usr/bin/env python3
"""O179: YouDo radar wall sync + traffic guard + retry goto commit."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    "src/main.py",
    "src/youdo_parser.py",
    "src/exchange_browser_fetch.py",
)


def main() -> int:
    print("=== O179 deploy: YouDo wall sync + traffic guard ===")
    remotes: list[str] = []
    for rel in _UPLOADS:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "grep -c youdo_source_fetch_wall_sec /opt/rawlead/src/youdo_parser.py && "
        "grep -c _youdo_traffic_guard /opt/rawlead/src/youdo_parser.py && "
        "grep -c _youdo_goto_wait_until_for_attempt /opt/rawlead/src/exchange_browser_fetch.py && "
        "systemctl restart rawlead-radar && sleep 4 && systemctl is-active rawlead-radar && "
        "echo o179_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text)
    if "o179_deploy_ok" not in text or "active" not in text:
        print("O179 DEPLOY CHECK FAILED")
        return 1
    print("O179 DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
