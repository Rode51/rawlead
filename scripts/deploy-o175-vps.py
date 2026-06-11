#!/usr/bin/env python3
"""O175: multi-source feed filter + inbox replies + cabinet pagination."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    "src/public_feed.py",
    "src/api_server.py",
)


def main() -> int:
    print("=== O175 deploy: API feed source + inbox + WP theme ===")
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
        "grep -c parse_feed_source_param /opt/rawlead/src/public_feed.py && "
        "grep -c inbox_replies_where_sql /opt/rawlead/src/public_feed.py && "
        "grep -c _feed_where_with_sources /opt/rawlead/src/api_server.py && "
        "grep -c 'state.sources' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js && "
        "grep -c 'limit: 10' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-cabinet.js && "
        "grep -c \"RAWLEAD_CHILD_VERSION', '1.18.54'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php && "
        "echo o175_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text)
    if "o175_deploy_ok" not in text or "active" not in text:
        print("O175 DEPLOY CHECK FAILED")
        return 1
    print("O175 DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
