#!/usr/bin/env python3
"""O214: ops panel truth — cycle_age log fallback + FL residential badge (API only)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_API_FILES = (
    "src/ops_funnel.py",
    "src/exchange_proxy.py",
    "src/owner_admin.py",
    "src/static/ops-pult.js",
)


def _upload(files: tuple[str, ...]) -> list[str]:
    remotes: list[str] = []
    for rel in files:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    return remotes


def main() -> int:
    print("=== O214 deploy: ops truth cycle_age + residential (API) ===")
    ssh.run("mkdir -p /opt/rawlead/src/static && chown rawlead:rawlead /opt/rawlead/src/static")
    remotes = _upload(_API_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-api && "
        "grep -c '_cycle_ts_from_log' /opt/rawlead/src/ops_funnel.py && "
        "grep -c 'residential_active' /opt/rawlead/src/exchange_proxy.py && "
        "curl -sf -o /dev/null -w 'ops_root=%{http_code}\\n' "
        "http://127.0.0.1:8000/ops/ && "
        "echo o214_api_ok",
        check=False,
    )
    print(out.strip())
    ok = "o214_api_ok" in (out or "") and "active" in (out or "") and "ops_root=200" in (out or "")
    if ok:
        print("DEPLOY OK — hard refresh /ops/ for cycle_age + residential badge")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
