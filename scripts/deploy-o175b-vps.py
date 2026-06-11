#!/usr/bin/env python3
"""O175b: WP REST proxy forwards feed ?source= to API."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== O175b deploy: WP feed source proxy ===")
    if subprocess.call([sys.executable, str(_ROOT / "scripts" / "deploy-wp-theme-vps.py")]) != 0:
        return 1
    _, out, _ = ssh.run(
        "grep -c \"get_param('source')\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/rawlead-api.php && "
        "grep -c \"query\\['source'\\]\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/inc/rawlead-api.php && "
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "echo o175b_deploy_ok",
        check=False,
    )
    text = out or ""
    print(text)
    if "o175b_deploy_ok" not in text or "1.18.55" not in text:
        print("O175b DEPLOY CHECK FAILED")
        return 1
    print("O175b DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
