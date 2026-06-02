from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from config import load_config
from health_check import send_owner_text
from pg_storage import pg_storage_from_config
from radar_cycle_log import load_cycle_summary
from proxy_exchange_probe import probe_exchange_pools
from storage import storage_from_config

_KEY_LAST_ALERT = "watchdog_last_alert_at"
_KEY_LAST_STATUS = "watchdog_last_status"


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _should_alert(storage, cooldown_sec: int) -> bool:
    raw = storage.get_setting(_KEY_LAST_ALERT, "0").strip()
    try:
        last = float(raw)
    except ValueError:
        last = 0.0
    return (time.time() - last) >= cooldown_sec


def _mark_alert(storage) -> None:
    storage.set_setting(_KEY_LAST_ALERT, str(int(time.time())))


def _status_to_json(status: dict) -> str:
    return json.dumps(status, ensure_ascii=False, sort_keys=True)


def _maybe_restart(gap_min: int, restart_gap_min: int, auto_restart: bool) -> str:
    if not auto_restart or gap_min < restart_gap_min:
        return ""
    try:
        proc = subprocess.run(
            ["systemctl", "restart", "rawlead-radar"],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception as exc:
        return f"restart error: {exc}"
    if proc.returncode != 0:
        return f"restart failed: {(proc.stderr or proc.stdout or '').strip()[:200]}"
    return "restart ok"


def main() -> int:
    cfg = load_config()
    storage = storage_from_config(cfg)
    pg = pg_storage_from_config(cfg)
    if pg is None or not pg.enabled:
        return 1

    cycle_gap_min = _env_int("WATCHDOG_CYCLE_GAP_MIN", 15)
    insert_gap_min = _env_int("WATCHDOG_INSERT_GAP_MIN", 20)
    l1_backlog_limit = _env_int("WATCHDOG_L1_BACKLOG", 120)
    restart_gap_min = _env_int("WATCHDOG_RESTART_GAP_MIN", 25)
    auto_restart = os.environ.get("WATCHDOG_AUTO_RESTART", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )
    cooldown = _env_int("WATCHDOG_ALERT_COOLDOWN_SEC", 1800)

    summary = load_cycle_summary(storage)
    ops = pg.ingest_ops_snapshot()
    backlog = pg.count_leads_missing_l1_recent(hours=48)
    pools = probe_exchange_pools()

    gaps = {
        src: int((ops.get(src) or {}).get("last_insert_gap_sec", 0) // 60)
        for src in ("fl", "kwork")
    }
    cycle_gap = 0
    if summary and summary.ts:
        s = summary.ts.strip().replace(" UTC", "")
        epoch = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                epoch = datetime.strptime(s, fmt).replace(tzinfo=timezone.utc).timestamp()
                break
            except ValueError:
                continue
        if epoch:
            cycle_gap = int((time.time() - epoch) // 60)

    reasons: list[str] = []
    if cycle_gap > cycle_gap_min:
        reasons.append(f"cycle_gap={cycle_gap}m>{cycle_gap_min}m")
    for src in ("fl", "kwork"):
        if gaps[src] > insert_gap_min:
            reasons.append(f"{src}_insert_gap={gaps[src]}m>{insert_gap_min}m")
    if backlog > l1_backlog_limit:
        reasons.append(f"l1_backlog={backlog}>{l1_backlog_limit}")
    for src in ("fl", "kwork"):
        pool = pools.get(src, {"alive": 0, "total": 0})
        if pool["total"] > 0 and pool["alive"] <= 0:
            reasons.append(f"{src}_proxy_alive=0/{pool['total']}")

    status = {
        "cycle_gap_min": cycle_gap,
        "insert_gap_min": gaps,
        "l1_backlog": backlog,
        "proxy_pools": pools,
        "reasons": reasons,
    }

    previous = storage.get_setting(_KEY_LAST_STATUS, "").strip()
    current = _status_to_json(status)
    was_bad = bool(previous and '"reasons": []' not in previous)
    now_bad = bool(reasons)
    storage.set_setting(_KEY_LAST_STATUS, current)

    if now_bad:
        if _should_alert(storage, cooldown):
            restart_note = _maybe_restart(
                max([cycle_gap, gaps["fl"], gaps["kwork"]]),
                restart_gap_min,
                auto_restart,
            )
            text = (
                "⚠️ RawLead ingest watchdog\n"
                + "\n".join(f"- {r}" for r in reasons[:8])
                + f"\n- proxy: fl {pools['fl']['alive']}/{pools['fl']['total']},"
                + f" kwork {pools['kwork']['alive']}/{pools['kwork']['total']}"
            )
            if restart_note:
                text += f"\n- {restart_note}"
            send_owner_text(cfg, text)
            _mark_alert(storage)
    elif was_bad:
        send_owner_text(
            cfg,
            "✅ RawLead ingest recovered\n"
            f"- cycle_gap={cycle_gap}m\n"
            f"- fl gap={gaps['fl']}m, kwork gap={gaps['kwork']}m\n"
            f"- backlog={backlog}",
        )

    print(json.dumps(status, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
