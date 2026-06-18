"""O271: restart services + tail journal on failure."""
from __future__ import annotations

import sys

sys.path.insert(0, "scripts")
import deploy_vps_ssh as ssh

REMOTE = r"""
systemctl start rawlead-api rawlead-radar
sleep 4
echo ===STATUS===
systemctl is-active rawlead-api rawlead-radar postgresql
echo ===API_LOG===
journalctl -u rawlead-api -n 25 --no-pager 2>/dev/null | tail -20
echo ===RADAR_LOG===
journalctl -u rawlead-radar -n 25 --no-pager 2>/dev/null | tail -20
echo ===HEALTH===
curl -fsS -m 8 http://127.0.0.1:8000/health 2>&1 || true
"""


def main() -> int:
    _, out, err = ssh.run(REMOTE.strip(), check=False)
    text = (out or "") + (err or "")
    for line in text.splitlines():
        print(line.encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
