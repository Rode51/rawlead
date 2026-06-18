#!/usr/bin/env python3
"""O233 + O215 bundle: FL auto-recovery, ban clear, subprocess JSON, ops lamp."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_RADAR_FILES = (
    "src/exchange_proxy.py",
    "src/exchange_browser_fetch.py",
    "src/fl_parser.py",
    "src/ops_funnel.py",
    "scripts/fl_fetch_worker.py",
)


def _upload(files: tuple[str, ...]) -> list[str]:
    remotes: list[str] = []
    for rel in files:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    return remotes


def main() -> int:
    print("=== O233 deploy: FL auto-recovery + O215 proxy bundle ===")
    remotes = _upload(_RADAR_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 8 && "
        "systemctl is-active rawlead-api rawlead-radar && "
        "grep -c clear_fl_source_bans /opt/rawlead/src/exchange_proxy.py && "
        "grep -c fl_listing:empty_html /opt/rawlead/src/fl_parser.py && "
        "grep -c _fl_recent_pool_exhausted /opt/rawlead/src/ops_funnel.py && "
        "echo o233_deploy_ok",
        check=False,
    )
    print(out.strip())
    ok = "o233_deploy_ok" in (out or "") and (out or "").count("active") >= 2
    if ok:
        print("DEPLOY OK — tail radar log for listing:fl parsed>=25")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
