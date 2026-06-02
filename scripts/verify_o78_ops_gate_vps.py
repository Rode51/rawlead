#!/usr/bin/env python3
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_, key_line, _ = ssh.run("grep '^RAWLEAD_OPS_KEY=' /opt/rawlead/.env | tail -1", check=False)
key = (key_line or "").strip().split("=", 1)[1] if "=" in (key_line or "") else ""
print("key_len:", len(key))

_, out, _ = ssh.run(
    f"curl -sf -o /dev/null -w 'ops_key=%{{http_code}}\\n' "
    f"'http://127.0.0.1:8000/ops/?key={key}'",
    check=False,
)
print((out or "").strip())

_, html, _ = ssh.run(f"curl -sf 'http://127.0.0.1:8000/ops/?key={key}'", check=False)
m = re.search(r'var API = "([^"]*)"', html or "")
print("api_in_html:", repr(m.group(1) if m else "?"))
print("title_ok:", "Пульт RawLead" in (html or ""))

_, out2, _ = ssh.run("curl -sf -o /dev/null -w 'ops_plain=%{http_code}\\n' http://127.0.0.1:8000/ops/", check=False)
print((out2 or "").strip())
