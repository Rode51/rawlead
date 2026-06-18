#!/usr/bin/env python3
"""O207: upload TG funnel scripts + run t1 audit on VPS (no radar restart)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_SCRIPT_FILES = (
    "scripts/tg_funnel_audit.py",
    "scripts/tg_history_sample.py",
    "scripts/tg_filter_replay.py",
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
    print("=== O207 deploy: TG funnel audit + sample + replay scripts ===")
    remotes = _upload(_SCRIPT_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "test -f /opt/rawlead/scripts/tg_funnel_audit.py && "
        "test -f /opt/rawlead/scripts/tg_history_sample.py && "
        "test -f /opt/rawlead/scripts/tg_filter_replay.py && "
        "cd /opt/rawlead && .venv/bin/python scripts/tg_funnel_audit.py "
        "--log data/radar_site.log "
        "--out data/tg_funnel_audit.json "
        "--human-out data/tg_funnel_audit_human.md 2>&1 | tail -12 && "
        "echo o207_ok",
        check=False,
    )
    print(out.strip())
    ok = "o207_ok" in (out or "") and "days_7" in (out or "")
    if ok:
        print("DEPLOY OK (no radar restart)")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
