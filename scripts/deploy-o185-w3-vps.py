#!/usr/bin/env python3
"""O185 wave 3: t5b feed reset keep skills — VPS deploy."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

THEME_VER = "1.18.75"

_THEME_FILES = (
    "wordpress/rawlead-kadence-child/functions.php",
    "wordpress/rawlead-kadence-child/style.css",
    "wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js",
)


def main() -> int:
    print("=== O185 wave 3 deploy (t5b feed reset keep skills) ===")

    for rel in _THEME_FILES:
        local = _ROOT / rel
        remote = "/opt/rawlead/" + rel
        ssh.upload(local, remote)
        print(f"up {rel}")

    ssh.run(
        "rsync -a /opt/rawlead/wordpress/rawlead-kadence-child/ "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/ && "
        "chown -R www-data:www-data /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child"
    )

    _, out, _ = ssh.run(
        "grep -c 'persistTags\\(\\[\\]' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js; "
        "grep -c 'state.draftTags = \\[\\]' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js; "
        f"grep RAWLEAD_CHILD_VERSION "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
        check=False,
    )
    print((out or "").strip())
    ok = THEME_VER in (out or "")
    print("O185-W3 DEPLOY OK" if ok else "O185-W3 DEPLOY — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
