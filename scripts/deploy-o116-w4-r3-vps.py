#!/usr/bin/env python3
"""O116-W4 R3: theme 1.18.15 — contact without mailto."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"
THEME_VER = "1.18.15"
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print(f"=== O116-W4 R3 deploy (theme {THEME_VER}) ===")
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
        f"grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "grep -c mailto "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/marketing.php; "
        f"curl -sS https://rawlead.ru/contact/ 2>/dev/null | grep -c mailto || true",
        check=False,
    )
    print(out or "")
    text = out or ""
    ok = THEME_VER in text and text.strip().endswith("0")
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY VERIFY — check manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
