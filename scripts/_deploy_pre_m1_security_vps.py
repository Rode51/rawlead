#!/usr/bin/env python3
"""Pre-M1 security hotfix: require Bearer on /v1/me/* + RADAR_CORS_ORIGINS."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_CORS = "https://rawlead.ru,https://www.rawlead.ru"
_KEY = "RADAR_CORS_ORIGINS"


def main() -> int:
    remote = "/opt/rawlead/src/api_server.py"
    ssh.upload(_ROOT / "src/api_server.py", remote)
    print("up src/api_server.py")
    ssh.run(f"chown rawlead:rawlead {remote}")

    _, out, _ = ssh.run(
        f"grep -q '^{_KEY}=' /opt/rawlead/.env.site && "
        f"sed -i 's|^{_KEY}=.*|{_KEY}={_CORS}|' /opt/rawlead/.env.site || "
        f"echo '{_KEY}={_CORS}' >> /opt/rawlead/.env.site; "
        f"grep '^{_KEY}=' /opt/rawlead/.env.site | tail -1; "
        "systemctl restart rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-api && "
        "echo pre_m1_security_ok",
        check=False,
    )
    text = (out or "").strip()
    print(text)
    return 0 if "pre_m1_security_ok" in text else 1


if __name__ == "__main__":
    raise SystemExit(main())
