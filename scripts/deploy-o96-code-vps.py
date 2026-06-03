#!/usr/bin/env python3
"""O96-code: copy + UI O96-D · theme 1.17.0 (+ API today_count if not yet prod)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== O96-code deploy (1.17.0) ===")
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
        "grep -c rl-feed-anon-strip "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/page-lenta.php",
        check=False,
    )
    print(out or "")
    text = out or ""
    ok = "active" in text and "1.17.0" in text
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
