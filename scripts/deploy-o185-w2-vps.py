#!/usr/bin/env python3
"""O185 wave 2: t3 avatar · t4 match — VPS deploy."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

THEME_VER = "1.18.73"
AVATAR_DIR = "/var/www/rawlead.ru/wp-content/uploads/rawlead-avatars"

_SRC_FILES = (
    "api_server.py",
    "rank.py",
    "user_avatar.py",
)

_THEME_FILES = (
    "wordpress/rawlead-kadence-child/functions.php",
    "wordpress/rawlead-kadence-child/inc/rawlead-api.php",
    "wordpress/rawlead-kadence-child/page-cabinet.php",
    "wordpress/rawlead-kadence-child/template-parts/rawlead/header.php",
    "wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js",
    "wordpress/rawlead-kadence-child/assets/css/rawlead.css",
)


def _ensure_avatar_dir() -> str:
    _, out, err = ssh.run(
        f"mkdir -p {AVATAR_DIR} && "
        f"grep -q '^RAWLEAD_AVATAR_DIR=' /opt/rawlead/.env.site 2>/dev/null || "
        f"echo 'RAWLEAD_AVATAR_DIR={AVATAR_DIR}' >> /opt/rawlead/.env.site && "
        f"chown -R rawlead:www-data {AVATAR_DIR} && chmod 775 {AVATAR_DIR}",
        check=False,
    )
    return (out or err or "").strip()


def main() -> int:
    print("=== O185 wave 2 deploy (t3/t4) ===")
    print("--- avatar uploads dir ---")
    print(_ensure_avatar_dir())

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
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "grep -c 'def me_avatar' /opt/rawlead/src/api_server.py && "
        "test -d "
        + AVATAR_DIR
        + " && echo AVATAR_DIR_OK && "
        f"grep RAWLEAD_CHILD_VERSION "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "curl -s http://127.0.0.1:8000/health",
        check=False,
    )
    print((out or "").strip())
    ok = "active" in (out or "") and THEME_VER in (out or "") and "AVATAR_DIR_OK" in (out or "")
    print("O185-W2 DEPLOY OK" if ok else "O185-W2 DEPLOY — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
