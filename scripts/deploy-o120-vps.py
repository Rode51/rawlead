#!/usr/bin/env python3
"""O120-deploy: TG Bot API proxy failover → restart bot-poll + api."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "tg_proxy_pool.py",
    "config.py",
    "telegram_control.py",
    "telegram_notify.py",
    "health_check.py",
)


def main() -> int:
    print("=== O120 deploy: tg_proxy_pool failover ===")
    for name in _FILES:
        local = _ROOT / "src" / name
        remote = f"/opt/rawlead/src/{name}"
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up src/{name}")

    _, out, _ = ssh.run(
        "systemctl restart rawlead-bot-poll rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-bot-poll rawlead-api && "
        "grep -c tg_proxy_pool /opt/rawlead/src/tg_proxy_pool.py && "
        "grep -c tg_http_request /opt/rawlead/src/telegram_control.py && "
        "grep -c tg_http_request /opt/rawlead/src/telegram_notify.py && "
        "journalctl -u rawlead-bot-poll --since '45 sec ago' --no-pager -n 8 && "
        "echo o120_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    ok = text.count("active") >= 2 and "o120_ok" in text
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
