"""O271: restart bot-poll + legacy after DB cutover."""
from __future__ import annotations

import sys

sys.path.insert(0, "scripts")
import deploy_vps_ssh as ssh

REMOTE = r"""
systemctl restart rawlead-bot-poll rawlead-radar-legacy
sleep 3
systemctl is-active rawlead-bot-poll rawlead-radar-legacy rawlead-api
journalctl -u rawlead-bot-poll -n 8 --no-pager 2>/dev/null | tail -5
cd /opt/rawlead && sudo -u rawlead env PYTHONPATH=/opt/rawlead/src .venv/bin/python - <<'PY'
from dotenv import load_dotenv
import os
load_dotenv('/opt/rawlead/.env.site', override=True)
url = os.environ.get('DATABASE_URL','')
print('bot_poll_would_use=' + ('local' if '127.0.0.1' in url else 'neon/other'))
PY
"""


def main() -> int:
    _, out, err = ssh.run(REMOTE.strip(), check=False)
    for line in ((out or "") + (err or "")).splitlines():
        print(line.encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
