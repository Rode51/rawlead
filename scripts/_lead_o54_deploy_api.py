#!/usr/bin/env python3
"""O54: sync src + restart rawlead-api."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== O54 API deploy ===")
    n = ssh.sync_project()
    print(f"synced {n} files -> /opt/rawlead")
    ssh.run(
        r"find /opt/rawlead/deploy -name '*.sh' -exec sed -i 's/\r$//' {} \; && "
        "chmod +x /opt/rawlead/deploy/*.sh"
    )
    ssh.run("chown -R rawlead:rawlead /opt/rawlead/src /opt/rawlead/scripts /opt/rawlead/tests")
    _, out, _ = ssh.run(
        "test -f /opt/rawlead/src/reply_draft_strip.py && echo OK || echo MISSING",
        check=False,
    )
    print("reply_draft_strip.py:", (out or "").strip())
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api && sleep 2 && systemctl is-active rawlead-api",
        check=False,
    )
    print("rawlead-api:", (out or "").strip())
    _, code, _ = ssh.run(
        "curl -s -o /dev/null -w '%{http_code}' 'http://127.0.0.1:8000/v1/feed?limit=1'",
        check=False,
    )
    print("feed HTTP:", (code or "").strip())
    ok = "OK" in (out or "") and (code or "").strip() == "200"
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
