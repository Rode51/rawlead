#!/usr/bin/env python3
"""Deploy L3 uniquify hotfix (G6) — ai_analyze + l3_human_style only."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "src/l3_human_style.py",
    "src/ai_analyze.py",
)


def main() -> int:
    remotes: list[str] = []
    for rel in _FILES:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 5 && "
        "systemctl is-active rawlead-api rawlead-radar && echo g6_l3_deploy_ok",
        check=False,
    )
    print(out.strip())
    return 0 if "g6_l3_deploy_ok" in (out or "") else 1


if __name__ == "__main__":
    raise SystemExit(main())
