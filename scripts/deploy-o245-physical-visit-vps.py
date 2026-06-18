#!/usr/bin/env python3
"""O245: onsite/physical service markers + backfill delist — radar+api."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_RADAR_FILES = (
    "src/vacancy_filter.py",
    "src/ai_analyze.py",
    "scripts/backfill_o245_physical_visit.py",
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
    print("=== O245 deploy: physical/onsite guard ===")
    remotes = _upload(_RADAR_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 6 && "
        "systemctl is-active rawlead-api rawlead-radar && "
        "grep -c 'с указанием адреса' /opt/rawlead/src/vacancy_filter.py && "
        "echo o245_deploy_ok",
        check=False,
    )
    print(out.strip())
    ok = "o245_deploy_ok" in (out or "") and (out or "").count("active") >= 2
    if not ok:
        print("DEPLOY CHECK — verify manually")
        return 1

    print("=== O245 backfill delist ===")
    _, vps_out, _ = ssh.run(
        "cd /opt/rawlead && sudo -u rawlead env RADAR_PROFILE=site "
        "PYTHONPATH=/opt/rawlead/src .venv/bin/python "
        "scripts/backfill_o245_physical_visit.py",
        check=False,
    )
    print((vps_out or "").strip())
    print("DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
