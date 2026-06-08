#!/usr/bin/env python3
"""O136: draft pipeline stage timing logs (grep draft:trace)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_API_FILES = (
    "src/draft_trace.py",
    "src/api_server.py",
    "src/match_push.py",
    "src/ai_analyze.py",
    "src/draft_async.py",
)


def main() -> int:
    print("=== O136 deploy: draft trace logs ===")
    remotes: list[str] = []
    for rel in _API_FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)

    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "grep -c log_draft_stage /opt/rawlead/src/draft_trace.py && "
        "echo o136_api_ok",
        check=False,
    )
    print(out.strip())
    if "o136_api_ok" not in (out or ""):
        print("API DEPLOY CHECK — verify manually")
        return 1
    print("DEPLOY OK — smoke draft then: journalctl -u rawlead-api | grep -E 'draft:trace|L2 skip|l2_http'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
