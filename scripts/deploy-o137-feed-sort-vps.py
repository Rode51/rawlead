#!/usr/bin/env python3
"""O137: feed sort/pagination — time=SQL offset, match=wide scan."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== O137 deploy: feed sort/pagination fix ===")
    remote = "/opt/rawlead/src/api_server.py"
    ssh.upload(_ROOT / "src/api_server.py", remote)
    ssh.run("chown rawlead:rawlead " + remote)
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && systemctl is-active rawlead-api && "
        "grep -c 'LIMIT %s OFFSET %s' /opt/rawlead/src/api_server.py && echo o137_ok",
        check=False,
    )
    print((out or "").strip())
    if "o137_ok" not in (out or ""):
        return 1
    print("DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
