#!/usr/bin/env python3
"""O72e-L2-r3: deploy l3_human_style.py → restart rawlead-api."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== O72e-L2-r3 deploy: l3_human_style.py ===")
    local = _ROOT / "src" / "l3_human_style.py"
    remote = "/opt/rawlead/src/l3_human_style.py"
    ssh.upload(local, remote)
    ssh.run(f"chown rawlead:rawlead {remote}")
    print("up src/l3_human_style.py")

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "grep -c 'Глубина без простыни' /opt/rawlead/src/l3_human_style.py && echo r3_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    ok = "active" in text and "r3_ok" in text
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
