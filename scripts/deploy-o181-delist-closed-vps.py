#!/usr/bin/env python3
"""O181: YouDo closed-for-responses markers + delisted purge pass."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    "src/youdo_parser.py",
    "scripts/purge_old_leads.py",
    "scripts/run-delist-backfill.py",
    "deploy/systemd/rawlead-purge-leads.service",
)


def main() -> int:
    print("=== O181 deploy: YouDo closed markers + purge_delisted ===")
    remotes: list[str] = []
    for rel in _UPLOADS:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "grep -c 'закрыто для откликов' /opt/rawlead/src/youdo_parser.py && "
        "grep -c purge_delisted /opt/rawlead/scripts/purge_old_leads.py && "
        "cp /opt/rawlead/deploy/systemd/rawlead-purge-leads.service /etc/systemd/system/ && "
        "systemctl daemon-reload && "
        "systemctl restart rawlead-radar && sleep 4 && systemctl is-active rawlead-radar && "
        "echo o181_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text)
    if "o181_deploy_ok" not in text or "active" not in text:
        print("O181 DEPLOY CHECK FAILED")
        return 1
    print("O181 DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
