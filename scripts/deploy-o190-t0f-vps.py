#!/usr/bin/env python3
"""O190 t0f: health_check off main thread + PW asyncio loop guards."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    ("src/health_check.py", "/opt/rawlead/src/health_check.py"),
    ("src/exchange_browser_fetch.py", "/opt/rawlead/src/exchange_browser_fetch.py"),
)


def main() -> int:
    print("=== O190 t0f deploy: health_check thread + asyncio guards ===")
    remotes: list[str] = []
    for rel, remote in _UPLOADS:
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    reset_guard = (
        "cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src "
        ".venv/bin/python -c \"from config import load_config; "
        "from storage import storage_from_config; "
        "from youdo_parser import _reset_youdo_fail_streak, YOUDO_COOLDOWN_KEY; "
        "st = storage_from_config(load_config()); "
        "_reset_youdo_fail_streak(st); "
        "st.set_setting(YOUDO_COOLDOWN_KEY, '0'); "
        "print('guard_reset_ok')\""
    )
    _, out, _ = ssh.run(
        "grep -c 'check_telethon_account_sync' /opt/rawlead/src/health_check.py && "
        "grep -c '_clear_stale_asyncio_loop' /opt/rawlead/src/exchange_browser_fetch.py && "
        f"{reset_guard} && "
        "systemctl stop rawlead-radar 2>/dev/null || true; sleep 3; "
        "systemctl reset-failed rawlead-radar 2>/dev/null || true; "
        "systemctl start rawlead-radar && sleep 6 && systemctl is-active rawlead-radar && "
        "echo o190_t0f_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text.encode("ascii", errors="replace").decode("ascii"))
    if "o190_t0f_deploy_ok" not in text or "active" not in text:
        print("O190 t0f DEPLOY CHECK FAILED")
        return 1
    print("O190 t0f DEPLOY OK — wait 1-2 cycles: grep fetch_end parsed / health:youdo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
