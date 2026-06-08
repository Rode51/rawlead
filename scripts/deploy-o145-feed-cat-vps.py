#!/usr/bin/env python3
"""O145-FEED-CAT: personal feed category + sort=time wide scan."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== O145 deploy: personal feed category + time scan ===")
    remote = "/opt/rawlead/src/api_server.py"
    ssh.upload(_ROOT / "src/api_server.py", remote)
    ssh.run("chown rawlead:rawlead " + remote)
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && systemctl is-active rawlead-api && "
        "grep -c '_personal_feed_page' /opt/rawlead/src/api_server.py && echo o145_ok",
        check=False,
    )
    print((out or "").strip())
    if "o145_ok" not in (out or ""):
        return 1
    print("DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
