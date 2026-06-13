#!/usr/bin/env python3
"""Wait for post-t0f YouDo fetch cycle on VPS."""
from __future__ import annotations

import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def _grep() -> str:
    _, out, _ = ssh.run(
        "date -u '+%Y-%m-%d %H:%M:%S UTC'; "
        "systemctl show rawlead-radar -p ActiveEnterTimestamp --value; "
        "grep -E 'fetch_start|fetch_end|youdo:browser backend' "
        "/opt/rawlead/data/radar_site.log | tail -12",
        check=False,
    )
    return out or ""


def main() -> int:
    for attempt in range(1, 13):
        text = _grep()
        safe = text.encode("ascii", errors="replace").decode("ascii")
        print(f"=== attempt {attempt} ===")
        print(safe)
        if "parsed=" in safe:
            for line in safe.splitlines():
                if "fetch_end" in line and "parsed=" in line:
                    part = line.split("parsed=")[-1].split()[0]
                    try:
                        if int(part) >= 50:
                            print("INGEST OK parsed>=50")
                            return 0
                    except ValueError:
                        pass
        if attempt < 12:
            print("waiting 90s for next cycle...")
            time.sleep(90)
    print("INGEST NOT OK yet — check logs manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
