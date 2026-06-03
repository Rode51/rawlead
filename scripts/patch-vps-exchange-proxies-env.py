#!/usr/bin/env python3
"""Записать EXCHANGE_PROXY_URLS в /opt/rawlead/.env.site на VPS (секреты не в git).

Задай строку локально (PowerShell):
  $env:EXCHANGE_PROXY_URLS='http://185.147.131.15:8000:user:pass,...'
  .venv\\Scripts\\python.exe scripts\\patch-vps-exchange-proxies-env.py
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
KEY = "EXCHANGE_PROXY_URLS"


def main() -> int:
    value = (os.environ.get(KEY) or "").strip()
    if not value:
        print(f"Set {KEY} in environment (comma-separated http://host:port:user:pass)")
        return 1
    if " " in value and "," not in value:
        print("Use commas between proxies, no spaces")
        return 1
    # Escape for shell: single-quote wrap, escape single quotes in value
    safe = value.replace("'", "'\"'\"'")
    cmd = (
        f"grep -q '^{KEY}=' {ENV_FILE} 2>/dev/null && "
        f"sed -i '/^{KEY}=/d' {ENV_FILE}; "
        f"echo '{KEY}={safe}' >> {ENV_FILE} && "
        f"grep -c '^{KEY}=' {ENV_FILE}"
    )
    _, out, err = ssh.run(cmd, check=False)
    print(out or err)
    if (out or "").strip() == "1":
        print("OK — patching FL/KWORK to same cascade + restart radar")
        for extra_key in ("FL_PROXY_URLS", "KWORK_PROXY_URLS"):
            ev = (os.environ.get(extra_key) or os.environ.get(KEY) or "").strip()
            if extra_key == "KWORK_PROXY_URLS" and not (os.environ.get("KWORK_PROXY_URLS") or "").strip():
                ev = ""
            elif not ev:
                continue
            safe_e = ev.replace("'", "'\"'\"'")
            ssh.run(
                f"grep -q '^{extra_key}=' {ENV_FILE} 2>/dev/null && "
                f"sed -i '/^{extra_key}=/d' {ENV_FILE}; "
                f"echo '{extra_key}={safe_e}' >> {ENV_FILE}",
                check=False,
            )
        _, rst, _ = ssh.run(
            "systemctl restart rawlead-radar && sleep 3 && systemctl is-active rawlead-radar",
            check=False,
        )
        print((rst or "").strip())
        return 0 if "active" in (rst or "") else 1
    print("FAIL — check VPS .env.site")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
