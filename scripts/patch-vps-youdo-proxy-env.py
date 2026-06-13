#!/usr/bin/env python3
"""Записать YOUDO_PROXY_URLS в /opt/rawlead/.env.site на VPS (секреты не в git).

O191 order (DC→RU): use scripts/deploy-o191-youdo-proxy-vps.py — prepends FL/EXCHANGE DC slot(s),
keeps RU residential tail, resets youdo active_slot=0. Rollback here with RU-only YOUDO_PROXY_URLS.

Локально в .env:
  YOUDO_PROXY_URLS=http://user:pass@host:10000,http://user:pass@host:10001
  .venv\\Scripts\\python.exe scripts\\patch-vps-youdo-proxy-env.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.site", override=True)

ENV_FILE = "/opt/rawlead/.env.site"
KEY = "YOUDO_PROXY_URLS"


def main() -> int:
    value = (os.environ.get(KEY) or "").strip()
    if not value:
        print(f"Set {KEY} in .env (comma-separated, no spaces)")
        return 1
    if " " in value and "," not in value:
        print("Use commas between proxies, no spaces")
        return 1
    safe = value.replace("'", "'\"'\"'")
    cmd = (
        f"grep -q '^{KEY}=' {ENV_FILE} 2>/dev/null && "
        f"sed -i '/^{KEY}=/d' {ENV_FILE}; "
        f"echo '{KEY}={safe}' >> {ENV_FILE} && "
        f"grep -c '^{KEY}=' {ENV_FILE}"
    )
    _, out, err = ssh.run(cmd, check=False)
    print(out or err)
    if (out or "").strip() != "1":
        print("FAIL — check VPS .env.site")
        return 1
    _, rst, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 3 && systemctl is-active rawlead-radar",
        check=False,
    )
    print("radar:", (rst or "").strip())
    return 0 if "active" in (rst or "") else 1


if __name__ == "__main__":
    raise SystemExit(main())
