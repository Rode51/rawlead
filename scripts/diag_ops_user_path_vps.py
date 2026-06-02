#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

checks = [
    "grep -n 'ops/dashboard' /opt/rawlead/src/owner_admin.py | head -3",
    "grep -n 'wp-json/rawlead/v1' /opt/rawlead/src/owner_admin.py | head -3",
    "curl -sf 'https://rawlead.ru/ops/?key=ZDZFL74ChSIFpm732mzbqhLEj3_U0xEo' -k | grep -o 'var API = \"[^\"]*\"'",
    "curl -sf -o /dev/null -w 'ops_no_auth=%{http_code}\\n' 'https://rawlead.ru/wp-json/rawlead/v1/ops/dashboard' -k",
    "grep -i authorization /etc/nginx/sites-available/rawlead.ru.conf | head -5 || echo no_auth_nginx",
]

for c in checks:
    print("===", c[:70])
    _, out, err = ssh.run(c, check=False)
    print((out or err or "").strip()[:400])
