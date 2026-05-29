#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh

for c in [
    "grep '2026-05-29 13:5' /opt/rawlead/data/radar_site.log | grep -E 'FL.ru|Kwork|pipeline|Цикл|конвейер|site:сводка' | tail -20",
    "systemctl is-active rawlead-radar",
    "curl -s 'http://127.0.0.1:8000/v1/feed?limit=1' | python3 -c \"import sys,json;d=json.load(sys.stdin);i=d['items'][0] if d.get('items') else {};print(i.get('created_at'), i.get('title','')[:50])\"",
]:
    print("===", c[:55])
    _, o, _ = ssh.run(c, check=False)
    sys.stdout.buffer.write((o or "(empty)\n").encode("utf-8", errors="replace"))
