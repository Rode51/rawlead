#!/usr/bin/env python3
"""O280: deploy draft quota reset for preprod E2E — api_server.py + match_push.py."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_API_FILES = (
    "src/api_server.py",
    "src/match_push.py",
)


def main() -> int:
    print("=== O280 deploy: draft quota reset for E2E ===")
    remotes: list[str] = []
    for rel in _API_FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-api && "
        "curl -sf http://127.0.0.1:8000/health && echo o280_reset_ok && "
        "grep -c 'draft/quota/reset' /opt/rawlead/src/api_server.py",
        check=False,
    )
    print((out or "").strip())
    ok = "o280_reset_ok" in (out or "") and "active" in (out or "")
    print("OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
