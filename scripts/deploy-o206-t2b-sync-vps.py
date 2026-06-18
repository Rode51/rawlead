#!/usr/bin/env python3
"""O206-t2b: multi-queue chat_ids sync + radar restart + listen audit."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    ("src/config.py", "/opt/rawlead/src/config.py"),
    ("scripts/tg_sync_chat_ids.py", "/opt/rawlead/scripts/tg_sync_chat_ids.py"),
    ("scripts/tg_join_listen_audit.py", "/opt/rawlead/scripts/tg_join_listen_audit.py"),
    ("docs/ops/TG_JOIN_QUEUE.csv", "/opt/rawlead/docs/ops/TG_JOIN_QUEUE.csv"),
    ("docs/ops/TG_JOIN_QUEUE_v2.csv", "/opt/rawlead/docs/ops/TG_JOIN_QUEUE_v2.csv"),
    ("docs/ops/TG_JOIN_QUEUE_v3.csv", "/opt/rawlead/docs/ops/TG_JOIN_QUEUE_v3.csv"),
)


def main() -> int:
    print("=== O206-t2b deploy: sync chat_ids from all queue CSVs ===")
    remotes: list[str] = []
    for rel, remote in _UPLOADS:
        local = _ROOT / rel
        if not local.is_file():
            print("skip missing", rel)
            continue
        ssh.upload(local, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    sync_cmd = (
        "cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src "
        ".venv/bin/python scripts/tg_sync_chat_ids.py --account all"
    )
    audit_cmd = (
        "cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src "
        ".venv/bin/python scripts/tg_join_listen_audit.py "
        "--log /opt/rawlead/data/radar_site.log"
    )
    _, out, _ = ssh.run(
        f"{sync_cmd} && "
        "systemctl restart rawlead-radar && sleep 12 && "
        "systemctl is-active rawlead-radar && "
        f"{audit_cmd} && "
        "echo t2b_ok",
        check=False,
    )
    text = out or ""
    print(text.encode("ascii", errors="replace").decode("ascii"))
    ok = "t2b_ok" in text and "active" in text and '"ok": true' in text
    if ok:
        print("O206-t2b DEPLOY OK — listen audit ok:true")
        return 0
    if '"ok": false' in text:
        print("O206-t2b SYNC RAN but audit still ok:false — check gaps in JSON above")
    print("O206-t2b DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
