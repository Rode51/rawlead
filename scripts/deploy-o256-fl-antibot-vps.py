#!/usr/bin/env python3
"""O256: FL soft antibot detect + html_snip log — fl_parser + radar_status + ops hook."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_RADAR_FILES = (
    "src/fl_parser.py",
    "src/radar_status.py",
    "src/ops_funnel.py",
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
    print("=== O256 deploy: FL antibot soft-detect ===")
    remotes = _upload(_RADAR_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 8 && "
        "systemctl is-active rawlead-api rawlead-radar && "
        "grep -c 'fl_listing:soft_antibot_reset' /opt/rawlead/src/fl_parser.py && "
        "grep -c 'fl_listing:html_snip' /opt/rawlead/src/fl_parser.py && "
        "grep -c fl_antibot_soft_active /opt/rawlead/src/radar_status.py && "
        "grep -c apply_fl_antibot_soft_ops_row /opt/rawlead/src/ops_funnel.py && "
        "grep 'listing:fl' /opt/rawlead/data/radar_site.log | tail -3 && "
        "echo o256_deploy_ok",
        check=False,
    )
    print((out or "").strip())
    ok = "o256_deploy_ok" in (out or "") and (out or "").count("active") >= 2
    if ok:
        print("DEPLOY OK — watch fl_listing:html_snip / soft_antibot_reset in radar log")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
