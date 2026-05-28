#!/usr/bin/env python3
"""Sync rawlead-kadence-child to VPS WP themes dir (B1 polish etc.)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    if not _THEME.is_dir():
        print("missing theme:", _THEME)
        return 1
    print("=== deploy WP theme B1 ===")
    n = ssh.sync_project(
        local_root=_THEME,
        remote_root="/opt/rawlead/wordpress/rawlead-kadence-child",
    )
    print(f"uploaded {n} files -> /opt/rawlead/wordpress/rawlead-kadence-child")
    ssh.run(
        "rsync -a /opt/rawlead/wordpress/rawlead-kadence-child/ "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/ && "
        "chown -R www-data:www-data /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child"
    )
    print("rsync -> /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child")
    _, ver, _ = ssh.run(
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
        check=False,
    )
    _, gs, _ = ssh.run(
        "grep -c GUEST_SKILLS "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js",
        check=False,
    )
    _, auth, _ = ssh.run(
        "grep -c 'Login required to save skills' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/rawlead-api.php",
        check=False,
    )
    print("version:", ver.strip())
    print("GUEST_SKILLS lines:", gs.strip())
    print("auth guard lines:", auth.strip())
    ok = "1.7.10" in ver and int((gs.strip() or "0").split()[0]) >= 1
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
