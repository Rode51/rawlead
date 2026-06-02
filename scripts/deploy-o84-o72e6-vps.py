#!/usr/bin/env python3
"""O84 bot deep-link auth + O72e-6 reply draft tone · API + bot + theme + Neon 015."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_SRC_FILES = (
    "src/api_server.py",
    "src/telegram_control.py",
    "src/ai_analyze.py",
)

_THEME_MARKER = "startBotLogin"


def _upload_src() -> list[str]:
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
    return remotes


def _apply_neon_015() -> None:
    local_sql = _ROOT / "sql" / "015_auth_bot_sessions.sql"
    if not local_sql.exists():
        print("SKIP missing sql/015_auth_bot_sessions.sql")
        return
    ssh.upload(local_sql, "/opt/rawlead/sql/015_auth_bot_sessions.sql")
    print("up sql/015_auth_bot_sessions.sql")
    _, out, _ = ssh.run(
        "DB_URL=$(grep '^DATABASE_URL=' /opt/rawlead/.env.site | head -1 | cut -d= -f2-) && "
        "[ -z \"$DB_URL\" ] && DB_URL=$(grep '^DATABASE_URL=' /opt/rawlead/.env | head -1 | cut -d= -f2-); "
        "if [ -z \"$DB_URL\" ]; then echo 'NEON-015 SKIP: DATABASE_URL not found'; exit 0; fi && "
        "psql \"$DB_URL\" -f /opt/rawlead/sql/015_auth_bot_sessions.sql && "
        "psql \"$DB_URL\" -c \"\\d auth_bot_sessions\" | head -20 && echo 'NEON-015 OK'",
        check=False,
    )
    print(out or "")


def _deploy_theme() -> None:
    theme = _ROOT / "wordpress" / "rawlead-kadence-child"
    if not theme.is_dir():
        print("SKIP missing theme")
        return
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


def main() -> int:
    print("=== O84 + O72e-6 deploy ===")
    remotes = _upload_src()
    if remotes:
        ssh.run("chown rawlead:rawlead " + " ".join(remotes))

    _apply_neon_015()
    _deploy_theme()

    verify_cmd = " && ".join(
        [
            "systemctl restart rawlead-api rawlead-bot-poll rawlead-radar",
            "sleep 3",
            "systemctl is-active rawlead-api rawlead-bot-poll rawlead-radar",
            "grep -c bot-session /opt/rawlead/src/api_server.py",
            "grep -c 'auth_' /opt/rawlead/src/telegram_control.py",
            f"grep -c {_THEME_MARKER} "
            "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-cabinet.js",
            "grep \"define('RAWLEAD_CHILD_VERSION'\" "
            "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
            "grep -c _validate_reply_draft_opener /opt/rawlead/src/ai_analyze.py",
            "curl -sf http://127.0.0.1:8000/health | head -c 300; echo",
            "curl -sf -o /dev/null -w 'bot-session_http=%{http_code}\\n' "
            "-X POST http://127.0.0.1:8000/v1/auth/bot-session -H 'Content-Type: application/json' -d '{}'",
        ]
    )
    _, out, _ = ssh.run(verify_cmd, check=False)
    print(out or "")

    text = out or ""
    ok = (
        "active" in text
        and "1.11.18" in text
        and "NEON-015 OK" in text
        and "bot-session_http=200" in text
    )
    if ok:
        print("O84 + O72e-6 DEPLOY OK")
        return 0
    if "active" in text and "1.11.18" in text:
        print("O84 + O72e-6 DEPLOY OK (Neon verify skipped — check sql manually)")
        return 0
    print("O84 + O72e-6 DEPLOY — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
