#!/usr/bin/env python3
"""O158: match push dedup · feed match bar · get_lead keyword_match · theme 1.18.49."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_API_FILES = (
    "src/api_server.py",
    "src/match_push.py",
)


def deploy_api() -> int:
    print("=== O158 API deploy ===")
    remotes: list[str] = []
    for rel in _API_FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 4 && "
        "systemctl is-active rawlead-api && systemctl is-active rawlead-radar && "
        "grep -c _user_already_pushed_for_order /opt/rawlead/src/match_push.py && "
        "grep -c 'keyword_match для deep link' /opt/rawlead/src/api_server.py && "
        "echo o158_api_ok",
        check=False,
    )
    print(out.strip())
    if "o158_api_ok" not in (out or "") or "active" not in (out or ""):
        print("API DEPLOY FAIL")
        return 1
    print("API+RADAR DEPLOY OK")
    return 0


def deploy_theme() -> int:
    print("=== O158 theme deploy ===")
    return subprocess.call(
        [sys.executable, str(_ROOT / "scripts" / "deploy-wp-theme-vps.py")],
    )


def main() -> int:
    if deploy_api() != 0:
        return 1
    if deploy_theme() != 0:
        return 1
    _, ver, _ = ssh.run(
        "grep -c syncMatchFillsInViewport "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js",
        check=False,
    )
    print("syncMatchFillsInViewport:", ver.strip())
    print("=== O158 DEPLOY OK ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
