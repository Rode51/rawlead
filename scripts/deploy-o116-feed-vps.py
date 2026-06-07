#!/usr/bin/env python3
"""O116-WP-FEED + Z234: feed prefs Neon · toolbar · feed_social · theme 1.18.10."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_API_SRC = (
    "api_server.py",
    "feed_social.py",
    "jwt_auth.py",
)


def _apply_sql_018() -> str:
    local_sql = _ROOT / "sql" / "018_user_feed_prefs.sql"
    if not local_sql.is_file():
        return "SKIP sql/018 missing"
    ssh.upload(local_sql, "/opt/rawlead/sql/018_user_feed_prefs.sql")
    _, out, _ = ssh.run(
        "DB_URL=$(grep '^DATABASE_URL=' /opt/rawlead/.env.site | head -1 | cut -d= -f2-) && "
        "psql \"$DB_URL\" -f /opt/rawlead/sql/018_user_feed_prefs.sql && "
        "psql \"$DB_URL\" -c \"\\d users\" 2>/dev/null | grep feed_prefs && echo 'NEON-018 OK'",
        check=False,
    )
    return out or ""


def main() -> int:
    print("=== O116-WP-FEED deploy (theme 1.18.10 + API) ===")

    sql_out = _apply_sql_018()
    print(sql_out)

    remote_src = "/opt/rawlead/src"
    for name in _API_SRC:
        local = _ROOT / "src" / name
        if not local.is_file():
            print("missing", local)
            return 1
        remote = f"{remote_src}/{name}"
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up src/{name}")

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
        "grep -q '^DRAFT_HOURLY_LIMIT=' /opt/rawlead/.env.site 2>/dev/null || "
        "echo 'DRAFT_HOURLY_LIMIT=10' >> /opt/rawlead/.env.site; "
        "systemctl restart rawlead-api rawlead-radar && sleep 4 && "
        "systemctl is-active rawlead-api rawlead-radar && "
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "grep -c rl-feed-toolbar "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js && "
        "grep -c display_replies /opt/rawlead/src/api_server.py && "
        "grep -c feed_prefs /opt/rawlead/src/api_server.py && "
        "curl -sS https://rawlead.ru/lenta/ 2>/dev/null | grep -o '1\\.18\\.10' | head -1 && "
        "curl -sS https://rawlead.ru/faq/ 2>/dev/null | grep -c rl-faq-group || true",
        check=False,
    )
    print(out or "")
    text = (out or "") + sql_out
    ok = (
        "active" in text
        and "1.18.10" in text
        and "NEON-018 OK" in text
    )
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY VERIFY — check manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
