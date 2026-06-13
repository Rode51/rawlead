#!/usr/bin/env python3
"""O193: FL listing subprocess worker — deploy + grep gate."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    ("src/exchange_browser_fetch.py", "/opt/rawlead/src/exchange_browser_fetch.py"),
    ("scripts/fl_fetch_worker.py", "/opt/rawlead/scripts/fl_fetch_worker.py"),
)


def main() -> int:
    print("=== O193 deploy: FL listing subprocess worker ===")
    remotes: list[str] = []
    for rel, remote in _UPLOADS:
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    smoke = (
        "cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src "
        "FL_LISTING_SUBPROCESS=1 .venv/bin/python scripts/fl_fetch_worker.py "
        "--url https://www.fl.ru/projects/ --user-agent test --timeout 30 --json "
        "2>&1 | tail -1"
    )
    _, out, _ = ssh.run(
        "grep -c 'fl_fetch_worker' /opt/rawlead/src/exchange_browser_fetch.py && "
        "grep -c 'fetch_fl_listing_ephemeral_standalone' "
        "/opt/rawlead/src/exchange_browser_fetch.py && "
        "test -x /opt/rawlead/scripts/fl_fetch_worker.py || "
        "test -f /opt/rawlead/scripts/fl_fetch_worker.py && "
        f"{smoke} && "
        "systemctl stop rawlead-radar 2>/dev/null || true; sleep 3; "
        "systemctl reset-failed rawlead-radar 2>/dev/null || true; "
        "systemctl start rawlead-radar && sleep 6 && systemctl is-active rawlead-radar && "
        "echo o193_fl_subprocess_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text.encode("ascii", errors="replace").decode("ascii"))
    if "o193_fl_subprocess_deploy_ok" not in text or "active" not in text:
        print("O193 DEPLOY CHECK FAILED")
        return 1
    print("O193 DEPLOY OK — wait 1-2 cycles: grep 'listing:fl parsed' radar_site.log")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
