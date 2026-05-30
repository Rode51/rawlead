#!/usr/bin/env python3
"""Post-deploy smoke: health, /status text, O68 JS markers."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

REMOTE_STATUS = r"""cd /opt/rawlead && sudo -u rawlead .venv/bin/python << 'PY'
import sys
sys.path.insert(0, "src")
from dotenv import load_dotenv
load_dotenv(".env.site")
load_dotenv(".env")
from config import load_config
from storage import storage_from_config
from radar_status import format_status_message
c = load_config()
s = storage_from_config(c)
m = format_status_message(c, s)
print(m[:2000])
PY"""


def main() -> int:
    _, health, _ = ssh.run("curl -s http://127.0.0.1:8000/health", check=False)
    print("=== /health ===")
    print(health.strip())

    _, status, _ = ssh.run(REMOTE_STATUS, check=False)
    print("=== /status (format_status_message) ===")
    sys.stdout.buffer.write(status.encode("utf-8", errors="replace"))

    _, js, _ = ssh.run(
        "grep -c replyCtaHtml /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js; "
        "grep -c 'function headBadgesHtml' /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js; "
        "awk '/function headBadgesHtml/,/^  }/' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js | grep -c repliedBadge || echo 0",
        check=False,
    )
    print("=== O68 markers ===")
    print(js.strip())

    ok = (
        "draft_fail_per_hour" in health
        and "L1 48ч" in status
        and "ИИ:" in status
    )
    print("SMOKE", "OK" if ok else "PARTIAL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
