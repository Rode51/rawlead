#!/usr/bin/env python3
"""O144-RFP-COMPLY: guard rfp_defer + RFP block в промпте L2."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_FILES = (
    "src/ai_analyze.py",
    "src/l3_human_style.py",
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
    print("=== O144 deploy: RFP ideas guard ===")
    remotes = _upload(_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar rawlead-radar-legacy && sleep 4 && "
        "systemctl is-active rawlead-api rawlead-radar rawlead-radar-legacy && "
        "grep -c '_rfp_defer_instead_of_ideas' /opt/rawlead/src/ai_analyze.py && "
        "grep -c 'RFP' /opt/rawlead/src/l3_human_style.py && "
        "echo o144_ok",
        check=False,
    )
    print((out or "").strip())
    if "o144_ok" not in (out or "") or (out or "").count("active") < 3:
        print("DEPLOY CHECK — verify manually")
        return 1
    print("DEPLOY OK — owner: тест Kwork HoReCa → отклик с 2–3 идеями")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
