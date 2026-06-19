#!/usr/bin/env python3
"""O283: MiMo audit fixes — FL loop guards + ai_analyze ContextVar/R11 proxy fallback."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "src/exchange_browser_fetch.py",
    "src/exchange_proxy.py",
    "src/ai_analyze.py",
)


def main() -> int:
    print("=== O283 deploy: MiMo audit fixes (radar + api) ===")
    remotes: list[str] = []
    for rel in _FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "grep -c 'set_restart_source=not fl_listing_subprocess_enabled' "
        "/opt/rawlead/src/exchange_browser_fetch.py && "
        "grep -c 'ContextVar' /opt/rawlead/src/ai_analyze.py && "
        "systemctl restart rawlead-radar rawlead-api && sleep 5 && "
        "systemctl is-active rawlead-radar rawlead-api && "
        "echo o283_mimo_ok",
        check=False,
    )
    print((out or "").strip())
    ok = "o283_mimo_ok" in (out or "") and (out or "").count("active") >= 2
    print("DEPLOY OK" if ok else "DEPLOY CHECK — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
