#!/usr/bin/env python3

"""One-shot VPS: tg_monitor join-bootstrap deploy, acc2 join, L1 drain, fresh L1."""

from __future__ import annotations



import sys

from pathlib import Path



_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(_ROOT / "scripts"))

import deploy_vps_ssh as ssh  # noqa: E402



PY_ENV = (

    "PYTHONPATH=/opt/rawlead/src RADAR_PROFILE=site "

    "TELEGRAM_BOT_USERNAME=rawlead_bot"

)

PY = f"cd /opt/rawlead && sudo -u rawlead env {PY_ENV} /opt/rawlead/.venv/bin/python"





def run(label: str, cmd: str) -> None:

    print(f"\n=== {label} ===", flush=True)

    _, out, err = ssh.run(cmd, check=False)

    text = (out or "") + (err or "")

    sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))





def main() -> int:

    local_tg = _ROOT / "src" / "tg_monitor.py"

    remote_tg = "/opt/rawlead/src/tg_monitor.py"
    ssh.upload(local_tg, remote_tg)
    ssh.run(f"chown rawlead:rawlead {remote_tg}")
    print("uploaded src/tg_monitor.py", flush=True)



    run("L1_BACKLOG_DRAIN", "grep -E '^L1_BACKLOG_DRAIN=' /opt/rawlead/.env.site 2>/dev/null || echo '(unset)'")

    run(

        "Enable L1_BACKLOG_DRAIN",

        "grep -q '^L1_BACKLOG_DRAIN=' /opt/rawlead/.env.site 2>/dev/null && "

        "sed -i 's/^L1_BACKLOG_DRAIN=.*/L1_BACKLOG_DRAIN=1/' /opt/rawlead/.env.site || "

        "echo 'L1_BACKLOG_DRAIN=1' >> /opt/rawlead/.env.site",

    )

    run("acc2 pending", "grep -c ',acc2,pending,' /opt/rawlead/docs/ops/TG_JOIN_QUEUE_v2.csv || true")

    run(

        "Stop radar",

        "systemctl stop rawlead-radar; sleep 3; "

        "pkill -9 -f tg_main.py 2>/dev/null || true; "

        "pkill -9 -f run-radar-site 2>/dev/null || true; sleep 2; "

        "systemctl is-active rawlead-radar 2>/dev/null || echo stopped",

    )

    run(

        "acc2 join (TG_JOIN_IN_TG_MAIN=0 in .env.site)",

        "sed -i 's/^TG_JOIN_IN_TG_MAIN=1/TG_JOIN_IN_TG_MAIN=0/' /opt/rawlead/.env.site; "

        f"{PY} /opt/rawlead/scripts/tg_join_queue.py --account acc2 --max-per-hour 1; "

        "sed -i 's/^TG_JOIN_IN_TG_MAIN=0/TG_JOIN_IN_TG_MAIN=1/' /opt/rawlead/.env.site",

    )

    run(

        "tg_bot_start acc2+acc3",

        f"{PY} /opt/rawlead/scripts/tg_bot_start.py --account acc2 --force; "

        f"{PY} /opt/rawlead/scripts/tg_bot_start.py --account acc3 --force",

    )

    run(

        "L1 recent sample (created_at DESC)",

        f"{PY} -c \""

        "import sys; sys.path.insert(0,'/opt/rawlead/src'); "

        "from config import load_radar_env, load_config; "

        "from pg_storage import pg_storage_from_config; "

        "load_radar_env(); cfg=load_config(); pg=pg_storage_from_config(cfg); "

        "err=[]; "

        "print('backlog_total', pg.count_leads_missing_l1(err)); "

        "print('backlog_48h', pg.count_leads_missing_l1_recent(48, err)); "

        "ids=pg.l1_backlog_sample_ids(limit=12, errors=err); "

        "print('sample_ids', ','.join(str(i) for i in ids))\"",

    )

    run(

        "Replay L1 for sample ids",

        f"{PY} -c \""

        "import subprocess, sys; sys.path.insert(0,'/opt/rawlead/src'); "

        "from config import load_radar_env, load_config; "

        "from pg_storage import pg_storage_from_config; "

        "load_radar_env(); cfg=load_config(); pg=pg_storage_from_config(cfg); "

        "ids=pg.l1_backlog_sample_ids(limit=12); arg=','.join(str(i) for i in ids); "

        "sys.exit(0) if not ids else subprocess.run("

        "['/opt/rawlead/.venv/bin/python','/opt/rawlead/scripts/replay_neon_lite_site.py',"

        "'--profile','site','--lead-ids',arg,'--limit',str(len(ids))], check=False)\"",

    )

    run("Start radar", "systemctl start rawlead-radar && sleep 4 && systemctl is-active rawlead-radar rawlead-api")

    run("chat_ids acc2", "wc -l /opt/rawlead/data/telethon_chat_ids_acc2.txt 2>/dev/null || echo 'no file'")

    run("acc2 pending after", "grep -c ',acc2,pending,' /opt/rawlead/docs/ops/TG_JOIN_QUEUE_v2.csv || true")

    run("tg_join log", "tail -15 /opt/rawlead/data/tg_join.log 2>/dev/null || echo no log")

    run("radar log L1", "grep -E 'конвейер:L1|join-bootstrap|acc2 join' /opt/rawlead/data/radar_site.log 2>/dev/null | tail -8 || true")

    return 0





if __name__ == "__main__":

    raise SystemExit(main())

