#!/usr/bin/env python3
"""O87: QR desktop login + ops pageview labels + mobile flow logo."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = ("src/owner_admin.py",)


def main() -> int:
    print("=== O87 QR + ops + logo deploy ===")
    for rel in _FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead /opt/rawlead/src/owner_admin.py")

    theme = _ROOT / "wordpress" / "rawlead-kadence-child"
    n = ssh.sync_project(
        local_root=theme,
        remote_root="/opt/rawlead/wordpress/rawlead-kadence-child",
    )
    print(f"theme uploaded {n} files")
    ssh.run(
        "rsync -a /opt/rawlead/wordpress/rawlead-kadence-child/ "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/ && "
        "chown -R www-data:www-data /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child"
    )

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "grep -c rl-cabinet-login__qr /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/page-cabinet.php && "
        "grep -c 'methods.*GET' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/rawlead-api.php && "
        "curl -sf -o /dev/null -w 'bot_complete_get=%{http_code}\\n' "
        "'https://rawlead.ru/wp-json/rawlead/v1/auth/bot-complete?auth=fake' -k",
        check=False,
    )
    print(out or "")
    text = out or ""
    ok = (
        "active" in text
        and "1.11.25" in text
        and "bot_complete_get=404" in text or "bot_complete_get=401" in text
    )
    print("O87 DEPLOY OK" if ok else "O87 DEPLOY — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
