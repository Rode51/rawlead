#!/usr/bin/env python3
"""O79 + O72e: proxy parsers + ai_analyze · restart API/radar."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_DEPLOY_FILES = (
    "src/exchange_proxy.py",
    "src/fl_parser.py",
    "src/kwork_parser.py",
    "src/main.py",
    "src/ai_analyze.py",
    "scripts/preprod_ai_prod_audit.py",
)


def _upload_files() -> None:
    for rel in _DEPLOY_FILES:
        local = _ROOT / rel
        if not local.is_file():
            print("SKIP missing", rel)
            continue
        remote = f"/opt/rawlead/{rel.replace(chr(92), '/')}"
        ssh.upload(local, remote)
        print("up", rel)


def main() -> int:
    print("=== O79+O72e deploy: proxy parsers + ai_analyze ===")
    _upload_files()
    ssh.run(
        "chown rawlead:rawlead "
        "/opt/rawlead/src/exchange_proxy.py "
        "/opt/rawlead/src/fl_parser.py "
        "/opt/rawlead/src/kwork_parser.py "
        "/opt/rawlead/src/main.py "
        "/opt/rawlead/src/ai_analyze.py "
        "/opt/rawlead/scripts/preprod_ai_prod_audit.py"
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
    _, proxy_lines, _ = ssh.run(
        "wc -l /opt/rawlead/src/exchange_proxy.py; "
        "grep -c 'fetch:fl proxy=' /opt/rawlead/src/fl_parser.py || true",
        check=False,
    )
    print("verify:", proxy_lines.strip())
    if "active" in (out or "") and health:
        print("O79+O72e DEPLOY OK")
        return 0
    print("O79+O72e DEPLOY — verify services manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
