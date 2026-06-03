#!/usr/bin/env python3
"""O96-polish-b: CTA slot, cabinet copy, live-preview corner, features H2 · theme 1.17.2."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== O96-polish-b deploy (1.17.2) ===")
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
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "grep -c 'rl-feed-card__cta:empty' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/css/rawlead.css && "
        "grep -c 'Показать ещё' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/page-cabinet.php",
        check=False,
    )
    print(out.strip())
    print("=== done ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
