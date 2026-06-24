#!/usr/bin/env python3
"""YOUDO-CLICK-RETRY + SP-STABLE (sticky worker + click-through)."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)

_UPLOADS = (
    ("scripts/youdo_sticky_worker.py", "/opt/rawlead/scripts/youdo_sticky_worker.py"),
    ("src/youdo_parser.py", "/opt/rawlead/src/youdo_parser.py"),
    ("src/exchange_browser_fetch.py", "/opt/rawlead/src/exchange_browser_fetch.py"),
    ("src/lead_pipeline.py", "/opt/rawlead/src/lead_pipeline.py"),
)

_BACKUP_DIR = "/opt/rawlead/data/backups"
_STAMP = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
_BACKUP_TAR = f"{_BACKUP_DIR}/pre_click_retry_{_STAMP}.tar.gz"


def _backup_remote() -> None:
    files = " ".join(remote for _, remote in _UPLOADS)
    cmd = (
        f"mkdir -p {_BACKUP_DIR} && "
        f"tar -czf {_BACKUP_TAR} {files} && "
        f"chown rawlead:rawlead {_BACKUP_TAR} && "
        f"ls -la {_BACKUP_TAR}"
    )
    _, out, _ = ssh.run(cmd, check=False)
    print(out or "")


def _verify_remote() -> str:
    remote = r"""
grep -c 'youdo_detail_pending' /opt/rawlead/src/lead_pipeline.py
grep -c 'click_summary' /opt/rawlead/src/youdo_parser.py
grep -c 'click_through_details' /opt/rawlead/scripts/youdo_sticky_worker.py
grep -c 'youdo_click_through_details' /opt/rawlead/src/exchange_browser_fetch.py
systemctl is-active rawlead-radar
grep 'fetch:youdo' /opt/rawlead/data/radar_site.log | tail -3
"""
    _, out, _ = ssh.run(remote.strip(), check=False)
    return (out or "").replace("\r\n", "\n")


def main() -> int:
    print(f"backup -> {_BACKUP_TAR}")
    _backup_remote()

    for local, remote in _UPLOADS:
        ssh.upload(_ROOT / local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"uploaded {local}")

    _, rst, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 8 && systemctl is-active rawlead-radar",
        check=False,
    )
    print(rst or "")
    print(_verify_remote())

    ok = "active" in (rst or "")
    if not ok:
        print("FAIL - rawlead-radar not active")
        return 1

    print("OK - click-retry + SP-STABLE deployed")
    print(f"ROLLBACK: tar -xzf {_BACKUP_TAR} -C / && systemctl restart rawlead-radar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
