#!/usr/bin/env python3
"""O107: Trial 3 дня — Neon migration + API + theme 1.18.17."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

THEME_VER = "1.18.17"

_SRC_FILES = (
    "api_server.py",
    "trial_subscription.py",
    "match_push.py",
    "main.py",
)

_THEME_FILES = (
    "wordpress/rawlead-kadence-child/functions.php",
    "wordpress/rawlead-kadence-child/inc/rawlead-api.php",
    "wordpress/rawlead-kadence-child/page-cabinet.php",
    "wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js",
)


def _apply_neon_migration() -> str:
    local_sql = _ROOT / "sql" / "020_trial_subscription.sql"
    if not local_sql.is_file():
        return "SKIP sql/020 missing"
    ssh.upload(local_sql, "/opt/rawlead/sql/020_trial_subscription.sql")
    _, out, _ = ssh.run(
        "set -a && source /opt/rawlead/.env.site 2>/dev/null; set +a; "
        "DB_URL=\"${DATABASE_URL:-$NEON_DATABASE_URL}\"; "
        "psql \"$DB_URL\" -f /opt/rawlead/sql/020_trial_subscription.sql && "
        "psql \"$DB_URL\" -c \"\\d subscriptions\" 2>/dev/null | grep trial_ && echo 'NEON-020 OK'",
        check=False,
    )
    return (out or "").strip()


def main() -> int:
    print(f"=== O107 deploy (theme {THEME_VER}) ===")
    neon_out = _apply_neon_migration()
    print(neon_out)

    for name in _SRC_FILES:
        local = _ROOT / "src" / name
        remote = f"/opt/rawlead/src/{name}"
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up src/{name}")

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
        "systemctl restart rawlead-api rawlead-radar rawlead-radar-legacy && sleep 3 && "
        "systemctl is-active rawlead-api rawlead-radar rawlead-radar-legacy && "
        "grep -c trial_subscription /opt/rawlead/src/api_server.py && "
        "grep -c trial-start /opt/rawlead/wordpress/rawlead-kadence-child/inc/rawlead-api.php && "
        "grep -c 'Попробовать 3 дня' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/page-cabinet.php && "
        "grep RAWLEAD_CHILD_VERSION "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "echo o107_ok",
        check=False,
    )
    print((out or "").strip())
    text = out or ""
    ok = text.count("active") >= 3 and "o107_ok" in text and THEME_VER in text
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY VERIFY — check manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
