#!/usr/bin/env python3
"""O180: all-web delist coverage + backlog throughput."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    "src/delist_checker.py",
    "src/exchange_delist.py",
    "src/fl_parser.py",
    "src/kwork_parser.py",
    "src/youdo_parser.py",
    "src/freelance_ru_parser.py",
    "src/freelancejob_parser.py",
    "src/pchyol_parser.py",
    "scripts/run-delist-backfill.py",
)


def main() -> int:
    print("=== O180 deploy: all-web delist + backfill script ===")
    remotes: list[str] = []
    for rel in _UPLOADS:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "grep -c check_source_page_gone /opt/rawlead/src/exchange_delist.py && "
        "grep -c check_project_page_gone /opt/rawlead/src/youdo_parser.py && "
        "grep -c DELIST_BATCH_LIMIT /opt/rawlead/src/delist_checker.py && "
        "test -f /opt/rawlead/scripts/run-delist-backfill.py && "
        "systemctl restart rawlead-radar && sleep 4 && systemctl is-active rawlead-radar && "
        "echo o180_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text)
    if "o180_deploy_ok" not in text or "active" not in text:
        print("O180 DEPLOY CHECK FAILED")
        return 1
    print("O180 DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
