#!/usr/bin/env python3
"""O114+O115: vacancy filter + TG health deploy → VPS rawlead-api / rawlead-radar."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_SRC_FILES = (
    "vacancy_filter.py",
    "ai_analyze.py",
)
_SCRIPT_FILES = ("backfill_vacancy_hide.py", "o115_tg_feed_health.py")


def main() -> int:
    print("=== O114+O115 deploy ===")
    for name in _SRC_FILES:
        local = _ROOT / "src" / name
        remote = f"/opt/rawlead/src/{name}"
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up src/{name}")

    for name in _SCRIPT_FILES:
        local = _ROOT / "scripts" / name
        remote = f"/opt/rawlead/scripts/{name}"
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up scripts/{name}")

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-radar && sleep 3 && "
        "systemctl is-active rawlead-api rawlead-radar && "
        "grep -c 'VACANCY (O114)' /opt/rawlead/src/ai_analyze.py && "
        "grep -c is_staff_vacancy /opt/rawlead/src/vacancy_filter.py && "
        "pgrep -af tg_main.py | head -2; "
        "tail -5 /opt/rawlead/data/radar_site_tg.log 2>/dev/null; "
        "echo o114_ok",
        check=False,
    )
    print((out or "").strip())
    text = out or ""
    ok = text.count("active") >= 2 and "o114_ok" in text
    if ok:
        print("DEPLOY OK — run backfill on VPS if needed:")
        print("  cd /opt/rawlead && sudo -u rawlead .venv/bin/python scripts/backfill_vacancy_hide.py --dry-run")
        return 0
    print("DEPLOY CHECK — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
