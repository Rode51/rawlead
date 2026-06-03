#!/usr/bin/env python3
"""O95-fix-2: WP theme 1.16.2 — /me/feed + loadTags/persist sync."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== O95-fix-2 deploy (1.16.2) ===")
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
    _, ver, _ = ssh.run(
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
        check=False,
    )
    _, me_feed, _ = ssh.run(
        "grep -c restMeFeed "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php",
        check=False,
    )
    _, feed_js, _ = ssh.run(
        "grep -c feedApiBase "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js",
        check=False,
    )
    print("version:", ver.strip())
    print("restMeFeed lines:", me_feed.strip())
    print("feedApiBase lines:", feed_js.strip())
    ok = (
        "1.16.2" in ver
        and int((me_feed.strip() or "0").split()[0]) >= 1
        and int((feed_js.strip() or "0").split()[0]) >= 1
    )
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
