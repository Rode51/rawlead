#!/usr/bin/env python3
"""O95-fix-4: me/feed empty profile + WP sort lock 1.16.4."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== O95-fix-4 deploy (1.16.4 + API) ===")
    api_local = _ROOT / "src" / "api_server.py"
    api_remote = "/opt/rawlead/src/api_server.py"
    ssh.upload(api_local, api_remote)
    ssh.run("chown rawlead:rawlead " + api_remote)
    print("up src/api_server.py")

    n = ssh.sync_project(
        local_root=_THEME,
        remote_root="/opt/rawlead/wordpress/rawlead-kadence-child",
    )
    print(f"WP uploaded {n} files")
    ssh.run(
        "rsync -a /opt/rawlead/wordpress/rawlead-kadence-child/ "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/ && "
        "chown -R www-data:www-data /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child"
    )
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "grep -c has_profile /opt/rawlead/src/api_server.py",
        check=False,
    )
    print(out or "")
    text = out or ""
    ok = "active" in text and "1.16.4" in text and "has_profile" in open(_ROOT / "src" / "api_server.py", encoding="utf-8").read()
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
