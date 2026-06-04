#!/usr/bin/env python3
"""O109: Kwork delist grace + bot «Лента» deep link + feed scroll/pulse (theme 1.18.6)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_EXTRA_SRC = (
    "kwork_parser.py",
    "delist_checker.py",
    "pg_storage.py",
    "match_push.py",
)


def main() -> int:
    print("=== O109 deploy (delist fix + bot deeplink + theme 1.18.6) ===")

    uploaded = ssh.deploy_ingest_coupled_src()
    print(f"ingest coupled: {len(uploaded)} files")
    remote_src = "/opt/rawlead/src"
    for name in _EXTRA_SRC:
        local = _ROOT / "src" / name
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

    ssh.upload(_ROOT / "scripts" / "_relist_kwork_source_gone.py", "/tmp/relist_kwork_source_gone.py")
    _, relist_out, _ = ssh.run(
        "DB_URL=$(grep '^DATABASE_URL=' /opt/rawlead/.env.site | head -1 | cut -d= -f2-) && "
        "DATABASE_URL=\"$DB_URL\" /opt/rawlead/.venv/bin/python /tmp/relist_kwork_source_gone.py",
        check=False,
    )
    print(relist_out or "")

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 4 && "
        "systemctl is-active rawlead-api rawlead-radar && "
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "grep -c rl-lead-card--push-focus "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/css/rawlead.css && "
        "grep -c 'lead=' /opt/rawlead/src/match_push.py && "
        "curl -sS 'https://rawlead.ru/wp-json/rawlead/v1/leads/11837' 2>/dev/null | head -c 80 && echo && "
        "curl -sS https://rawlead.ru/lenta/ 2>/dev/null | grep -o '1\\.18\\.6' | head -1",
        check=False,
    )
    print(out or "")
    text = (out or "") + (relist_out or "")
    ok = (
        "active" in text
        and "1.18.6" in text
        and "relisted_kwork_source_gone=" in text
    )
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY VERIFY FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
