#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_, out, _ = ssh.run(
    "curl -sf -o /dev/null -w 'qr=%{http_code} type=%{content_type}\\n' "
    "'https://rawlead.ru/wp-json/rawlead/v1/auth/qr-image?data=https%3A%2F%2Ft.me%2Frawlead_bot' -k",
    check=False,
)
print((out or "").strip())
