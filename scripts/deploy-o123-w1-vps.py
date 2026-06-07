#!/usr/bin/env python3
"""O123-w1: theme 1.18.16 — copy 10/h, feed-strip, flow caption, cabinet CTA."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"
THEME_VER = "1.18.16"
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print(f"=== O123-w1 deploy (theme {THEME_VER}) ===")
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
        "grep -c '10 откликов в час' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/marketing.php && "
        "grep -c 'Продлить подписку' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-cabinet.js || true",
        check=False,
    )
    print(out or "")
    text = out or ""
    ok = THEME_VER in text and "0" in text.splitlines()[-1] if text.strip() else False
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY VERIFY — check manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
