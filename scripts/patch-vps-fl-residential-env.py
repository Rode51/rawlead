#!/usr/bin/env python3
"""Set FL_PROXY_URLS_RESIDENTIAL on VPS from YOUDO_PROXY_URLS RU tail (O210).

Uses RU slots after the first YOUDO slot (O191 DC prepend). Secrets stay on VPS / local .env only.

  .venv\\Scripts\\python.exe scripts\\patch-vps-fl-residential-env.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.site", override=True)

ENV_FILE = "/opt/rawlead/.env.site"
KEY = "FL_PROXY_URLS_RESIDENTIAL"
YOUDO_KEY = "YOUDO_PROXY_URLS"
DC_SKIP = max(1, int(os.environ.get("YOUDO_O191_DC_SLOTS", "1") or "1"))


def _parse_list(raw: str) -> list[str]:
    return [p.strip() for p in (raw or "").split(",") if p.strip()]


def _hint(url: str) -> str:
    u = url if "://" in url else f"http://{url}"
    p = urlparse(u)
    return f"{p.hostname}:{p.port or ''}".rstrip(":")


def _read_vps_youdo() -> str:
    remote = r"""
python3 - <<'PY'
path = "/opt/rawlead/.env.site"
val = ""
for line in open(path):
    if line.startswith("YOUDO_PROXY_URLS="):
        val = line.split("=", 1)[1].strip()
        break
print(val)
PY
"""
    _, out, _ = ssh.run(remote.strip(), check=False)
    return (out or "").strip()


def _residential_from_youdo(youdo_raw: str) -> list[str]:
    slots = _parse_list(youdo_raw)
    if len(slots) <= DC_SKIP:
        return []
    return slots[DC_SKIP:]


def _residential_local_fallback() -> list[str]:
    local = _parse_list(os.environ.get(YOUDO_KEY, ""))
    if len(local) <= DC_SKIP:
        return []
    return local[DC_SKIP:]


def _patch_env(value: str) -> bool:
    safe = value.replace("'", "'\"'\"'")
    cmd = (
        f"grep -q '^{KEY}=' {ENV_FILE} 2>/dev/null && "
        f"sed -i '/^{KEY}=/d' {ENV_FILE}; "
        f"echo '{KEY}={safe}' >> {ENV_FILE} && "
        f"grep -c '^{KEY}=' {ENV_FILE}"
    )
    _, out, _ = ssh.run(cmd, check=False)
    return (out or "").strip() == "1"


def main() -> int:
    print("=== patch FL_PROXY_URLS_RESIDENTIAL (O210) ===")
    youdo_raw = _read_vps_youdo()
    res = _residential_from_youdo(youdo_raw)
    if not res:
        print(f"VPS {YOUDO_KEY}: no RU tail after DC_SKIP={DC_SKIP}, trying local .env")
        res = _residential_local_fallback()
    if not res:
        print("FAIL — no residential slots (set YOUDO_PROXY_URLS with RU tail)")
        return 1

    merged_val = ",".join(res)
    print(f"residential slots: {len(res)} · first={_hint(res[0])} · last={_hint(res[-1])}")
    if not _patch_env(merged_val):
        print("FAIL — could not write VPS .env.site")
        return 1
    print(f"env: {KEY} ok")

    _, cnt, _ = ssh.run(f"grep -c '^{KEY}=' {ENV_FILE}", check=False)
    print("verify key count:", (cnt or "").strip())

    _, rst, _ = ssh.run(
        "systemctl restart rawlead-api 2>/dev/null || true; "
        "systemctl restart rawlead-radar && sleep 6 && "
        "systemctl is-active rawlead-api && systemctl is-active rawlead-radar && "
        "grep -c fl_on_residential_tier /opt/rawlead/src/exchange_proxy.py && "
        "echo fl_residential_patch_ok",
        check=False,
    )
    text = rst or ""
    print(text.encode("ascii", errors="replace").decode("ascii"))
    if "fl_residential_patch_ok" not in text:
        print("WARN — restart check incomplete")
        return 1
    print("OK — FL residential fallback armed on VPS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
