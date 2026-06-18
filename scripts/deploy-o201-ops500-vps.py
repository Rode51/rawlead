#!/usr/bin/env python3
"""O201-OPS-500: fix /ops/funnel + /ops/dashboard HTTP 500 — API only."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.site", override=False)

_API_FILES = (
    "src/owner_admin.py",
    "src/ops_funnel.py",
    "src/api_server.py",
)


def _upload_api() -> list[str]:
    remotes: list[str] = []
    for rel in _API_FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    return remotes


def main() -> int:
    print("=== O201 ops500 fix deploy (API) ===")
    api_remotes = _upload_api()
    ssh.run("chown rawlead:rawlead " + " ".join(api_remotes))

    _, out_api, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-api && "
        "grep -c 'load_config' /opt/rawlead/src/ops_funnel.py && "
        "grep -c '_safe_ops_funnel' /opt/rawlead/src/owner_admin.py && "
        "grep -c 'ops_dashboard_json' /opt/rawlead/src/api_server.py && "
        "echo o201_ops500_api_ok",
        check=False,
    )
    print(out_api.strip())
    if "o201_ops500_api_ok" not in (out_api or "") or "active" not in (out_api or ""):
        print("API deploy verify failed")
        return 1
    print("OK — owner smoke: /ops/ login → funnel + dashboard без HTTP 500")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
