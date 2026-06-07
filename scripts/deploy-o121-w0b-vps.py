#!/usr/bin/env python3
"""O121-w0b: /ops/ section «Боты» — @rawlead_bot + @FLPARSINGBOT restart."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = ("src/owner_admin.py",)


def main() -> int:
    print("=== O121-w0b deploy: ops bots section ===")
    remotes: list[str] = []
    for rel in _FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "grep -c '@rawlead_bot' /opt/rawlead/src/owner_admin.py && "
        "grep -c '@FLPARSINGBOT' /opt/rawlead/src/owner_admin.py && "
        "grep -c 'Перезапуск обоих ботов' /opt/rawlead/src/owner_admin.py && "
        "grep -c 'flparsing-bot' /opt/rawlead/src/owner_admin.py && "
        "cd /opt/rawlead && sudo -u rawlead .venv/bin/python -c "
        "\"import os,sys; sys.path.insert(0,'src'); "
        "from dotenv import load_dotenv; load_dotenv('.env'); "
        "from owner_admin import _bots_snapshot; "
        "bots=_bots_snapshot(); "
        "print('bots', len(bots), bots[0]['username'], bots[1]['username'])\" && "
        "echo o121_w0b_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    ok = (
        "active" in text
        and "o121_w0b_ok" in text
        and "@rawlead_bot" in text
        and "@FLPARSINGBOT" in text
    )
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
