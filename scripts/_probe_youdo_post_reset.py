#!/usr/bin/env python3
"""YouDo tail after hard reset."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh

QUERIES = [
    ("tail_all", "tail -n 400 /opt/rawlead/data/radar_site.log"),
    ("hard_reset_recent", "grep -E 'hard_reset|restart_source|profile_wiped|youdo_hard' /opt/rawlead/data/radar_site.log | tail -25"),
    ("outcome_recent", "grep 'fetch:youdo outcome' /opt/rawlead/data/radar_site.log | tail -15"),
    ("antibot_recent", "grep 'html_len=17' /opt/rawlead/data/radar_site.log | tail -20"),
    ("profile", "ls -la /opt/rawlead/data/ | grep youdo"),
    ("sticky_recent", "grep sticky_goto /opt/rawlead/data/radar_site.log | tail -8"),
]

def main():
    for label, cmd in QUERIES:
        print(f"\n=== {label} ===")
        _, out, err = ssh.run(cmd, check=False)
        text = (out or err or "(empty)").strip()
        try:
            print(text[-4000:] if len(text) > 4000 else text)
        except UnicodeEncodeError:
            print(text.encode("ascii", errors="replace").decode("ascii"))

if __name__ == "__main__":
    main()
