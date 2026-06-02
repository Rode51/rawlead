#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_, out, _ = ssh.run(
    "curl -sf http://127.0.0.1:8000/ops/ 2>/dev/null | grep -o 'Пульт RawLead' | head -1",
    check=False,
)
print("ops_title:", (out or "").strip() or "(not found)")
_, out2, _ = ssh.run(
    "grep 'admin/pageview' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
    check=False,
)
print("beacon_ok:", "rest_url" in (out2 or ""))
