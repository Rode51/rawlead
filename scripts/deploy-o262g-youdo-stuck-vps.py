#!/usr/bin/env python3
"""O262g: YouDo stuck leads — requeue L1 + YOUDO_DETAIL_FETCH=0 on VPS."""
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
    ("src/lead_pipeline.py", "/opt/rawlead/src/lead_pipeline.py"),
    ("src/pg_storage.py", "/opt/rawlead/src/pg_storage.py"),
    ("scripts/requeue_youdo_l1.py", "/opt/rawlead/scripts/requeue_youdo_l1.py"),
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
grep 'YOUDO_DETAIL_FETCH=' /opt/rawlead/.env.site | tail -1
grep 'pipeline:L1 youdo:' /opt/rawlead/data/radar_site.log | tail -5 || echo 'no L1 youdo yet'
grep 'конвейер:L1=' /opt/rawlead/data/radar_site.log | tail -3 || true
"""
    _, out, _ = ssh.run(remote.strip(), check=False)
    return (out or "").replace("\r\n", "\n")


def main() -> int:
    if not _patch_env_key("YOUDO_DETAIL_FETCH", "0"):
        print("FAIL — YOUDO_DETAIL_FETCH not written")
        return 1
    print("env: YOUDO_DETAIL_FETCH=0 ok")

    for local, remote in _UPLOADS:
        ssh.upload(_ROOT / local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"uploaded {local}")

    _, requeue_out, _ = ssh.run(
        "cd /opt/rawlead && sudo -u rawlead env RADAR_PROFILE=site "
        "PYTHONPATH=/opt/rawlead/src .venv/bin/python "
        "scripts/requeue_youdo_l1.py --apply --since 2026-06-15",
        check=False,
    )
    print((requeue_out or "").strip())

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
    print("OK — O262g deployed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
