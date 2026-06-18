#!/usr/bin/env python3
"""O261: FL dead-proxy rotate, YouDo DC ban limit, auto-unban, ops YouDo clear button."""
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
    ("src/exchange_browser_fetch.py", "/opt/rawlead/src/exchange_browser_fetch.py"),
    ("src/fl_parser.py", "/opt/rawlead/src/fl_parser.py"),
    ("src/proxy_ops.py", "/opt/rawlead/src/proxy_ops.py"),
    ("src/owner_admin.py", "/opt/rawlead/src/owner_admin.py"),
    ("src/static/ops-pult.js", "/opt/rawlead/src/static/ops-pult.js"),
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
grep -E 'fetch:(fl|youdo)' /opt/rawlead/data/radar_site.log | tail -10
"""
    _, out, _ = ssh.run(remote.strip(), check=False)
    return out or ""


def main() -> int:
    for key, val in (
        ("YOUDO_MAX_DC_BANS_PER_FETCH", "2"),
        ("YOUDO_AUTO_UNBAN_MIN", "20"),
        ("FL_DEAD_PROXY_BAN_TTL_SEC", "300"),
        ("FL_HTTPX_MAX_BANS", "4"),
    ):
        if not _patch_env_key(key, val):
            print(f"FAIL — {key} not written")
            return 1
    print("env: O261 recovery vars ok")

    for local_rel, remote in _UPLOADS:
        local = _ROOT / local_rel
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up {local_rel}")

    _, rst, _ = ssh.run(
        "systemctl restart rawlead-radar rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-radar rawlead-api",
        check=False,
    )
    print(rst or "")

    verify = _verify_remote()
    print(verify)

    ok = "active" in (rst or "")
    if not ok:
        print("FAIL — services not active")
        return 1
    print("OK — O261 deployed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
