#!/usr/bin/env python3
"""O138-PARSER-OBS: parsed vs fresh metrics, O104 health, /ops/ listing line."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_RADAR_FILES = (
    "src/radar_cycle_log.py",
    "src/fl_parser.py",
    "src/kwork_parser.py",
    "src/main.py",
    "src/exchange_health.py",
)
_API_FILES = (
    "src/owner_admin.py",
    "src/exchange_health.py",
)
_SMOKE_FILES = (
    "scripts/exchange_parse_smoke.py",
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
    print("=== O138 deploy: radar parsed/fresh + health ===")
    radar_remotes = _upload(_RADAR_FILES + _SMOKE_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(radar_remotes))

    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-radar && "
        "grep -c stash_listing_metrics /opt/rawlead/src/radar_cycle_log.py && "
        "grep -c 'listing:fl parsed' /opt/rawlead/src/fl_parser.py && "
        "grep -c last_parsed_cards /opt/rawlead/src/exchange_health.py && "
        "echo o138_radar_ok",
        check=False,
    )
    print(out.strip())
    if "o138_radar_ok" not in (out or "") or "active" not in (out or ""):
        print("RADAR DEPLOY CHECK — verify manually")
        return 1
    print("RADAR DEPLOY OK")

    print("\n=== O138 deploy: API /ops/ parsed line ===")
    api_remotes = _upload(_API_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(api_remotes))

    _, out2, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "grep -c listing_line /opt/rawlead/src/owner_admin.py && "
        "grep -c listing_line /opt/rawlead/src/exchange_health.py && "
        "echo o138_api_ok",
        check=False,
    )
    print(out2.strip())
    if "o138_api_ok" not in (out2 or "") or "active" not in (out2 or ""):
        print("API DEPLOY CHECK — verify manually")
        return 1
    print("API DEPLOY OK")
    print("DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
