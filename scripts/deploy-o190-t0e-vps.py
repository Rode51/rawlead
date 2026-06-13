#!/usr/bin/env python3
"""O190 t0e/t0i: camoufox listing — thread guards + subprocess isolation."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    ("src/exchange_browser_fetch.py", "/opt/rawlead/src/exchange_browser_fetch.py"),
    ("src/main.py", "/opt/rawlead/src/main.py"),
    ("src/delist_checker.py", "/opt/rawlead/src/delist_checker.py"),
    ("scripts/youdo_fetch_worker.py", "/opt/rawlead/scripts/youdo_fetch_worker.py"),
    ("scripts/smoke_youdo_t6c_vps.py", "/opt/rawlead/scripts/smoke_youdo_t6c_vps.py"),
)


def main() -> int:
    print("=== O190 t0j deploy: cycle close + fetch_end gate + delist cap ===")
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
        "grep -c 'youdo_fetch_worker' /opt/rawlead/src/exchange_browser_fetch.py && "
        "grep -c '_commit_youdo_fetch_gate' /opt/rawlead/src/main.py && "
        "grep -c 'youdo_delist_max_per_cycle' /opt/rawlead/src/delist_checker.py && "
        "grep -c 'fetch_listing_html_browser_slots_wall_clock' "
        "/opt/rawlead/src/exchange_browser_fetch.py && "
        f"{reset_guard} && "
        "systemctl stop rawlead-radar 2>/dev/null || true; sleep 3; "
        "systemctl reset-failed rawlead-radar 2>/dev/null || true; "
        "systemctl start rawlead-radar && sleep 6 && systemctl is-active rawlead-radar && "
        "echo o190_t0e_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text.encode("ascii", errors="replace").decode("ascii"))
    if "o190_t0e_deploy_ok" not in text or "active" not in text:
        print("O190 t0e DEPLOY CHECK FAILED")
        return 1
    print("O190 t0e DEPLOY OK — wait 1-2 cycles: grep fetch_end parsed / smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
