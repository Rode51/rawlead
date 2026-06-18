#!/usr/bin/env python3
"""O237: WP theme + YANDEX_METRIKA_ID in wp-config (counter 109860210)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"
_METRIKA_ID = "109860210"

sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    if not _THEME.is_dir():
        print("missing theme:", _THEME)
        return 1

    print("=== O237 Yandex Metrika deploy ===")
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

    ssh.run(
        f"grep -q \"YANDEX_METRIKA_ID\" /var/www/rawlead.ru/wp-config.php || "
        f"sed -i \"/^\\/\\* That's all/i define('YANDEX_METRIKA_ID', '{_METRIKA_ID}');\" "
        f"/var/www/rawlead.ru/wp-config.php"
    )
    ssh.run(
        f"grep -q '^YANDEX_METRIKA_ID=' /opt/rawlead/.env.site && "
        f"sed -i 's/^YANDEX_METRIKA_ID=.*/YANDEX_METRIKA_ID={_METRIKA_ID}/' /opt/rawlead/.env.site || "
        f"echo 'YANDEX_METRIKA_ID={_METRIKA_ID}' >> /opt/rawlead/.env.site",
        check=False,
    )

    _, out, _ = ssh.run(
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "grep -c rawlead_yandex_metrika_enabled "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/yandex-metrika.php && "
        "grep YANDEX_METRIKA_ID /var/www/rawlead.ru/wp-config.php | head -1 && "
        "curl -sS https://rawlead.ru/lenta/ 2>/dev/null | grep -o 'mc.yandex.ru/metrika/tag.js' | head -1 && "
        f"curl -sS https://rawlead.ru/lenta/ 2>/dev/null | grep -o '{_METRIKA_ID}' | head -1",
        check=False,
    )
    print(out or "")
    text = out or ""
    ok = "rawlead_yandex_metrika_enabled" in text and _METRIKA_ID in text
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY VERIFY — check manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
