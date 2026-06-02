#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

root = Path(__file__).resolve().parents[1]
remote = "/tmp/_vps_test_ops_dashboard.py"
ssh.upload(root / "scripts/_vps_test_ops_dashboard.py", remote)
_, out, err = ssh.run(
    f"cd /opt/rawlead && sudo -u rawlead .venv/bin/python {remote}",
    check=False,
)
print(out or err)
