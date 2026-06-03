#!/usr/bin/env python3
"""VPS .env.site: L1_MAX_WORKERS + опц. OPENROUTER_API_KEY_L1_B (секреты не в git).

PowerShell:
  $env:L1_MAX_WORKERS='4'
  $env:OPENROUTER_API_KEY_L1_B='sk-or-...'   # опц., для O99-w
  .venv\\Scripts\\python.exe scripts\\patch-vps-l1-workers-env.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

ENV_FILE = "/opt/rawlead/.env.site"


def _set_kv(key: str, value: str) -> None:
    safe = value.replace("'", "'\"'\"'")
    ssh.run(
        f"grep -q '^{key}=' {ENV_FILE} 2>/dev/null && sed -i '/^{key}=/d' {ENV_FILE}; "
        f"echo '{key}={safe}' >> {ENV_FILE}",
        check=False,
    )


def main() -> int:
    workers = (os.environ.get("L1_MAX_WORKERS") or "4").strip()
    key_b = (os.environ.get("OPENROUTER_API_KEY_L1_B") or "").strip()

    _set_kv("L1_MAX_WORKERS", workers)
    print(f"OK L1_MAX_WORKERS={workers}")

    if key_b:
        _set_kv("OPENROUTER_API_KEY_L1_B", key_b)
        print("OK OPENROUTER_API_KEY_L1_B=*** (stored on VPS, not in git)")
    else:
        print("SKIP OPENROUTER_API_KEY_L1_B (not in env)")

    _, rst, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 3 && systemctl is-active rawlead-radar",
        check=False,
    )
    print((rst or "").strip())
    _, verify, _ = ssh.run(
        f"grep -E '^L1_MAX_WORKERS=|^OPENROUTER_API_KEY_L1_B=' {ENV_FILE} | "
        "sed 's/OPENROUTER_API_KEY_L1_B=.*/OPENROUTER_API_KEY_L1_B=***/'",
        check=False,
    )
    print(verify or "")
    return 0 if "active" in (rst or "") else 1


if __name__ == "__main__":
    raise SystemExit(main())
