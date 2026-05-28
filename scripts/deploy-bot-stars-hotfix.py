#!/usr/bin/env python3
"""Hotfix: /start + /pay для admin chat + Stars handlers."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = ("src/telegram_control.py", "src/stars_billing.py")


def main() -> int:
    for rel in _FILES:
        local = _ROOT / rel
        ssh.upload(local, f"/opt/rawlead/{rel}")
        print("up", rel)
    _, out, _ = ssh.run(
        "chown rawlead:rawlead /opt/rawlead/src/telegram_control.py "
        "/opt/rawlead/src/stars_billing.py && "
        "systemctl restart rawlead-bot-poll && sleep 2 && "
        "systemctl is-active rawlead-bot-poll && "
        "grep STARS_ /opt/rawlead/.env.site; "
        "grep DATABASE_URL /opt/rawlead/.env | head -1",
        check=False,
    )
    print(out)
    return 0 if "active" in out else 1


if __name__ == "__main__":
    raise SystemExit(main())
