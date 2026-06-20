#!/usr/bin/env python3
"""YouDo regression triage — VPS log snapshot."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

QUERIES = [
    ("last_sticky_big", "grep sticky_goto /opt/rawlead/data/radar_site.log | tail -8"),
    ("last_ingest", "grep 'youdo:ingest' /opt/rawlead/data/radar_site.log | tail -10"),
    ("last_fetch", "grep 'fetch:youdo' /opt/rawlead/data/radar_site.log | tail -15"),
    ("env", "grep -E '^YOUDO_|^RADAR_CYCLE' /opt/rawlead/.env.site"),
    ("profile_dirs", "ls -ld /opt/rawlead/data/youdo_* 2>&1"),
    ("cookie_size", "ls -la /opt/rawlead/data/youdo_185.147.131.15:8000_g2/cookies.sqlite 2>&1"),
]


def main() -> int:
    for label, cmd in QUERIES:
        print(f"\n=== {label} ===")
        _, out, err = ssh.run(cmd, check=False)
        text = (out or err or "(empty)").strip()
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode("ascii", errors="replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
