#!/usr/bin/env python3
"""O135-DRAFT: L2-only first user · draft_async restart · OpenRouter proxy."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_API_FILES = (
    "src/api_server.py",
    "src/match_push.py",
    "src/ai_analyze.py",
    "src/config.py",
    "src/draft_async.py",
)


def main() -> int:
    print("=== O135 deploy: draft timeout + OR proxy ===")
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
        "grep -c first_user_l2_only /opt/rawlead/src/match_push.py && "
        "grep -c draft:restart /opt/rawlead/src/draft_async.py && "
        "grep -c openrouter_proxy_hint /opt/rawlead/src/config.py && "
        "journalctl -u rawlead-api -n 40 --no-pager | "
        "grep -E 'openrouter:proxy=|first_user_l2_only|draft:restart' | tail -3 && "
        "echo o135_api_ok",
        check=False,
    )
    print(out.strip())
    if "o135_api_ok" not in (out or ""):
        print("API DEPLOY CHECK — verify manually")
        return 1
    print("DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
