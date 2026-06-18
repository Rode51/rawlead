#!/usr/bin/env python3
"""O222: FL hard reset on first ban — radar+api restart."""
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
    print("=== O222 deploy: FL hard reset on first ban ===")
    remotes = _upload(_RADAR_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 6 && "
        "systemctl is-active rawlead-api rawlead-radar && "
        "grep -c fl_hard_reset /opt/rawlead/src/exchange_browser_fetch.py && "
        "grep -c _fl_hard_reset_on_ban_enabled /opt/rawlead/src/exchange_proxy.py && "
        "echo o222_deploy_ok",
        check=False,
    )
    print(out.strip())
    ok = "o222_deploy_ok" in (out or "") and (out or "").count("active") >= 2
    if ok:
        print("DEPLOY OK — tail radar log for listing:fl parsed>=25")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
