#!/usr/bin/env python3
"""O122: delist batch env, redirect detection, /ops/ «Проверить ссылки».

O122-hotfix: trial_subscription.py (radar import), ops delist limit=15, WP timeout 120s.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "src/delist_checker.py",
    "src/fl_parser.py",
    "src/kwork_parser.py",
    "src/main.py",
    "src/owner_admin.py",
    "src/trial_subscription.py",
)


def main() -> int:
    print("=== O122 deploy: delist + ops link check ===")
    remotes: list[str] = []
    for rel in _FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)

    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    api_rel = "wordpress/rawlead-kadence-child/inc/rawlead-api.php"
    api_local = _ROOT / api_rel
    api_remote = "/opt/rawlead/" + api_rel
    ssh.upload(api_local, api_remote)
    print("up", api_rel)
    ssh.run(
        "cp /opt/rawlead/wordpress/rawlead-kadence-child/inc/rawlead-api.php "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/rawlead-api.php && "
        "chown www-data:www-data "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/rawlead-api.php"
    )

    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-radar && systemctl is-active rawlead-api && "
        "grep -c 'Проверить ссылки' /opt/rawlead/src/owner_admin.py && "
        "grep -c 'delist_interval_sec' /opt/rawlead/src/delist_checker.py && "
        "grep -c '_fl_redirected_away' /opt/rawlead/src/fl_parser.py && "
        "test -f /opt/rawlead/src/trial_subscription.py && "
        "grep -c \"delist') ? 120\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/rawlead-api.php && "
        "echo o122_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    ok = "active" in text and "o122_ok" in text
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
