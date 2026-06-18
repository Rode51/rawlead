#!/usr/bin/env python3
"""O230: remove max-12 skills cap — API only."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_API_FILES = (
    "src/api_server.py",
    "src/skills_catalog.py",
)


def main() -> int:
    print("=== O230 deploy: remove skills cap (API) ===")
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
        "curl -sf http://127.0.0.1:8000/health && echo o230_ok",
        check=False,
    )
    print((out or "").strip())
    ok = "o230_ok" in (out or "") and "active" in (out or "")
    print("OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
