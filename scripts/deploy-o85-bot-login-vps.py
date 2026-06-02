#!/usr/bin/env python3
"""O85: bot-session WP REST proxy + bot-first /login."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "src/api_server.py",
    "src/telegram_control.py",
)


def main() -> int:
    print("=== O85 bot login fix deploy ===")
    remotes: list[str] = []
    for rel in _FILES:
        local = _ROOT / rel
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(local, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

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
        "systemctl restart rawlead-api rawlead-bot-poll rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-api rawlead-bot-poll rawlead-radar && "
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "grep -c auth/bot-session "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/rawlead-api.php && "
        "grep -c mint_bot_first_login_url /opt/rawlead/src/api_server.py && "
        "curl -sf -o /dev/null -w 'wp_bot_session=%{http_code}\\n' "
        "-X POST https://rawlead.ru/wp-json/rawlead/v1/auth/bot-session "
        "-H 'Content-Type: application/json' -d '{}'",
        check=False,
    )
    print(out or "")
    ok = "active" in (out or "") and "1.11.20" in (out or "") and "wp_bot_session=200" in (out or "")
    print("O85 DEPLOY OK" if ok else "O85 DEPLOY — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
