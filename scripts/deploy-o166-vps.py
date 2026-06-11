#!/usr/bin/env python3
"""O166-HOME-MATCH-BAR: live-preview match bar width in rawlead.css."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== O166 theme deploy (match bar live-preview) ===")
    if subprocess.call([sys.executable, str(_ROOT / "scripts" / "deploy-wp-theme-vps.py")]) != 0:
        return 1
    _, out, _ = ssh.run(
        "grep -c 'rl-live-preview .rl-match__fill' "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/css/rawlead.css",
        check=False,
    )
    n = (out or "").strip()
    print("rl-live-preview .rl-match__fill rules:", n)
    if n.isdigit() and int(n) >= 2:
        print("=== O166 DEPLOY OK ===")
        return 0
    print("O166 DEPLOY CHECK — verify CSS on VPS")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
