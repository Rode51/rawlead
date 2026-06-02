#!/usr/bin/env python3
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_, out, _ = ssh.run("grep RAWLEAD_PUBLIC_API_URL /opt/rawlead/.env 2>/dev/null || echo NO_VAR", check=False)
print("env:", (out or "").strip())

_, html, _ = ssh.run("curl -sf http://127.0.0.1:8000/ops/", check=False)
m = re.search(r'var API = "([^"]*)"', html or "")
print("api_in_html:", repr(m.group(1) if m else "?"))

_, out2, _ = ssh.run(
    "curl -sf -o /dev/null -w 'dash_no_auth=%{http_code}\\n' http://127.0.0.1:8000/v1/admin/dashboard",
    check=False,
)
print((out2 or "").strip())

_, out3, _ = ssh.run(
    "cd /opt/rawlead && sudo -u rawlead .venv/bin/python -c "
    "\"import os,sys; sys.path.insert(0,'src'); "
    "from dotenv import load_dotenv; load_dotenv('.env'); "
    "from owner_admin import fetch_dashboard; "
    "d=fetch_dashboard(os.environ['DATABASE_URL']); "
    "print('ok visits', d['today']['visits'], 'leads', d['feed']['visible_count'])\"",
    check=False,
)
print("fetch_dashboard:", (out3 or "").strip()[:500])

_, out4, _ = ssh.run("grep TELEGRAM_CHAT_ID /opt/rawlead/.env | head -1", check=False)
print("owner_tid:", (out4 or "").strip()[:40] + "...")

_, out5, _ = ssh.run(
    "grep -c 'location /v1/admin/' /etc/nginx/sites-available/rawlead.ru.conf 2>/dev/null || echo 0",
    check=False,
)
print("nginx admin proxy:", (out5 or "").strip())
