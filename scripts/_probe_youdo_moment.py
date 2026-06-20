#!/usr/bin/env python3
"""One-off: capture YouDo breakthrough context from VPS radar log."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

QUERIES = [
    ("ingest_50_all", "grep 'youdo:ingest done=50' /opt/rawlead/data/radar_site.log | tail -10"),
    (
        "first_outcome_ok_jun18",
        "grep 'fetch:youdo outcome=ok' /opt/rawlead/data/radar_site.log | head -3",
    ),
    (
        "last_outcome_ok",
        "grep 'fetch:youdo outcome=ok' /opt/rawlead/data/radar_site.log | tail -5",
    ),
    (
        "tail_youdo",
        "tail -n 1200 /opt/rawlead/data/radar_site.log | grep -i youdo | tail -80",
    ),
    (
        "profile_sticky",
        "grep -E 'profile_wiped|sticky|graduate|html_len|list_view|ephemeral' /opt/rawlead/data/radar_site.log | tail -25",
    ),
    ("profile_list", "ls -la /opt/rawlead/data/youdo_* 2>&1 | head -15"),
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
