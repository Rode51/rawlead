#!/usr/bin/env python3
"""O262i: YouDo 3 conflicts — DC_SLOTS=0, cycle wall ≥900, ingest path."""
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
    ("src/exchange_proxy.py", "/opt/rawlead/src/exchange_proxy.py"),
    ("src/main.py", "/opt/rawlead/src/main.py"),
)
_ENV_KEYS = (
    ("YOUDO_O191_DC_SLOTS", "0"),
    ("RADAR_CYCLE_WALL_SEC", "900"),
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
grep YOUDO_O191_DC_SLOTS /opt/rawlead/.env.site | tail -1
grep RADAR_CYCLE_WALL_SEC /opt/rawlead/.env.site | tail -1
grep -n 'max(0, int(raw))' /opt/rawlead/src/exchange_proxy.py | head -1
grep -n 'max(base, 900.0)' /opt/rawlead/src/main.py | head -1
grep 'youdo:ingest done' /opt/rawlead/data/radar_site.log | tail -5 || echo 'no ingest log yet'
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
    print("OK — O262i deployed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
