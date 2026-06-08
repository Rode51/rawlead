#!/usr/bin/env python3
"""O141-EXCHANGE-PARITY: detail TZ all web sources + TG labels + secondary every cycle."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_RADAR_FILES = (
    "src/exchange_detail.py",
    "src/lead_pipeline.py",
    "src/youdo_parser.py",
    "src/freelance_ru_parser.py",
    "src/freelancejob_parser.py",
    "src/pchyol_parser.py",
    "src/telegram_notify.py",
    "src/main.py",
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
    print("=== O141 deploy: exchange detail parity ===")
    remotes = _upload(_RADAR_FILES)
    ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    _, out, _ = ssh.run(
        "systemctl restart rawlead-radar rawlead-radar-legacy rawlead-api && sleep 4 && "
        "systemctl is-active rawlead-radar rawlead-radar-legacy rawlead-api && "
        "grep -c is_web_detail_source /opt/rawlead/src/exchange_detail.py && "
        "grep -c 'SECONDARY_FETCH_EVERY_N_CYCLES\", \"1\"' /opt/rawlead/src/main.py && "
        "grep -c SOURCE_LABELS /opt/rawlead/src/telegram_notify.py && "
        "echo o141_ok",
        check=False,
    )
    print((out or "").strip())
    if "o141_ok" not in (out or "") or (out or "").count("active") < 3:
        print("DEPLOY CHECK — verify manually")
        return 1
    print("DEPLOY OK — VPS: fresh youdo lead length(body)>500; radar push:match YouDo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
