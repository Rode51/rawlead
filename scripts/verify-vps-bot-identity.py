#!/usr/bin/env python3
"""VPS: getMe для .env.legacy vs .env.site (без вывода токенов)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

REMOTE = r"""
cd /opt/rawlead && sudo -u rawlead .venv/bin/python - <<'PY'
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

root = Path("/opt/rawlead")

def check(name: str) -> None:
    path = root / name
    if not path.is_file():
        print(f"{name}: MISSING")
        return
    load_dotenv(path, override=True)
    tok = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not tok:
        print(f"{name}: NO_TOKEN")
        return
    r = requests.get(f"https://api.telegram.org/bot{tok}/getMe", timeout=20)
    j = r.json()
    if not j.get("ok"):
        print(f"{name}: getMe_FAIL {j.get('description', '?')[:60]}")
        return
    u = j["result"].get("username", "?")
    print(f"{name}: @{u}")

check(".env.legacy")
check(".env.site")
PY
"""

if __name__ == "__main__":
    _, out, err = ssh.run(REMOTE, check=False)
    print(out or err)
