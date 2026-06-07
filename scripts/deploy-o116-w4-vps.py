#!/usr/bin/env python3
"""O116-W4: support TG + contact form — theme 1.18.14 + API + Neon 019."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"
THEME_VER = "1.18.14"
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_API_SRC = (
    "support_tickets.py",
    "api_server.py",
    "owner_admin.py",
    "telegram_control.py",
)


def _apply_sql_019() -> str:
    local_sql = _ROOT / "sql" / "019_support_tickets.sql"
    if not local_sql.is_file():
        return "SKIP sql/019 missing"
    ssh.upload(local_sql, "/opt/rawlead/sql/019_support_tickets.sql")
    _, out, _ = ssh.run(
        "DB_URL=$(grep '^DATABASE_URL=' /opt/rawlead/.env.site | head -1 | cut -d= -f2-) && "
        "psql \"$DB_URL\" -f /opt/rawlead/sql/019_support_tickets.sql && "
        "psql \"$DB_URL\" -c \"\\dt support_*\" 2>/dev/null | head -5 && echo 'NEON-019 OK'",
        check=False,
    )
    return out or ""


def main() -> int:
    print(f"=== O116-W4 deploy (theme {THEME_VER} + API + Neon 019) ===")

    sql_out = _apply_sql_019()
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
        "systemctl restart rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-api && "
        f"grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "wc -c /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-support.js && "
        "grep -c '/support/unread' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/rawlead-api.php && "
        "grep -c support_tickets /opt/rawlead/src/api_server.py && "
        f"curl -sS -o /dev/null -w 'support_unread:%{{http_code}}\\n' "
        "https://rawlead.ru/wp-json/rawlead/v1/support/unread && "
        f"curl -sS https://rawlead.ru/contact/ 2>/dev/null | grep -c mailto || true",
        check=False,
    )
    print(out or "")
    text = (out or "") + sql_out
    route_ok = any(
        s in text
        for s in (
            "support_unread:400",
            "support_unread:401",
            "support_unread:200",
            "support_unread:403",
        )
    )
    ok = (
        "active" in text
        and THEME_VER in text
        and "NEON-019 OK" in text
        and route_ok
        and "support_unread:404" not in text
    )
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY VERIFY — check manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
