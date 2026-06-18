#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh

cmds = [
    ("push_26978", r"grep 'lead=26978' /opt/rawlead/data/radar_site.log | tail -10 || echo NONE"),
    ("l1_26978", r"grep '26978\|tg:-1005177575757:id=185' /opt/rawlead/data/radar_site.log | tail -15"),
    ("env_debug", r"grep -E '^(MATCH_PUSH|MATCH_PUSH_DEBUG)=' /opt/rawlead/.env.site"),
    ("runtime", r"""PID=$(systemctl show -p MainPID --value rawlead-radar); tr '\0' '\n' < /proc/$PID/environ | grep -E '^(MATCH_PUSH|MATCH_PUSH_DEBUG)='"""),
]
out = []
for n, c in cmds:
    _, t, _ = ssh.run(c, check=False)
    out.append(f"=== {n} ===\n{(t or '').strip()}\n")
Path(_ROOT / "scripts" / "_mechanic_push_final.out").write_text("\n".join(out), encoding="utf-8")
print("ok")
