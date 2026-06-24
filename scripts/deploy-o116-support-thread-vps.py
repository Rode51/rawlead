#!/usr/bin/env python3
"""O116: support thread lookup fix + TG reply DB — api + bot-poll."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = ("support_tickets.py", "api_server.py", "telegram_control.py")


def main() -> int:
    print("=== O116 support thread hotfix ===")
    for name in _FILES:
        local = _ROOT / "src" / name
        remote = f"/opt/rawlead/src/{name}"
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print("up", name)

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-bot-poll && sleep 3 && "
        "systemctl is-active rawlead-api && systemctl is-active rawlead-bot-poll && "
        "grep -c 'guest_token = %s' /opt/rawlead/src/support_tickets.py && "
        "grep -c require_database_url /opt/rawlead/src/telegram_control.py && "
        "curl -sS -o /dev/null -w 'health:%{http_code}\\n' https://api.rawlead.ru/health",
        check=False,
    )
    print(out or "")
    return 0 if "active" in (out or "") and "health:200" in (out or "") else 1


if __name__ == "__main__":
    raise SystemExit(main())
