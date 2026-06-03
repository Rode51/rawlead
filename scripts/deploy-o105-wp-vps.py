#!/usr/bin/env python3
"""O105-WP-r3: TWO-SPEEDS anon strip · cabinet notif Premium · theme 1.18.3."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== O105-WP-r3 deploy (1.18.3) ===")
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
        "grep -c '790 ₽/мес' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/marketing.php && "
        "grep -c 'Почему лимит 10 откликов' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/marketing.php && "
        "grep -c rl-feed-card__slot-line "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js && "
        "grep -c 'Premium — сразу, от 790' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/page-lenta.php && "
        "grep -c 'Premium в @rawlead_bot' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/page-cabinet.php && "
        "curl -sS https://rawlead.ru/faq/ 2>/dev/null | grep -c '790 ₽/мес' || true && "
        "curl -sS https://rawlead.ru/how/ 2>/dev/null | grep -c '790 ₽/мес' || true && "
        "curl -sS https://rawlead.ru/lenta/ 2>/dev/null | grep -c '1.18.3' || true",
        check=False,
    )
    print(out or "")
    text = out or ""
    ok = "1.18.3" in text
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
