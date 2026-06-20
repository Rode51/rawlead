#!/usr/bin/env python3
"""O280-R9b: avatar dir post-Next cutover — fix .env.site + deploy user_avatar.py."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

AVATAR_DIR = "/opt/rawlead/data/avatars"
_REMOTE = "/opt/rawlead/src/user_avatar.py"
_ENV_KEY = "RAWLEAD_AVATAR_DIR"


def _patch_env_site() -> None:
    esc = AVATAR_DIR.replace("'", "'\\''")
    ssh.run(
        f"grep -q '^{_ENV_KEY}=' /opt/rawlead/.env.site 2>/dev/null && "
        f"sed -i 's|^{_ENV_KEY}=.*|{_ENV_KEY}={esc}|' /opt/rawlead/.env.site || "
        f"echo '{_ENV_KEY}={esc}' >> /opt/rawlead/.env.site"
    )


def main() -> int:
    print("=== O280-R9b deploy: avatar VPS path ===")
    print("--- mkdir + chown avatar dir ---")
    _, out, _ = ssh.run(
        f"mkdir -p {AVATAR_DIR} && chown rawlead:rawlead {AVATAR_DIR} && chmod 755 {AVATAR_DIR} && "
        f"ls -ld {AVATAR_DIR}",
        check=False,
    )
    print((out or "").strip())

    print("--- patch .env.site RAWLEAD_AVATAR_DIR ---")
    _patch_env_site()
    _, out, _ = ssh.run(
        f"grep '^{_ENV_KEY}=' /opt/rawlead/.env.site | tail -1",
        check=False,
    )
    print((out or "").strip())

    print("--- upload src/user_avatar.py ---")
    ssh.upload(_ROOT / "src/user_avatar.py", _REMOTE)
    ssh.run(f"chown rawlead:rawlead {_REMOTE}")

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "curl -sf http://127.0.0.1:8000/health && echo api_ok && "
        f"grep -c '_wp_content_path_unwritable' {_REMOTE}",
        check=False,
    )
    print((out or "").strip())
    ok = "api_ok" in (out or "") and "active" in (out or "")
    print("O280-R9b DEPLOY OK" if ok else "O280-R9b DEPLOY — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
