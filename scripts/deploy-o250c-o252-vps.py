#!/usr/bin/env python3
"""O250c+O252: push tg_http_request + TG content dedup — API + radar + tg_main restart."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "src/match_push.py",
    "src/lead_pipeline.py",
    "src/l1_pool.py",
    "src/pg_storage.py",
)


def main() -> int:
    print("=== O250c+O252 deploy: push failover + TG content dedup ===")
    for rel in _FILES:
        remote = f"/opt/rawlead/{rel}"
        ssh.upload(_ROOT / rel, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up {rel}")
    cmd = (
        "systemctl restart rawlead-api && sleep 3 && "
        "systemctl is-active rawlead-api && "
        "curl -sf http://127.0.0.1:8000/health && echo api_ok && "
        "systemctl restart rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-radar && echo radar_ok && "
        "(systemctl restart rawlead-tg 2>/dev/null || "
        "systemctl restart rawlead-tg-main 2>/dev/null || true) && "
        "grep -c tg_http_request /opt/rawlead/src/match_push.py && "
        "grep -c 'content_hash=\"\"' /opt/rawlead/src/lead_pipeline.py || true"
    )
    _, out, _ = ssh.run(cmd, check=False)
    print((out or "").strip())
    ok = "api_ok" in (out or "") and "radar_ok" in (out or "") and "active" in (out or "")
    print("OK" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
