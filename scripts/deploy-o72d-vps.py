#!/usr/bin/env python3
"""O72d: deploy ai_analyze.py (O72c prompts) · restart API/radar. Без regen старых."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_O72D_FILES = (
    "src/ai_analyze.py",
    "src/config.py",
    "src/match_push.py",
)


def _upload_files() -> None:
    for rel in _O72D_FILES:
        local = _ROOT / rel
        if not local.is_file():
            print("SKIP missing", rel)
            continue
        remote = f"/opt/rawlead/{rel.replace(chr(92), '/')}"
        ssh.upload(local, remote)
        print("up", rel)


def main() -> int:
    print("=== O72d deploy: ai_analyze (new leads only, no regen) ===")
    _upload_files()
    ssh.run(
        "chown rawlead:rawlead "
        "/opt/rawlead/src/ai_analyze.py "
        "/opt/rawlead/src/config.py "
        "/opt/rawlead/src/match_push.py"
    )
    print("restart rawlead-api rawlead-radar...")
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-api rawlead-radar",
        check=False,
    )
    print(out or "")
    _, health, _ = ssh.run(
        "curl -sf http://127.0.0.1:8000/health | head -c 500; echo",
        check=False,
    )
    print(health or "")
    if "active" in (out or "") and health:
        print("O72d DEPLOY OK")
        return 0
    print("O72d DEPLOY — verify services manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
