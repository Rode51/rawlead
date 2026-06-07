#!/usr/bin/env python3
"""O117-deploy: Kwork wall-clock timeout + O72e allowlist → restart radar/bot/api."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "exchange_browser_fetch.py",
    "kwork_parser.py",
    "ai_analyze.py",
)


def main() -> int:
    print("=== O117 deploy: kwork timeout + forbidden allowlist ===")
    for name in _FILES:
        local = _ROOT / "src" / name
        remote = f"/opt/rawlead/src/{name}"
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up src/{name}")

    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar rawlead-bot-poll rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-radar rawlead-bot-poll rawlead-api && "
        "grep -c fetch_listing_html_browser_wall_clock /opt/rawlead/src/exchange_browser_fetch.py && "
        "grep -c fetch_listing_html_browser_wall_clock /opt/rawlead/src/kwork_parser.py && "
        "grep -c _check_forbidden_reply_words /opt/rawlead/src/ai_analyze.py && echo o117_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    ok = text.count("active") >= 3 and "o117_ok" in text
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
