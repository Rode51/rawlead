#!/usr/bin/env python3
"""O207b: TG filter soft bypass — radar restart + replay script."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_RADAR_FILES = (
    "src/filters.py",
    "src/tg_spam_filter.py",
)
_SCRIPT_FILES = ("scripts/tg_filter_replay.py",)


def _upload(files: tuple[str, ...]) -> list[str]:
    remotes: list[str] = []
    for rel in files:
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(_ROOT / rel, remote)
        remotes.append(remote)
        print("up", rel)
    return remotes


def main() -> int:
    print("=== O207b deploy: TG filter soft bypass (radar) ===")
    remotes = _upload(_RADAR_FILES + _SCRIPT_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))
    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar && sleep 4 && "
        "systemctl is-active rawlead-radar && "
        "grep -c TG_WIDE_SOFT_STOPS /opt/rawlead/src/filters.py && "
        "grep -c tg_filter_soft_bypass /opt/rawlead/src/filters.py && "
        "echo o207b_radar_ok",
        check=False,
    )
    print(out.strip())
    ok = "o207b_radar_ok" in (out or "") and "active" in (out or "")
    if not ok:
        print("DEPLOY CHECK — verify manually")
        return 1

    _, replay_out, _ = ssh.run(
        "cd /opt/rawlead && "
        "test -f data/tg_history_sample_labeled.json && "
        ".venv/bin/python scripts/tg_filter_replay.py "
        "--in data/tg_history_sample_labeled.json "
        "--out data/tg_filter_replay_o207b_post.json 2>&1 | tail -8 && "
        "echo o207b_replay_ok",
        check=False,
    )
    print(replay_out.strip())
    if "o207b_replay_ok" not in (replay_out or ""):
        print("RADAR OK — replay skipped (no labeled sample on VPS)")
        return 0
    print("DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
