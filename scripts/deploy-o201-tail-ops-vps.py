#!/usr/bin/env python3
"""O201 tail: ops auth hardening + header admin + SSR dashboard hydrate — API + theme."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.site", override=False)

_API_FILES = ("src/owner_admin.py", "src/api_server.py")
_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"
_EXPECT_THEME = "1.18.78"


def _upload_api() -> list[str]:
    remotes: list[str] = []
    for rel in _API_FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    return remotes


def _deploy_theme() -> bool:
    if not _THEME.is_dir():
        print("missing theme:", _THEME)
        return False
    n = ssh.sync_project(
        local_root=_THEME,
        remote_root="/opt/rawlead/wordpress/rawlead-kadence-child",
    )
    print(f"theme uploaded {n} files")
    ssh.run(
        "rsync -a /opt/rawlead/wordpress/rawlead-kadence-child/ "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/ && "
        "chown -R www-data:www-data /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child"
    )
    _, ver, _ = ssh.run(
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
        check=False,
    )
    print("theme version:", (ver or "").strip())
    return _EXPECT_THEME in (ver or "")


def main() -> int:
    print("=== O201 tail ops fix deploy ===")
    api_remotes = _upload_api()
    ssh.run("chown rawlead:rawlead " + " ".join(api_remotes))

    _, out_api, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-api && "
        "grep -c 'max_age=0' /opt/rawlead/src/api_server.py && "
        "grep -c can_ops_admin /opt/rawlead/src/api_server.py && "
        "grep -c hydrateDashboardFallback /opt/rawlead/src/owner_admin.py && "
        "grep -c rlOpsRenderProxies /opt/rawlead/src/owner_admin.py && "
        "curl -sf -o /tmp/ops_tail.html -w 'ops_local=%{http_code}\\n' http://127.0.0.1:8000/ops/ && "
        "grep -c 'type=\"password\"' /tmp/ops_tail.html && "
        "echo o201_tail_api_ok",
        check=False,
    )
    print(out_api.strip())
    api_ok = "o201_tail_api_ok" in (out_api or "") and "active" in (out_api or "")

    theme_ok = _deploy_theme()
    _, out_hdr, _ = ssh.run(
        "grep -c 'rl-header__admin' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/template-parts/rawlead/header.php && "
        "grep -c 'syncAdminLinks' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/template-parts/rawlead/header.php",
        check=False,
    )
    hdr_ok = (out_hdr or "").strip() not in {"", "0"}

    ok = api_ok and theme_ok and hdr_ok
    print("O201 TAIL OK" if ok else "O201 TAIL — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
