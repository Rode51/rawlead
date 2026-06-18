#!/usr/bin/env python3
"""O250b: deploy match_push compatibility_match parity — API + radar restart."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_REMOTE = "/opt/rawlead/src/match_push.py"


def main() -> int:
    print("=== O250b deploy: push km = feed km (compatibility_match) ===")
    ssh.upload(_ROOT / "src/match_push.py", _REMOTE)
    print("up src/match_push.py")
    ssh.run(f"chown rawlead:rawlead {_REMOTE}")
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "curl -sf http://127.0.0.1:8000/health && echo api_ok && "
        "systemctl restart rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-radar && echo radar_ok && "
        "grep -c '_push_km_for_lead_row' /opt/rawlead/src/match_push.py",
        check=False,
    )
    print((out or "").strip())
    ok = "api_ok" in (out or "") and "radar_ok" in (out or "") and "active" in (out or "")
    print("OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
