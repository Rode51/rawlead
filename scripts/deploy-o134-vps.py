#!/usr/bin/env python3
"""O134-INGEST-SLA: fresh-only listing + published_at UTC + /ops/ SLA metrics."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_RADAR_FILES = (
    "src/listing_fresh.py",
    "src/ingest_published_at.py",
    "src/fl_parser.py",
    "src/kwork_parser.py",
    "src/lead_pipeline.py",
    "src/main.py",
    "src/pg_storage.py",
    "src/storage.py",
)
_API_FILES = (
    "src/owner_admin.py",
    "src/exchange_health.py",
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
    print("=== O134 deploy: radar ingest SLA ===")
    radar_remotes = _upload(_RADAR_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(radar_remotes))

    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-radar && "
        "grep -c trim_listing_at_known /opt/rawlead/src/listing_fresh.py && "
        "grep -c parse_fl_published_at /opt/rawlead/src/ingest_published_at.py && "
        "grep -c has_seen /opt/rawlead/src/storage.py && "
        "echo o134_radar_ok",
        check=False,
    )
    print(out.strip())
    if "o134_radar_ok" not in (out or "") or "active" not in (out or ""):
        print("RADAR DEPLOY CHECK — verify manually")
        return 1
    print("RADAR DEPLOY OK")

    print("\n=== O134 deploy: API /ops/ ingest SLA ===")
    api_remotes = _upload(_API_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(api_remotes))

    _, out2, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "grep -c feed_within_5m /opt/rawlead/src/owner_admin.py && "
        "grep -c feed_within_5m_pct /opt/rawlead/src/exchange_health.py && "
        "echo o134_api_ok",
        check=False,
    )
    print(out2.strip())
    if "o134_api_ok" not in (out2 or "") or "active" not in (out2 or ""):
        print("API DEPLOY CHECK — verify manually")
        return 1
    print("API DEPLOY OK")
    print("DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
