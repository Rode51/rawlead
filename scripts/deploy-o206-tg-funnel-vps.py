#!/usr/bin/env python3
"""O206: TG interest set + chat_id resolve + audit scripts."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_RADAR_FILES = (
    "src/tg_monitor.py",
    "src/public_feed.py",
)
_SCRIPT_FILES = (
    "scripts/probe_tg_test_group_membership.py",
    "scripts/tg_join_listen_audit.py",
    "scripts/tg_funnel_audit.py",
)


def _upload(files: tuple[str, ...]) -> list[str]:
    remotes: list[str] = []
    for rel in files:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    return remotes


def main() -> int:
    print("=== O206 deploy: TG funnel + interest set ===")
    remotes = _upload(_RADAR_FILES + _SCRIPT_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 5 && "
        "systemctl is-active rawlead-radar && "
        "grep -c chat_in_tg_interest_set /opt/rawlead/src/tg_monitor.py && "
        "grep -c chat_in_tg_interest_set /opt/rawlead/src/public_feed.py && "
        "grep -c _resolve_message_chat_id /opt/rawlead/src/tg_monitor.py && "
        "test -f /opt/rawlead/scripts/tg_funnel_audit.py && "
        "cd /opt/rawlead && .venv/bin/python scripts/tg_join_listen_audit.py "
        "--log data/radar_site.log --out data/tg_join_listen_audit.json 2>&1 | tail -5 && "
        "cd /opt/rawlead && .venv/bin/python scripts/tg_funnel_audit.py "
        "--log data/radar_site.log 2>&1 | tail -8 && "
        "echo o206_ok",
        check=False,
    )
    print(out.strip())
    ok = "o206_ok" in (out or "") and "active" in (out or "")
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
