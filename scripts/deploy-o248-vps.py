#!/usr/bin/env python3
"""O248: TG wave5 — v4 queue CSV + multi-queue join + radar restart."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    ("docs/ops/TG_JOIN_QUEUE_v4.csv", "/opt/rawlead/docs/ops/TG_JOIN_QUEUE_v4.csv"),
    ("src/tg_join_lib.py", "/opt/rawlead/src/tg_join_lib.py"),
    ("src/tg_join_runner.py", "/opt/rawlead/src/tg_join_runner.py"),
    ("src/config.py", "/opt/rawlead/src/config.py"),
    ("src/public_feed.py", "/opt/rawlead/src/public_feed.py"),
    ("src/tg_monitor.py", "/opt/rawlead/src/tg_monitor.py"),
    ("scripts/tg_queue_import.py", "/opt/rawlead/scripts/tg_queue_import.py"),
)


def main() -> int:
    print("=== O248 deploy: TG wave5 v4 queue + multi-queue join ===")
    _, kill_out, _ = ssh.run(
        "pkill -f 'tg_join_queue.py' 2>/dev/null || true; "
        "pkill -f 'python.*tg_join_queue' 2>/dev/null || true; "
        "sleep 1; "
        "pgrep -af tg_join_queue || echo no_stray_tg_join_cli",
        check=False,
    )
    print(kill_out or "")

    remotes: list[str] = []
    for rel, remote in _UPLOADS:
        local = _ROOT / rel
        if not local.is_file():
            print("MISSING", rel)
            return 1
        ssh.upload(local, remote)
        remotes.append(remote)
        print("up", rel)

    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    verify = (
        "grep -c 'TG_JOIN_QUEUE_v4.csv' /opt/rawlead/src/tg_join_lib.py && "
        "grep -c 'ordered_join_queue_paths' /opt/rawlead/src/tg_join_runner.py && "
        "grep -c 'TG_JOIN_QUEUE_v4.csv' /opt/rawlead/src/config.py && "
        "grep -c 'TG_JOIN_QUEUE_v4.csv' /opt/rawlead/src/public_feed.py && "
        "grep -c ',pending,' /opt/rawlead/docs/ops/TG_JOIN_QUEUE_v4.csv"
    )
    _, pre_out, _ = ssh.run(verify, check=False)
    print(pre_out or "")

    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 10 && "
        "systemctl is-active rawlead-radar && "
        "grep -c ',pending,' /opt/rawlead/docs/ops/TG_JOIN_QUEUE_v4.csv && "
        "grep -c 'ordered_join_queue_paths' /opt/rawlead/src/tg_join_lib.py && "
        "echo '--- join radar ---'; "
        "grep 'тг:join:acc' /opt/rawlead/data/radar_site.log | tail -8; "
        "echo '--- tg_join.log ---'; "
        "tail -8 /opt/rawlead/data/tg_join.log 2>/dev/null || true; "
        "echo o248_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text.encode("ascii", errors="replace").decode("ascii"))

    ok = (
        "o248_deploy_ok" in text
        and "active" in text
        and "305" in (pre_out or text)
    )
    if not ok:
        print("O248 DEPLOY — verify manually")
        return 1

    print("O248 DEPLOY OK - v4 305 pending - join drains v2->v3->v4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
