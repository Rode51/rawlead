#!/usr/bin/env python3

"""O116-b2 flip + tag +n: theme 1.18.13 · feed face chips."""

from __future__ import annotations



import sys

from pathlib import Path



_ROOT = Path(__file__).resolve().parents[1]

_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"

sys.path.insert(0, str(_ROOT / "scripts"))

import deploy_vps_ssh as ssh  # noqa: E402





def main() -> int:

    print("=== O116-b2 deploy (theme 1.18.13) ===")



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

        "grep -c rl-feed-card__flip "

        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js && "

        "grep -c 'renderTagChips(item, 2)' "

        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js && "

        "grep -c rl-chip--more "

        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js && "

        "curl -sS https://rawlead.ru/lenta/ 2>/dev/null | grep -o '1\\.18\\.13' | head -1",

        check=False,

    )

    print(out or "")

    text = out or ""
    ok = "1.18.13" in text
    if ok:

        print("DEPLOY OK")

        return 0

    print("DEPLOY VERIFY — check manually")

    return 1





if __name__ == "__main__":

    raise SystemExit(main())

