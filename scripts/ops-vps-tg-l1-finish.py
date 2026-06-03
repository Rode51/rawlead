#!/usr/bin/env python3
"""Finish VPS ops: stop long join CLI, L1 fresh replay, restart radar."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

PY_ENV = "PYTHONPATH=/opt/rawlead/src RADAR_PROFILE=site TELEGRAM_BOT_USERNAME=rawlead_bot"
PY = f"cd /opt/rawlead && sudo -u rawlead env {PY_ENV} /opt/rawlead/.venv/bin/python"


def run(label: str, cmd: str) -> None:
    print(f"\n=== {label} ===", flush=True)
    _, out, err = ssh.run(cmd, check=False)
    sys.stdout.buffer.write(((out or "") + (err or "")).encode("utf-8", errors="replace"))


def main() -> int:
    run(
        "Stop join CLI (radar join-bootstrap догонит)",
        "pkill -f 'tg_join_queue.py --account acc2' 2>/dev/null || true; "
        "grep '^TG_JOIN_IN_TG_MAIN=' /opt/rawlead/.env.site; "
        "sed -i 's/^TG_JOIN_IN_TG_MAIN=0/TG_JOIN_IN_TG_MAIN=1/' /opt/rawlead/.env.site; "
        "grep '^TG_JOIN_IN_TG_MAIN=' /opt/rawlead/.env.site",
    )
    run("acc2 chats + pending", "wc -l /opt/rawlead/data/telethon_chat_ids_acc2.txt; "
        "grep -c ',acc2,pending,' /opt/rawlead/docs/ops/TG_JOIN_QUEUE_v2.csv || true")
    run(
        "L1 backlog counts",
        f"{PY} -c \"import sys;sys.path.insert(0,'/opt/rawlead/src');"
        "from config import load_radar_env,load_config;"
        "from pg_storage import pg_storage_from_config;"
        "load_radar_env();pg=pg_storage_from_config(load_config());e=[];"
        "print('total',pg.count_leads_missing_l1(e));"
        "print('48h',pg.count_leads_missing_l1_recent(48,e));"
        "print('ids',','.join(str(i) for i in pg.l1_backlog_sample_ids(limit=8,errors=e)))\"",
    )
    run(
        "Replay L1 (8 newest sample ids)",
        f"{PY} -c \"import subprocess,sys;sys.path.insert(0,'/opt/rawlead/src');"
        "from config import load_radar_env,load_config;"
        "from pg_storage import pg_storage_from_config;"
        "load_radar_env();pg=pg_storage_from_config(load_config());"
        "ids=pg.l1_backlog_sample_ids(limit=8);"
        "print('replay',ids);"
        "subprocess.run(['/opt/rawlead/.venv/bin/python',"
        "'/opt/rawlead/scripts/replay_neon_lite_site.py','--profile','site',"
        "'--lead-ids',','.join(str(i) for i in ids),'--limit',str(len(ids) or 1)])\"",
    )
    run(
        "tg_bot_start acc2+acc3",
        f"{PY} /opt/rawlead/scripts/tg_bot_start.py --account acc2 --force; "
        f"{PY} /opt/rawlead/scripts/tg_bot_start.py --account acc3 --force",
    )
    run(
        "Start radar",
        "systemctl start rawlead-radar; sleep 4; "
        "systemctl is-active rawlead-radar rawlead-api; "
        "grep -E 'join-bootstrap|конвейер:L1' /opt/rawlead/data/radar_site.log 2>/dev/null | tail -6 || true",
    )
    run("tg_join tail", "tail -8 /opt/rawlead/data/tg_join.log")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
