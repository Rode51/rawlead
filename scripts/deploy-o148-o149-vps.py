#!/usr/bin/env python3
"""O148-O149: warm API + draft limits + theme 1.18.45."""
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
    "src/draft_async.py",
    "src/draft_limits.py",
)


def deploy_api() -> int:
    print("=== O148 API deploy ===")
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
        "grep -c warm_shared_lead_draft /opt/rawlead/src/match_push.py && "
        "grep -c submit_warm /opt/rawlead/src/draft_async.py && "
        "grep -c 'draft/warm' /opt/rawlead/src/api_server.py && "
        "echo o148_api_ok",
        check=False,
    )
    print(out.strip())
    if "o148_api_ok" not in (out or "") or "active" not in (out or ""):
        print("API DEPLOY FAIL")
        return 1
    print("API DEPLOY OK")
    return 0


def deploy_theme() -> int:
    print("=== O149 theme deploy ===")
    rc = subprocess.call(
        [sys.executable, str(_ROOT / "scripts" / "deploy-wp-theme-vps.py")],
    )
    if rc != 0:
        return rc
    _, out, _ = ssh.run(
        "grep -m1 '^Version:' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/style.css && "
        "grep -c maybeWarmDraftOnExpand "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js && "
        "grep -c 'rl-feed-card__flip' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js || true && "
        "echo o149_theme_ok",
        check=False,
    )
    print(out.strip())
    if "o149_theme_ok" not in (out or "") or "1.18.45" not in (out or ""):
        print("THEME DEPLOY CHECK — verify manually")
        return 1
    print("THEME DEPLOY OK")
    return 0


def main() -> int:
    if deploy_api() != 0:
        return 1
    if deploy_theme() != 0:
        return 1
    print("=== O148+O149 DEPLOY OK ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
