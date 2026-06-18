#!/usr/bin/env python3
"""O213+O212: Kwork pages 1-3 + exchange-safe filter + ops log truth — radar + API."""
from __future__ import annotations

import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_RADAR_FILES = (
    "src/kwork_parser.py",
    "src/filters.py",
    "src/tg_monitor.py",
)
_API_FILES = (
    "src/owner_admin.py",
    "src/static/ops-pult.js",
)


def _upload(files: tuple[str, ...]) -> list[str]:
    remotes: list[str] = []
    for rel in files:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    return remotes


def _wait_kwork_pages(max_wait_sec: int = 1320, poll_sec: int = 30) -> str:
    """Poll radar log until listing:kwork shows pages=2-3 (up to ~2 radar cycles)."""
    deadline = time.time() + max_wait_sec
    last = ""
    while time.time() < deadline:
        _, out, _ = ssh.run(
            "grep 'listing:kwork' /opt/rawlead/data/radar_site.log | tail -3",
            check=False,
        )
        last = (out or "").strip()
        print("--- listing:kwork tail ---")
        print(last or "(empty)")
        if "pages=" in last and any(f"pages={n}" in last for n in (2, 3)):
            return last
        time.sleep(poll_sec)
    return last


def main() -> int:
    print("=== O213+O212 deploy: radar + API ===")
    ssh.run("mkdir -p /opt/rawlead/src/static && chown rawlead:rawlead /opt/rawlead/src/static")
    remotes = _upload(_RADAR_FILES + _API_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    _, pre, _ = ssh.run(
        "grep -c KWORK_MAX_PAGES /opt/rawlead/src/kwork_parser.py && "
        "grep -c EXCHANGE_SAFE_STOPS /opt/rawlead/src/filters.py && "
        "grep -c skip_entity /opt/rawlead/src/tg_monitor.py && "
        "grep -c today_new_ids /opt/rawlead/src/owner_admin.py && "
        "echo o213_o212_upload_ok",
        check=False,
    )
    print(pre.strip())

    _, radar_out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 4 && "
        "systemctl is-active rawlead-radar && echo radar_active",
        check=False,
    )
    print(radar_out.strip())
    if "active" not in (radar_out or ""):
        print("RADAR RESTART FAILED")
        return 1

    print("Waiting for 2 kwork cycles (poll listing:kwork pages=2-3)...")
    kwork_tail = _wait_kwork_pages()
    ok_pages = "pages=" in kwork_tail and any(f"pages={n}" in kwork_tail for n in (2, 3))

    _, skip_out, _ = ssh.run(
        "grep skip_entity /opt/rawlead/data/radar_site.log | tail -3",
        check=False,
    )
    print("--- skip_entity tail ---")
    print((skip_out or "").strip())
    bad_ids = "ids=[" in (skip_out or "")

    _, api_out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-api && "
        "curl -sf -o /dev/null -w 'ops_root=%{http_code}\\n' "
        "http://127.0.0.1:8000/ops/ && echo api_active",
        check=False,
    )
    print(api_out.strip())

    ok_api = "active" in (api_out or "") and "ops_root=200" in (api_out or "")
    if ok_pages and not bad_ids and ok_api:
        print("DEPLOY OK — O213 pages + O212 log/ops on prod")
        return 0

    print("DEPLOY CHECK — partial:")
    print(f"  kwork pages=2-3: {'OK' if ok_pages else 'WAIT/MISSING'}")
    print(f"  skip_entity no ids dump: {'OK' if not bad_ids else 'FAIL'}")
    print(f"  api active: {'OK' if ok_api else 'FAIL'}")
    return 1 if not (ok_pages and not bad_ids and ok_api) else 0


if __name__ == "__main__":
    raise SystemExit(main())
