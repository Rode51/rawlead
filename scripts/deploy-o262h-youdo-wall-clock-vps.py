#!/usr/bin/env python3
"""O262h: YouDo wall-clock race — outer grace + carousel headroom on VPS."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.site", override=True)

_ENV_SITE = "/opt/rawlead/.env.site"
_UPLOADS = (
    ("src/youdo_parser.py", "/opt/rawlead/src/youdo_parser.py"),
    ("src/exchange_browser_fetch.py", "/opt/rawlead/src/exchange_browser_fetch.py"),
    ("src/main.py", "/opt/rawlead/src/main.py"),
)
_ENV_KEYS = (
    ("YOUDO_CAROUSEL_WALL_EXTRA_SEC", "150"),
    ("YOUDO_FETCH_OUTER_GRACE_SEC", "90"),
)


def _patch_env_key(key: str, value: str) -> bool:
    safe = value.replace("'", "'\"'\"'")
    cmd = (
        f"grep -q '^{key}=' {_ENV_SITE} 2>/dev/null && "
        f"sed -i '/^{key}=/d' {_ENV_SITE}; "
        f"echo '{key}={safe}' >> {_ENV_SITE} && "
        f"grep -c '^{key}=' {_ENV_SITE}"
    )
    _, out, _ = ssh.run(cmd, check=False)
    return (out or "").strip() == "1"


def _verify_remote() -> str:
    remote = r"""
grep YOUDO_FETCH_OUTER_GRACE_SEC /opt/rawlead/.env.site | tail -1
grep YOUDO_CAROUSEL_WALL_EXTRA_SEC /opt/rawlead/.env.site | tail -1
grep -c 'youdo:ingest done' /opt/rawlead/src/main.py
grep 'youdo:ingest done' /opt/rawlead/data/radar_site.log | tail -3 || echo 'no ingest log yet'
grep 'YouDo ' /opt/rawlead/data/radar_site.log | tail -3
"""
    _, out, _ = ssh.run(remote.strip(), check=False)
    return (out or "").replace("\r\n", "\n")


def main() -> int:
    for key, val in _ENV_KEYS:
        if not _patch_env_key(key, val):
            print(f"FAIL — {key} not written")
            return 1
        print(f"env: {key}={val} ok")

    for local, remote in _UPLOADS:
        ssh.upload(_ROOT / local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"uploaded {local}")

    _, rst, _ = ssh.run(
        "systemctl restart rawlead-radar rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-radar rawlead-api",
        check=False,
    )
    print(rst or "")
    print(_verify_remote())

    ok = "active" in (rst or "")
    if not ok:
        print("FAIL — services not active")
        return 1
    print("OK — O262h deployed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
