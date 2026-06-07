#!/usr/bin/env python3
"""O121-w2b: /ops/ control timeout 90s — clear-bans, radar/site/bots restart."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_API_REL = "wordpress/rawlead-kadence-child/inc/rawlead-api.php"
_THEME_API = (
    "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/rawlead-api.php"
)


def main() -> int:
    print("=== O121-w2b deploy: /ops/ control timeout 90s ===")
    api_local = _ROOT / _API_REL
    api_remote = "/opt/rawlead/" + _API_REL
    ssh.upload(api_local, api_remote)
    print("up", _API_REL)
    ssh.run(
        f"cp /opt/rawlead/{_API_REL} {_THEME_API} && "
        f"chown www-data:www-data {_THEME_API}"
    )

    _, out, _ = ssh.run(
        f"grep -c \"clear-bans'\" {_THEME_API} && "
        f"grep -c '\\$timeout = 90' {_THEME_API} && "
        f"grep -c \"delist'\" {_THEME_API} && "
        "echo o121_w2b_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    ok = "o121_w2b_ok" in text
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
