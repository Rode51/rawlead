#!/usr/bin/env python3
"""O72e-L2-r9: deploy l3_human_style.py (+ ai_analyze.py) → restart API/radar."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== O72e-L2-r9 deploy: l3_human_style + ai_analyze ===")
    for name in ("l3_human_style.py", "ai_analyze.py"):
        local = _ROOT / "src" / name
        remote = f"/opt/rawlead/src/{name}"
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up src/{name}")

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-api rawlead-radar && "
        "grep -c 'Структура send-ready' /opt/rawlead/src/l3_human_style.py && "
        "grep -c 'tools_required — сверка' /opt/rawlead/src/l3_human_style.py && "
        "grep -c 'GOOD (#12148)' /opt/rawlead/src/l3_human_style.py && echo r9_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    ok = text.count("active") >= 2 and "r9_ok" in text
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
