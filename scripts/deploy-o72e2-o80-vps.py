#!/usr/bin/env python3
"""O72e-2 + O80 backend: tools generic + api feed map · restart API/radar."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_DEPLOY_FILES = (
    "src/ai_analyze.py",
    "src/tools_catalog.py",
    "src/api_server.py",
    "src/match_push.py",
    "scripts/preprod_ai_prod_audit.py",
)


def main() -> int:
    print("=== O72e-2 deploy: tools generic + api map ===")
    remotes: list[str] = []
    for rel in _DEPLOY_FILES:
        local = _ROOT / rel
        if not local.is_file():
            print("SKIP missing", rel)
            continue
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(local, remote)
        remotes.append(remote)
        print("up", rel)
    if remotes:
        ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    print("restart rawlead-api rawlead-radar...")
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-api rawlead-radar",
        check=False,
    )
    print(out or "")
    _, health, _ = ssh.run(
        "curl -sf http://127.0.0.1:8000/health | head -c 500; echo",
        check=False,
    )
    print(health or "")
    _, grep, _ = ssh.run(
        "grep -c normalize_tools_required /opt/rawlead/src/match_push.py; "
        "grep -c normalize_tools_required /opt/rawlead/src/tools_catalog.py",
        check=False,
    )
    print("verify:", (grep or "").strip())
    if "active" in (out or "") and health:
        print("O72e-2 DEPLOY OK")
        return 0
    print("O72e-2 DEPLOY — verify services manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
