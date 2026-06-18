#!/usr/bin/env python3
"""O262d: YouDo list-view selector gate + pass2 on false click."""
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
    ("src/exchange_browser_fetch.py", "/opt/rawlead/src/exchange_browser_fetch.py"),
    ("scripts/youdo_fetch_worker.py", "/opt/rawlead/scripts/youdo_fetch_worker.py"),
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
grep 'youdo:trace stage=list_view' /opt/rawlead/data/radar_site.log | tail -8 || echo 'no list_view yet'
grep 'youdo:trace stage=fetch_end' /opt/rawlead/data/radar_site.log | tail -3
"""
    _, out, _ = ssh.run(remote.strip(), check=False)
    return out or ""


def main() -> int:
    for key, val in (
        ("YOUDO_LIST_VIEW_FORCE_MIN_HTML", "50000"),
        ("YOUDO_LIST_VIEW_CLICK", "1"),
        ("YOUDO_LIST_VIEW_ALLOW_CLASS_FALLBACK", "1"),
    ):
        if not _patch_env_key(key, val):
            print(f"FAIL — {key} not written")
            return 1
    print("env: O262d list-view vars ok")

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
    print(
        "OK — O262d deployed "
        "(grep stage=list_view selector_tier=primary or pass=2 parsed=50)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
