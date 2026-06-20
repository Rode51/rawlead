#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh

QUERIES = [
    ("after_021030", "awk '/2026-06-19 02:10:3|2026-06-19 02:1[1-9]/' /opt/rawlead/data/radar_site.log | grep -iE 'fetch:youdo|youdo:trace stage=(cycle|sticky|hard|fail|browser)|youdo:ingest|youdo:skip|outcome' | head -60"),
    ("hard_reset_log", "grep 'fetch:youdo hard_reset' /opt/rawlead/data/radar_site.log | tail -10"),
    ("restart_source", "grep 'restart_source' /opt/rawlead/data/radar_site.log | tail -10"),
    ("backup_tar", "ls -la /opt/rawlead/data/backups/youdo_profile_g2_2026-06-19.tar.gz 2>/dev/null || ls -la /opt/rawlead/data/backups/ | grep youdo"),
]

def main():
    for label, cmd in QUERIES:
        print(f"\n=== {label} ===")
        _, out, err = ssh.run(cmd, check=False)
        text = (out or err or "(empty)").strip()
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode("ascii", errors="replace").decode("ascii"))

if __name__ == "__main__":
    main()
