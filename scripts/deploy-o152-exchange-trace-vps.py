#!/usr/bin/env python3
"""O152: exchange trace jsonl + /ops/ trace block + FL lamp fix."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_RADAR_FILES = (
    "src/exchange_trace.py",
    "src/exchange_proxy.py",
    "src/exchange_browser_fetch.py",
    "src/exchange_health.py",
    "src/main.py",
)
_API_FILES = (
    "src/exchange_trace.py",
    "src/exchange_health.py",
    "src/owner_admin.py",
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
    print("=== O152 deploy: radar exchange trace ===")
    radar_remotes = _upload(_RADAR_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(radar_remotes))

    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-radar && "
        "grep -c log_exchange_trace /opt/rawlead/src/exchange_trace.py && "
        "grep -c OPENROUTER_HTTP_PROXY /opt/rawlead/src/exchange_proxy.py && "
        "grep -c _ok_after_error /opt/rawlead/src/exchange_health.py && "
        "echo o152_radar_ok",
        check=False,
    )
    print(out.strip())
    if "o152_radar_ok" not in (out or "") or "active" not in (out or ""):
        print("RADAR DEPLOY CHECK — verify manually")
        return 1
    print("RADAR DEPLOY OK")

    print("\n=== O152 deploy: API /ops/ trace ===")
    api_remotes = _upload(_API_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(api_remotes))

    _, out2, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "grep -c rl-ops-trace /opt/rawlead/src/owner_admin.py && "
        "grep -c recent_traces /opt/rawlead/src/exchange_health.py && "
        "echo o152_api_ok",
        check=False,
    )
    print(out2.strip())
    if "o152_api_ok" not in (out2 or "") or "active" not in (out2 or ""):
        print("API DEPLOY CHECK — verify manually")
        return 1
    print("API DEPLOY OK")
    print("DEPLOY OK — smoke: journalctl -u rawlead-radar | grep exchange:trace | tail -5")
    print("             /ops/ — «Последний trace» на карточках бирж")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
