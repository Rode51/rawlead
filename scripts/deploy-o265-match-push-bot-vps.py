#!/usr/bin/env python3
"""O265 + O265b: match_push 4-btn keyboard + push_nope + draft rate limit + bot callbacks."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_SRC_FILES = (
    "src/match_push.py",
    "src/api_server.py",
    "src/telegram_control.py",
)


def main() -> int:
    print("=== O265+O265b deploy: match_push + api_server + telegram_control ===")
    remotes: list[str] = []
    for rel in _SRC_FILES:
        local = _ROOT / rel
        if not local.is_file():
            print("MISSING", rel)
            return 1
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(local, remote)
        remotes.append(remote)
        print("up", rel)

    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-bot-poll && sleep 4 && "
        "systemctl is-active rawlead-api rawlead-bot-poll && "
        "curl -sf http://127.0.0.1:8000/health; echo && "
        "grep -q 'Не моё' /opt/rawlead/src/match_push.py && "
        "grep -q draft_rate_limit_retry_after /opt/rawlead/src/match_push.py && "
        "grep -q push_nope /opt/rawlead/src/api_server.py && "
        "grep -q handle_tg_nope_callback /opt/rawlead/src/telegram_control.py && "
        "echo o265_ok",
        check=False,
    )
    print(out or "")
    text = out or ""
    ok = "active" in text and "o265_ok" in text
    if ok:
        print("DEPLOY OK - smoke: next match push -> 4 buttons, nope/draft callbacks")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
