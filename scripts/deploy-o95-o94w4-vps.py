#!/usr/bin/env python3
"""O95 + O94-w4-code: WP theme 1.16.0 + api_server today_count · restart API."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def _deploy_wp() -> None:
    if not _THEME.is_dir():
        raise SystemExit(f"missing theme: {_THEME}")
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


def _deploy_api() -> None:
    local = _ROOT / "src" / "api_server.py"
    remote = "/opt/rawlead/src/api_server.py"
    ssh.upload(local, remote)
    ssh.run(f"chown rawlead:rawlead {remote}")
    print("up src/api_server.py")


def main() -> int:
    print("=== O95 + O94-w4-code deploy (1.16.0) ===")
    _deploy_wp()
    _deploy_api()
    print("restart rawlead-api...")
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && systemctl is-active rawlead-api",
        check=False,
    )
    print(out or "")
    _, ver, _ = ssh.run(
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
        check=False,
    )
    _, tray, _ = ssh.run(
        "grep -c rl-l3-tray "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/css/rawlead.css",
        check=False,
    )
    _, anon, _ = ssh.run(
        "grep -c rl-app--feed-anon "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/css/rawlead.css",
        check=False,
    )
    _, health, _ = ssh.run(
        "curl -sf http://127.0.0.1:8000/health | head -c 300; echo",
        check=False,
    )
    print("version:", ver.strip())
    print("rl-l3-tray lines:", tray.strip())
    print("rl-app--feed-anon lines:", anon.strip())
    print("health:", (health or "").strip())
    ok = (
        "1.16.0" in ver
        and int((tray.strip() or "0").split()[0]) >= 3
        and int((anon.strip() or "0").split()[0]) >= 1
        and "active" in (out or "")
    )
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
