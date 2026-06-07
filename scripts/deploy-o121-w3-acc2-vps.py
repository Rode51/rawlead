#!/usr/bin/env python3
"""O121-w3-acc2: tg_monitor join-bootstrap при legacy chat_ids → 0 listen."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_TG_MONITOR = "src/tg_monitor.py"
_LOG = "/opt/rawlead/data/radar_site.log"
_CHAT_IDS = "/opt/rawlead/data/telethon_chat_ids_acc2.txt"


def main() -> int:
    print("=== O121-w3-acc2 deploy: tg_monitor join-bootstrap (legacy filter) ===")
    local = _ROOT / _TG_MONITOR
    remote = "/opt/rawlead/" + _TG_MONITOR
    ssh.upload(local, remote)
    ssh.run(f"chown rawlead:rawlead {remote}")
    print("up", _TG_MONITOR)

    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 5 && "
        "systemctl is-active rawlead-radar && "
        f"grep -E 'join-bootstrap.*acc2|тг:монитор:acc2:.*0 listen' {_LOG} | tail -5 && "
        f"grep 'join:ok account=acc2' {_LOG} | tail -3 && "
        "echo o121_w3_acc2_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    ok = "active" in text and "o121_w3_acc2_ok" in text
    if ok:
        print("DEPLOY OK")
    else:
        print("DEPLOY CHECK — verify manually")

    print()
    print("Ops (если join-bootstrap не появился в логе):")
    print(f"  VPS: truncate {_CHAT_IDS} и restart rawlead-radar")
    print(f"  PowerShell: .venv\\Scripts\\python.exe scripts\\deploy-o121-w3-acc2-vps.py")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
