#!/usr/bin/env python3
"""O55: sync src + restart rawlead-api + rawlead-bot-poll."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== O55 API + bot-poll deploy ===")
    n = ssh.sync_project()
    print(f"synced {n} files -> /opt/rawlead")
    ssh.run(
        r"find /opt/rawlead/deploy -name '*.sh' -exec sed -i 's/\r$//' {} \; && "
        "chmod +x /opt/rawlead/deploy/*.sh"
    )
    ssh.run("chown -R rawlead:rawlead /opt/rawlead/src /opt/rawlead/scripts /opt/rawlead/tests")
    _, out, _ = ssh.run(
        "grep -c ensure_bot_polling_mode /opt/rawlead/src/telegram_control.py",
        check=False,
    )
    print("ensure_bot_polling_mode:", (out or "").strip())
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-bot-poll && sleep 3 && "
        "systemctl is-active rawlead-api rawlead-bot-poll",
        check=False,
    )
    print("services:", (out or "").strip())
    _, code, _ = ssh.run(
        "curl -s -o /dev/null -w '%{http_code}' 'http://127.0.0.1:8000/v1/feed?limit=1'",
        check=False,
    )
    print("feed HTTP:", (code or "").strip())
    _, wh, _ = ssh.run(
        r"cd /opt/rawlead && python3 -c \"import sys; sys.path.insert(0,'src'); "
        "from config import load_config, load_radar_env, apply_profile_argv; "
        "from telegram_control import ensure_bot_polling_mode; "
        "apply_profile_argv(); load_radar_env(); c=load_config(); "
        "print(';'.join(ensure_bot_polling_mode(c)))\"",
        check=False,
    )
    print("webhook check:", (wh or "").strip())
    active = (out or "").count("active") >= 2
    ok = active and (code or "").strip() == "200"
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
