#!/usr/bin/env python3
"""O247b: deploy draft quota API — api_server.py + match_push.py."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_API_FILES = (
    "src/api_server.py",
    "src/match_push.py",
    "src/draft_limits.py",
)


def main() -> int:
    print("=== O247b deploy: draft quota API ===")
    remotes: list[str] = []
    for rel in _API_FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "if grep -q '^DRAFT_HOURLY_LIMIT=' /opt/rawlead/.env.site 2>/dev/null; then "
        "sed -i 's/^DRAFT_HOURLY_LIMIT=.*/DRAFT_HOURLY_LIMIT=10/' /opt/rawlead/.env.site; "
        "else echo 'DRAFT_HOURLY_LIMIT=10' >> /opt/rawlead/.env.site; fi && "
        "grep '^DRAFT_HOURLY_LIMIT=' /opt/rawlead/.env.site && "
        "systemctl restart rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-api && "
        "curl -sf http://127.0.0.1:8000/health && echo o247b_ok && "
        "grep -c 'me/draft/quota' /opt/rawlead/src/api_server.py",
        check=False,
    )
    print((out or "").strip())
    ok = "o247b_ok" in (out or "") and "active" in (out or "")
    print("OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
