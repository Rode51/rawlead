#!/usr/bin/env python3
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_, key_line, _ = ssh.run("grep '^RAWLEAD_OPS_KEY=' /opt/rawlead/.env | tail -1", check=False)
key = (key_line or "").strip().split("=", 1)[1] if "=" in (key_line or "") else ""

_, html, _ = ssh.run(f"curl -sf 'https://rawlead.ru/ops/?key={key}' -k", check=False)
print("len", len(html or ""))
print("has_script", "<script>" in (html or ""))
print("api_line", re.search(r'var API = "[^"]*"', html or ""))
print("fetch_line", "fetch(API" in (html or ""))
# test https dashboard via external with fake token
_, out, _ = ssh.run(
    "curl -sf -o /dev/null -w 'code=%{http_code} time=%{time_total}\\n' "
    "-H 'Authorization: Bearer fake' "
    "https://rawlead.ru/v1/admin/dashboard -k",
    check=False,
)
print((out or "").strip())
