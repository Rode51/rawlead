#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh

QUERIES = [
    ("window_0205_0211", "awk '/2026-06-19 02:0[5-9]|2026-06-19 02:10|2026-06-19 02:11:0/' /opt/rawlead/data/radar_site.log | grep -iE 'fetch:youdo|hard_reset|sticky|outcome|ingest|restart|cooldown|profile_wiped|cycle_decision'"),
    ("window_0211_0216", "awk '/2026-06-19 02:11:1|2026-06-19 02:1[2-6]/' /opt/rawlead/data/radar_site.log | grep -iE 'fetch:youdo|outcome|ingest|fail|cooldown|traffic_guard'"),
    ("fetch_fail", "grep -E 'fetch:youdo outcome=fail|fetch:youdo outcome=skip|youdo:ingest|soft_sp|cooldown|fail_streak' /opt/rawlead/data/radar_site.log | tail -30"),
    ("ops_reset", "grep -iE 'ops.*youdo|youdo.*ops|manual.*reset|clear.youdo|profile_wipe' /opt/rawlead/data/radar_site.log | tail -15"),
]

def main():
    for label, cmd in QUERIES:
        print(f"\n=== {label} ===")
        _, out, err = ssh.run(cmd, check=False)
        text = (out or err or "(empty)").strip()
        try:
            print(text[-6000:] if len(text) > 6000 else text)
        except UnicodeEncodeError:
            print(text.encode("ascii", errors="replace").decode("ascii"))

if __name__ == "__main__":
    main()
