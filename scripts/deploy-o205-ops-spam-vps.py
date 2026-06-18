#!/usr/bin/env python3
"""O205: ops fast shell + banner + TG chat_id + ops-pult.js."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_API_FILES = (
    "src/api_server.py",
    "src/owner_admin.py",
    "src/ops_funnel.py",
    "src/static/ops-pult.js",
)
_RADAR_FILES = ("src/tg_monitor.py",)
_PROBE_FILES = ("scripts/probe_tg_test_group_membership.py",)


def _upload(files: tuple[str, ...]) -> list[str]:
    remotes: list[str] = []
    for rel in files:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    return remotes


def main() -> int:
    print("=== O205 tail deploy: fast ops + TG chat_id ===")
    ssh.run("mkdir -p /opt/rawlead/src/static && chown rawlead:rawlead /opt/rawlead/src/static")
    api_remotes = _upload(_API_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(api_remotes))
    _, out_api, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-api && "
        "grep -c 'запущена в фоне' /opt/rawlead/src/owner_admin.py && "
        "grep -c 'style.display' /opt/rawlead/src/static/ops-pult.js && "
        "curl -sf -o /dev/null -w 'ops_pult_js=%{http_code}\\n' "
        "http://127.0.0.1:8000/ops/static/ops-pult.js && "
        "echo o205_api_ok",
        check=False,
    )
    print(out_api.strip())
    api_ok = "o205_api_ok" in (out_api or "") and "active" in (out_api or "")

    radar_remotes = _upload(_RADAR_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(radar_remotes))
    probe_remotes = _upload(_PROBE_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(probe_remotes))
    _, out_radar, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 4 && "
        "systemctl is-active rawlead-radar && "
        "grep -c 'тг:пропуск' /opt/rawlead/src/tg_monitor.py && "
        "echo o205_radar_ok",
        check=False,
    )
    print(out_radar.strip())
    radar_ok = "o205_radar_ok" in (out_radar or "") and "active" in (out_radar or "")

    if api_ok and radar_ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
