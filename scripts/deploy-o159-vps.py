#!/usr/bin/env python3
"""O159-DRAFT-BURST: OR L2 slot sem · draft queue_ahead/queued · feed «В очереди…»."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_API_FILES = (
    "src/ai_analyze.py",
    "src/draft_async.py",
)


def deploy_api() -> int:
    print("=== O159 API deploy ===")
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
        "grep -c draft_or_concurrency /opt/rawlead/src/ai_analyze.py && "
        "grep -c _draft_queue_ahead /opt/rawlead/src/draft_async.py && "
        "echo o159_api_ok",
        check=False,
    )
    print(out.strip())
    if "o159_api_ok" not in (out or "") or "active" not in (out or ""):
        print("API DEPLOY FAIL")
        return 1
    print("API DEPLOY OK")
    return 0


def deploy_theme() -> int:
    print("=== O159 theme deploy ===")
    return subprocess.call(
        [sys.executable, str(_ROOT / "scripts" / "deploy-wp-theme-vps.py")],
    )


def main() -> int:
    if deploy_api() != 0:
        return 1
    if deploy_theme() != 0:
        return 1
    _, ver, _ = ssh.run(
        "grep -c 'DRAFT_BTN_QUEUE_RU' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js",
        check=False,
    )
    print("DRAFT_BTN_QUEUE_RU:", ver.strip())
    print("=== O159 DEPLOY OK ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
