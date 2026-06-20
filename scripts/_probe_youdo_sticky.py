#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh

QUERIES = [
    ("sticky_modes", "grep 'youdo:trace stage=sticky_' /opt/rawlead/data/radar_site.log | tail -40"),
    ("warm_counts", "grep 'youdo:trace stage=sticky_' /opt/rawlead/data/radar_site.log | grep -c 'warm=1' ; grep 'youdo:trace stage=sticky_' /opt/rawlead/data/radar_site.log | grep -c 'warm=0'"),
    ("reload_lines", "grep 'sticky_reload' /opt/rawlead/data/radar_site.log | tail -15"),
    ("teardown", "grep 'sticky_teardown' /opt/rawlead/data/radar_site.log | tail -15"),
    ("1712b_today", "awk '/2026-06-19/' /opt/rawlead/data/radar_site.log | grep 'html_len=17' | wc -l"),
    ("outcome_today", "grep 'fetch:youdo outcome' /opt/rawlead/data/radar_site.log | grep '2026-06-19' | tail -20"),
]

def main():
    for label, cmd in QUERIES:
        print(f"\n=== {label} ===")
        _, out, err = ssh.run(cmd, check=False)
        print((out or err or "(empty)").strip()[-5000:])

if __name__ == "__main__":
    main()
