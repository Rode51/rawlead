#!/usr/bin/env python3
"""O174b UX: deploy WP theme 1.18.58 checkout flow."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

THEME_VER = "1.18.60"
_FILES = (
    "wordpress/rawlead-kadence-child/functions.php",
    "wordpress/rawlead-kadence-child/template-parts/rawlead/pricing-card.php",
    "wordpress/rawlead-kadence-child/assets/js/rawlead-pricing.js",
    "wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js",
    "wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js",
    "wordpress/rawlead-kadence-child/assets/css/rawlead.css",
)


def main() -> int:
    for rel in _FILES:
        local = _ROOT / rel
        ssh.upload(local, "/opt/rawlead/" + rel)
        print(f"up {rel}")
    ssh.run(
        "rsync -a /opt/rawlead/wordpress/rawlead-kadence-child/ "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/ && "
        "chown -R www-data:www-data /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child"
    )
    _, out, _ = ssh.run(
        f"grep RAWLEAD_CHILD_VERSION "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
        check=False,
    )
    print((out or "").strip())
    ok = THEME_VER in (out or "")
    print("O174b WP OK" if ok else "verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
