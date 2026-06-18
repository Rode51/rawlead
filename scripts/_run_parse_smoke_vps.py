#!/usr/bin/env python3
"""Run exchange_parse_smoke on VPS."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

REMOTE = (
    "cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src "
    ".venv/bin/python scripts/exchange_parse_smoke.py 2>&1"
)


def main() -> int:
    ssh.upload(
        Path(__file__).resolve().parents[1] / "scripts" / "exchange_parse_smoke.py",
        "/opt/rawlead/scripts/exchange_parse_smoke.py",
    )
    _, out, err = ssh.run(REMOTE, check=False)
    print(out or err or "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
