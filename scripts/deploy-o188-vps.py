#!/usr/bin/env python3
"""O188: TG join wave4 — v3 queue, 10/h per acc, radar_site join logs."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_UPLOADS = (
    "docs/ops/TG_JOIN_QUEUE_v3.csv",
    "src/tg_join_runner.py",
    "src/radar_status.py",
)

_ENV_LINES = {
    "TG_JOIN_QUEUE_CSV": "docs/ops/TG_JOIN_QUEUE_v3.csv",
    "TG_JOIN_MAX_PER_HOUR": "10",
    "TG_JOIN_MAX_PER_DAY": "80",
    "TG_JOIN_MIN_DELAY_SEC": "300",
    "TG_JOIN_MAX_DELAY_SEC": "420",
    "TG_JOIN_IN_TG_MAIN": "1",
    "TELETHON_MONITOR_ACCOUNTS": "acc1,acc2,acc3",
}

_MERGE_QUEUE = r"""
cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
import csv
from pathlib import Path

def norm_link(link: str) -> str:
    return (link or "").strip().rstrip("/").casefold()

v3_path = Path("docs/ops/TG_JOIN_QUEUE_v3.csv")
v2_path = Path("docs/ops/TG_JOIN_QUEUE_v2.csv")
backup = Path("/tmp/tg_join_v3_pre_upload.csv")

done_by_link: dict[str, dict] = {}
for src in (backup, v2_path):
    if not src.is_file():
        continue
    with src.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            link = norm_link(row.get("link", ""))
            if not link:
                continue
            chat_id = (row.get("chat_id") or "").strip()
            status = (row.get("status") or "").strip().casefold()
            if chat_id or status in ("done", "already"):
                row = dict(row)
                row["status"] = "done"
                if chat_id:
                    row["chat_id"] = chat_id
                done_by_link[link] = row

if not v3_path.is_file():
    raise SystemExit("v3 missing")

with v3_path.open(encoding="utf-8", newline="") as fh:
    reader = csv.DictReader(fh)
    fieldnames = reader.fieldnames or []
    rows = list(reader)

merged = 0
for row in rows:
    old = done_by_link.get(norm_link(row.get("link", "")))
    if not old:
        continue
    row["status"] = "done"
    if old.get("chat_id"):
        row["chat_id"] = old["chat_id"]
    merged += 1

with v3_path.open("w", encoding="utf-8", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

pending = sum(1 for r in rows if (r.get("status") or "").strip().casefold() == "pending")
done = sum(1 for r in rows if (r.get("status") or "").strip().casefold() == "done")
print(f"merge_ok merged={merged} pending={pending} done={done}")
PY
"""


def _ensure_env_line(key: str, value: str) -> str:
    safe = value.replace("'", "'\\''")
    return (
        f"grep -q '^{key}=' /opt/rawlead/.env.site && "
        f"sed -i 's|^{key}=.*|{key}={safe}|' /opt/rawlead/.env.site || "
        f"echo '{key}={safe}' >> /opt/rawlead/.env.site"
    )


def _upload_all() -> None:
    for rel in _UPLOADS:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print("up", rel)


def main() -> int:
    print("=== O188 deploy: TG join wave4 ===")
    _, kill_out, _ = ssh.run(
        "pkill -f 'tg_join_queue.py' 2>/dev/null || true; "
        "pkill -f 'python.*tg_join_queue' 2>/dev/null || true; "
        "sleep 1; "
        "pgrep -af tg_join_queue || echo no_stray_tg_join_cli",
        check=False,
    )
    print(kill_out or "")

    ssh.run(
        "test -f /opt/rawlead/docs/ops/TG_JOIN_QUEUE_v3.csv && "
        "cp /opt/rawlead/docs/ops/TG_JOIN_QUEUE_v3.csv /tmp/tg_join_v3_pre_upload.csv || "
        "echo no_v3_backup",
        check=False,
    )
    _upload_all()

    _, merge_out, _ = ssh.run(_MERGE_QUEUE.strip(), check=False)
    print(merge_out or "")

    env_cmd = " && ".join(
        [_ensure_env_line(k, v) for k, v in _ENV_LINES.items()]
        + [
            "grep '^TG_JOIN_QUEUE_CSV=' /opt/rawlead/.env.site",
            "grep '^TG_JOIN_MAX_PER_HOUR=' /opt/rawlead/.env.site",
            "grep '^TELETHON_MONITOR_ACCOUNTS=' /opt/rawlead/.env.site",
            "grep -c ',pending,' /opt/rawlead/docs/ops/TG_JOIN_QUEUE_v3.csv",
            "grep -c ',done,' /opt/rawlead/docs/ops/TG_JOIN_QUEUE_v3.csv",
            "awk -F, 'NR>1{c[$2]++} END{for(a in c) print a,c[a]}' "
            "/opt/rawlead/docs/ops/TG_JOIN_QUEUE_v3.csv | sort",
        ]
    )
    _, env_out, _ = ssh.run(env_cmd, check=False)
    print(env_out or "")

    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 8 && "
        "systemctl is-active rawlead-radar && "
        "grep -c ',pending,' /opt/rawlead/docs/ops/TG_JOIN_QUEUE_v3.csv && "
        "grep 'тг:монитор:acc' /opt/rawlead/data/radar_site.log | tail -5; "
        "echo '--- join radar ---'; "
        "grep 'тг:join:acc' /opt/rawlead/data/radar_site.log | tail -10; "
        "echo '--- tg_join.log ---'; "
        "tail -6 /opt/rawlead/data/tg_join.log 2>/dev/null || true; "
        "echo o188_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text)

    ok = "o188_deploy_ok" in text and "active" in text
    if not ok:
        print("O188 DEPLOY — verify manually")
        return 1

    print("O188 DEPLOY OK — wave4 join in tg_main (first тг:join:acc after tick)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
