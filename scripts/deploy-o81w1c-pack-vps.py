#!/usr/bin/env python3
"""O81-w1c flow cards + pack: theme, O86/O78 API, O72e-6 ai_analyze."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_SRC_FILES = (
    "src/owner_admin.py",
    "src/telegram_control.py",
    "src/match_push.py",
    "src/api_server.py",
    "src/ai_analyze.py",
)


def main() -> int:
    print("=== O81-w1c pack deploy (theme + API + ai_analyze) ===")
    remotes: list[str] = []
    for rel in _SRC_FILES:
        local = _ROOT / rel
        if not local.is_file():
            print("SKIP missing", rel)
            continue
        remote = "/opt/rawlead/" + rel.replace("\\", "/")
        ssh.upload(local, remote)
        remotes.append(remote)
        print("up", rel)
    if remotes:
        ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    theme = _ROOT / "wordpress" / "rawlead-kadence-child"
    n = ssh.sync_project(
        local_root=theme,
        remote_root="/opt/rawlead/wordpress/rawlead-kadence-child",
    )
    print(f"theme uploaded {n} files")
    ssh.run(
        "rsync -a /opt/rawlead/wordpress/rawlead-kadence-child/ "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/ && "
        "chown -R www-data:www-data /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child"
    )

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-bot-poll && sleep 4 && "
        "systemctl is-active rawlead-api rawlead-bot-poll && "
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "grep -c flyVectorForCard "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-flow.js",
        check=False,
    )
    print(out or "")
    text = out or ""
    ok = "active" in text and "1.11." in text
    print("O81-w1c PACK DEPLOY OK" if ok else "O81-w1c PACK — verify manually on https://rawlead.ru/")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
