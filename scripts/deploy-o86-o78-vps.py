#!/usr/bin/env python3
"""O86 bot silence + O78 admin dashboard + pageview WP REST proxy."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "src/owner_admin.py",
    "src/telegram_control.py",
    "src/match_push.py",
    "src/api_server.py",
)


def main() -> int:
    print("=== O86 + O78 deploy ===")
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
        "systemctl restart rawlead-api rawlead-bot-poll && sleep 4 && "
        "systemctl is-active rawlead-api rawlead-bot-poll && "
        "curl -sf http://127.0.0.1:8000/health; echo && "
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "grep -c admin/pageview "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/rawlead-api.php && "
        "grep -c tg:draft:mute /opt/rawlead/src/match_push.py && "
        "grep -c 'Пульт RawLead' /opt/rawlead/src/owner_admin.py && "
        "curl -sf -o /dev/null -w 'wp_pageview=%{http_code}\\n' "
        "-X POST https://rawlead.ru/wp-json/rawlead/v1/admin/pageview "
        "-H 'Content-Type: application/json' -d '{\"path\":\"/lenta\"}' && "
        "curl -sf http://127.0.0.1:8000/v1/admin/dashboard -H 'Authorization: Bearer invalid' "
        "-o /dev/null -w 'dash=%{http_code}\\n' || true",
        check=False,
    )
    print(out or "")
    text = out or ""
    ok = "active" in text and "1.11.22" in text and "wp_pageview=204" in text
    print("O86+O78 DEPLOY OK" if ok else "O86+O78 DEPLOY — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
