#!/usr/bin/env python3
"""O257: Parser stability audit + fixes — upload src + scripts, restart radar, run probe.

Uploads:
  src/fl_parser.py            — auto httpx fallback, restart loop fix, pipeline logs
  src/exchange_browser_fetch.py — fl_hard_reset set_restart_source, YouDo RU dead skip
  src/kwork_parser.py         — fetch:kwork outcome= log
  src/youdo_parser.py         — fetch:youdo outcome= + reason= in fetch_end

Scripts:
  scripts/audit_parser_processes_vps.py
  scripts/probe_parsers_health_vps.py

After restart: runs probe and prints last 5 fetch:* outcome= lines.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_SRC_FILES = (
    "src/fl_parser.py",
    "src/exchange_browser_fetch.py",
    "src/kwork_parser.py",
    "src/youdo_parser.py",
)
_SCRIPT_FILES = (
    "scripts/audit_parser_processes_vps.py",
    "scripts/probe_parsers_health_vps.py",
)
_REMOTE_BASE = "/opt/rawlead"


def _upload(files: tuple[str, ...]) -> list[str]:
    remotes: list[str] = []
    for rel in files:
        remote = f"{_REMOTE_BASE}/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print(f"  up  {rel}")
    return remotes


def main() -> int:
    print("=== O257 deploy: parser stability audit + fixes ===")

    print("\n[1/4] Uploading src files...")
    src_remotes = _upload(_SRC_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(src_remotes))

    print("\n[2/4] Uploading scripts...")
    scr_remotes = _upload(_SCRIPT_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(scr_remotes))

    print("\n[3/4] Restarting rawlead-radar...")
    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 8 && "
        "systemctl is-active rawlead-radar",
        check=False,
    )
    radar_active = "active" in (out or "")
    print(f"  radar: {'active ✓' if radar_active else 'NOT active ✗'}")

    print("\n[4/4] Running probe + log check...")
    _, out2, _ = ssh.run(
        f"python3 {_REMOTE_BASE}/scripts/probe_parsers_health_vps.py --json && "
        f"echo '--- last fetch:* outcome= lines ---' && "
        f"grep 'fetch:.*outcome=' {_REMOTE_BASE}/data/radar_site.log 2>/dev/null | tail -5 && "
        f"echo o257_deploy_ok",
        check=False,
    )
    print((out2 or "").strip())

    ok = "o257_deploy_ok" in (out2 or "") and radar_active
    if ok:
        print("\nDEPLOY OK")
        print("Watch for: fetch:fl outcome=ok  /  fetch:fl stage=fallback httpx outcome=ok")
        return 0
    print("\nDEPLOY CHECK — verify manually:")
    print("  systemctl is-active rawlead-radar")
    print(f"  grep 'fetch:.*outcome=' {_REMOTE_BASE}/data/radar_site.log | tail -10")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
