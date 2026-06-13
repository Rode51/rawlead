#!/usr/bin/env python3
"""Hotfix: YouDo Playwright dedicated thread (2026-06-10 ticket)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_REMOTE = "/opt/rawlead/src/exchange_browser_fetch.py"
_LOCAL = _ROOT / "src" / "exchange_browser_fetch.py"


def main() -> int:
    ssh.upload(_LOCAL, _REMOTE)
    ssh.run(f"chown rawlead:rawlead {_REMOTE}")
    print(f"up {_LOCAL.relative_to(_ROOT)}")
    _, out, _ = ssh.run(
        "grep -c rawlead-playwright /opt/rawlead/src/exchange_browser_fetch.py && "
        "systemctl restart rawlead-radar && sleep 3 && systemctl is-active rawlead-radar",
        check=False,
    )
    print(out or "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
