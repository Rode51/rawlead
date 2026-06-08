#!/usr/bin/env python3
"""O155 pulse + O156 YouDo human + O157 traffic savings."""
from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_RADAR_FILES = (
    "src/healthchecks.py",
    "src/main.py",
    "src/lead_pipeline.py",
    "src/exchange_browser_fetch.py",
    "src/youdo_parser.py",
    "src/exchange_proxy.py",
)

HC_URL = "https://hc-ping.com/fb08c75e-4f32-479d-985a-b8cc46cd40de"
_ENV_PATH = "/opt/rawlead/.env"


def _patch_healthchecks_env() -> None:
    _, out, _ = ssh.run(f"grep -n HEALTHCHECKS_SITE_URL {_ENV_PATH} 2>/dev/null || true", check=False)
    line = (out or "").strip()
    if line:
        ssh.run(
            f"sed -i 's|^HEALTHCHECKS_SITE_URL=.*|HEALTHCHECKS_SITE_URL={HC_URL}|' {_ENV_PATH}",
            check=False,
        )
        print("env: updated HEALTHCHECKS_SITE_URL")
    else:
        ssh.run(
            f"grep -q '^HEALTHCHECKS_SITE_URL=' {_ENV_PATH} 2>/dev/null || "
            f"echo 'HEALTHCHECKS_SITE_URL={HC_URL}' >> {_ENV_PATH}",
            check=False,
        )
        print("env: appended HEALTHCHECKS_SITE_URL")


def main() -> int:
    print("=== O155+O156+O157 deploy ===")
    remotes: list[str] = []
    for rel in _RADAR_FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)

    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _patch_healthchecks_env()

    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-radar && "
        "grep -c ping_after_site_cycle /opt/rawlead/src/main.py && "
        "grep -c YOUDO_DETAIL_MIN_CHARS /opt/rawlead/src/lead_pipeline.py && "
        "grep -c _abort_youdo_lean_route /opt/rawlead/src/exchange_browser_fetch.py && "
        "grep HEALTHCHECKS_SITE_URL /opt/rawlead/.env | tail -1 && "
        "echo o155_o157_ok",
        check=False,
    )
    print(out.strip())
    if "o155_o157_ok" not in (out or "") or "active" not in (out or ""):
        print("RADAR DEPLOY CHECK — verify manually")
        return 1
    print("DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
