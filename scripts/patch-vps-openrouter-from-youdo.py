#!/usr/bin/env python3
"""O135/Wave2: OPENROUTER_HTTP_PROXY ← 1-й слот YOUDO_PROXY_URLS на VPS (секреты не в git).

  python scripts/patch-vps-openrouter-from-youdo.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from urllib.parse import urlparse

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

ENV_FILE = "/opt/rawlead/.env.site"
YOUDO_KEY = "YOUDO_PROXY_URLS"
OR_KEY = "OPENROUTER_HTTP_PROXY"


def _mask_proxy(url: str) -> str:
    try:
        p = urlparse(url.strip())
        host = p.hostname or "?"
        port = p.port or (443 if p.scheme == "https" else 80)
        return f"{host}:{port}"
    except Exception:
        return "?"


def main() -> int:
    _, out, err = ssh.run(
        f"grep '^{YOUDO_KEY}=' {ENV_FILE} 2>/dev/null | tail -1",
        check=False,
    )
    line = (out or err or "").strip()
    if not line or "=" not in line:
        print(f"FAIL: {YOUDO_KEY} not found in {ENV_FILE}")
        return 1
    value = line.split("=", 1)[1].strip().strip('"').strip("'")
    first = value.split(",")[0].strip()
    if not first:
        print(f"FAIL: {YOUDO_KEY} empty")
        return 1

    safe = first.replace("'", "'\"'\"'")
    cmd = (
        f"grep -q '^{OR_KEY}=' {ENV_FILE} 2>/dev/null && "
        f"sed -i '/^{OR_KEY}=/d' {ENV_FILE}; "
        f"echo '{OR_KEY}={safe}' >> {ENV_FILE} && "
        f"grep -c '^{OR_KEY}=' {ENV_FILE}"
    )
    _, set_out, set_err = ssh.run(cmd, check=False)
    if (set_out or "").strip() != "1":
        print("FAIL — could not write OPENROUTER_HTTP_PROXY")
        print(set_out or set_err)
        return 1

    print(f"OK: {OR_KEY} ← 1st {YOUDO_KEY} slot ({_mask_proxy(first)})")

    _, rst, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar rawlead-radar-legacy && sleep 4 && "
        "systemctl is-active rawlead-api rawlead-radar rawlead-radar-legacy",
        check=False,
    )
    active = (rst or "").count("active")
    print("services active:", active, "/ 3")
    if active < 3:
        print((rst or "").strip())
        return 1

    _, log_out, _ = ssh.run(
        "journalctl -u rawlead-api -n 30 --no-pager 2>/dev/null | grep -i 'openrouter\\|db:' | tail -3",
        check=False,
    )
    if log_out.strip():
        print("api log hint:", log_out.strip().splitlines()[-1][:120])
    print("or_proxy_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
