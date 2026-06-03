#!/usr/bin/env python3
"""O97-code: L1 complexity + API difficulty · API deploy."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_API_EXTRA = ("api_server.py", "tools_catalog.py")


def main() -> int:
    print("=== O97-code deploy (API + ingest bundle) ===")
    names = list(ssh.INGEST_COUPLED_SRC) + list(_API_EXTRA)
    remote_src = "/opt/rawlead/src"
    for name in names:
        local = _ROOT / "src" / name
        remote = f"{remote_src}/{name}"
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up src/{name}")

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-api rawlead-radar && "
        "grep -c difficulty_from_ai_reasons /opt/rawlead/src/api_server.py && "
        "test -f /opt/rawlead/src/ai_reasons.py && echo ai_reasons_ok",
        check=False,
    )
    print(out.strip())
    text = out or ""
    ok = "active" in text and "ai_reasons_ok" in text
    if ok:
        print("DEPLOY OK")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
