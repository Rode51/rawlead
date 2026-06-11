#!/usr/bin/env python3
"""O182b: fetch_youdo_detail_html import hotfix."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_REMOTE = "/opt/rawlead/src/youdo_parser.py"


def main() -> int:
    print("=== O182b deploy: fetch_youdo_detail_html import ===")
    ssh.upload(_ROOT / "src/youdo_parser.py", _REMOTE)
    print("up src/youdo_parser.py")
    ssh.run(f"chown rawlead:rawlead {_REMOTE}")
    _, out, _ = ssh.run(
        "grep -c fetch_youdo_detail_html /opt/rawlead/src/youdo_parser.py && "
        "systemctl restart rawlead-radar && sleep 4 && systemctl is-active rawlead-radar && "
        "echo o182b_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text)
    if "o182b_deploy_ok" not in text or "active" not in text:
        print("O182b DEPLOY CHECK FAILED")
        return 1
    print("O182b DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
