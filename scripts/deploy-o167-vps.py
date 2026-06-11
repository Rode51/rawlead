#!/usr/bin/env python3
"""O167-SORT-SOURCE: exchange filter in sort dropdown (rawlead-feed.js)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== O167 theme deploy (sort source filter) ===")
    if subprocess.call([sys.executable, str(_ROOT / "scripts" / "deploy-wp-theme-vps.py")]) != 0:
        return 1
    _, out, _ = ssh.run(
        "grep -c 'SORT_SOURCES' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js && "
        "grep -c 'rl-feed-sort-source' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js",
        check=False,
    )
    print((out or "").strip())
    lines = [x.strip() for x in (out or "").splitlines() if x.strip().isdigit()]
    if len(lines) >= 2 and int(lines[0]) >= 1 and int(lines[1]) >= 2:
        print("=== O167 DEPLOY OK ===")
        return 0
    print("O167 DEPLOY CHECK — verify rawlead-feed.js on VPS")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
