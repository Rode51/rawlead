#!/usr/bin/env python3
"""O178: feed source/sort SQL param fix + sticky error banner."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    "src/api_server.py",
    "src/public_feed.py",
)


def main() -> int:
    print("=== O178 deploy: feed source/sort + banner ===")
    remotes: list[str] = []
    for rel in _UPLOADS:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    if subprocess.call([sys.executable, str(_ROOT / "scripts" / "deploy-wp-theme-vps.py")]) != 0:
        return 1

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-api && "
        "grep -c 'hideFeedBanner' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js && "
        "grep \"RAWLEAD_CHILD_VERSION', '1.18.56'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php && "
        "echo o178_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text)
    if "o178_deploy_ok" not in text or "active" not in text:
        print("O178 DEPLOY CHECK FAILED")
        return 1
    print("O178 DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
