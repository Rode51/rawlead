#!/usr/bin/env python3
"""O72e-L2-r8: deploy ai_analyze.py + l3_human_style.py → restart API/radar."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== O72e-L2-r8 deploy: ai_analyze + l3_human_style ===")
    for name in ("ai_analyze.py", "l3_human_style.py"):
        local = _ROOT / "src" / name
        remote = f"/opt/rawlead/src/{name}"
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up src/{name}")

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-api rawlead-radar && "
        "grep -c 'Никогда null' /opt/rawlead/src/ai_analyze.py && "
        "grep -c 'creative/text (#8772' /opt/rawlead/src/l3_human_style.py && "
        "grep -c 'GOOD (#8752 TG есть' /opt/rawlead/src/l3_human_style.py && echo r8_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    ok = text.count("active") >= 2 and "r8_ok" in text
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
