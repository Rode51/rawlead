#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

checks = [
    "grep -A6 'location /v1/admin' /etc/nginx/sites-available/rawlead.ru.conf",
    "curl -sf -o /dev/null -w 'http_admin=%{http_code} time=%{time_total}\\n' http://127.0.0.1/v1/admin/dashboard 2>/dev/null || echo http_fail",
    "curl -sf -o /dev/null -w 'https_admin=%{http_code} time=%{time_total}\\n' https://rawlead.ru/v1/admin/dashboard -k",
    "curl -sf -o /dev/null -w 'https_ops=%{http_code}\\n' https://rawlead.ru/ops/ -k",
    "curl -sf -o /dev/null -w 'local_admin=%{http_code} time=%{time_total}\\n' http://127.0.0.1:8000/v1/admin/dashboard",
]
for c in checks:
    print("===", c[:70])
    _, out, err = ssh.run(c, check=False)
    print(out or err)
