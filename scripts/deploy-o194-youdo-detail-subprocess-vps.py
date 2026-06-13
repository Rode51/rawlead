#!/usr/bin/env python3
"""O194: YouDo detail subprocess (camoufox worker) — deploy + grep gate."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    ("src/exchange_browser_fetch.py", "/opt/rawlead/src/exchange_browser_fetch.py"),
    ("scripts/youdo_fetch_worker.py", "/opt/rawlead/scripts/youdo_fetch_worker.py"),
)


def main() -> int:
    print("=== O194 deploy: YouDo detail subprocess (camoufox worker) ===")
    remotes: list[str] = []
    for rel, remote in _UPLOADS:
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    smoke = (
        "cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src "
        "YOUDO_BROWSER=camoufox .venv/bin/python scripts/youdo_fetch_worker.py "
        "--url https://youdo.com/t1 --proxy $(grep -m1 YOUDO_PROXY /opt/rawlead/.env.site "
        "| cut -d= -f2- | tr -d '\"') "
        "--user-agent test --timeout 60 --stage detail --json 2>&1 | tail -1"
    )
    verify = (
        "grep -c '_youdo_use_subprocess_worker' /opt/rawlead/src/exchange_browser_fetch.py && "
        "grep -c 'youdo_fetch_worker.py' /opt/rawlead/src/exchange_browser_fetch.py && "
        "test -f /opt/rawlead/scripts/youdo_fetch_worker.py && "
        "systemctl stop rawlead-radar 2>/dev/null || true; sleep 3; "
        "systemctl reset-failed rawlead-radar 2>/dev/null || true; "
        "systemctl start rawlead-radar && sleep 6 && systemctl is-active rawlead-radar && "
        "echo o194_youdo_detail_subprocess_deploy_ok"
    )
    _, out, _ = ssh.run(verify, check=False)
    text = out or ""
    print(text.encode("ascii", errors="replace").decode("ascii"))
    if "o194_youdo_detail_subprocess_deploy_ok" not in text or "active" not in text:
        print("O194 DEPLOY CHECK FAILED")
        return 1
    print("O194 DEPLOY OK — wait 1-2 YouDo cycles:")
    print("  grep 'health:youdo ok' /opt/rawlead/data/radar_site.log | tail -3")
    print("  grep -E 'youdo:id=|pipeline:L1 youdo|neon_insert.*youdo' radar_site.log | tail -10")
    print("  grep -c 'Sync API inside asyncio' radar_site.log")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
