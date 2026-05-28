#!/usr/bin/env python3
"""L3-DEPLOY-PROD: sync L3 code + theme, wp-config bot id, restart API/radar."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_BOT_ID = "8989158953"
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def _apply_neon_010() -> None:
    """Upload sql/010 and apply via psql using DATABASE_URL from .env.site."""
    local_sql = _ROOT / "sql" / "010_user_push_settings.sql"
    if not local_sql.exists():
        print("SKIP missing sql/010_user_push_settings.sql")
        return
    ssh.upload(local_sql, "/opt/rawlead/sql/010_user_push_settings.sql")
    print("up sql/010_user_push_settings.sql")
    _, out, _ = ssh.run(
        "DB_URL=$(grep '^DATABASE_URL=' /opt/rawlead/.env.site | head -1 | cut -d= -f2-) && "
        "[ -z \"$DB_URL\" ] && DB_URL=$(grep '^DATABASE_URL=' /opt/rawlead/.env | head -1 | cut -d= -f2-); "
        "if [ -z \"$DB_URL\" ]; then echo 'NEON-010 SKIP: DATABASE_URL not found'; exit 0; fi && "
        "psql \"$DB_URL\" -f /opt/rawlead/sql/010_user_push_settings.sql && echo 'NEON-010 OK'",
        check=False,
    )
    print(out)


def _sync_code() -> None:
    for rel in (
        "src",
        "deploy",
        "scripts/purge_old_leads.py",
        "scripts/bot_poll_main.py",
        "requirements.txt",
    ):
        local = _ROOT / rel
        if not local.exists():
            print("SKIP missing", rel)
            continue
        if local.is_file():
            remote = f"/opt/rawlead/{rel.replace(chr(92), '/')}"
            ssh.upload(local, remote)
            print("up", rel)
        else:
            n = ssh.sync_project(local_root=local, remote_root=f"/opt/rawlead/{rel}")
            print(f"up {rel}: {n} files")


def main() -> int:
    print("=== L3-DEPLOY-PROD ===")
    _sync_code()
    _apply_neon_010()

    ssh.run(
        "find /opt/rawlead/deploy -name '*.sh' -exec sed -i 's/\\r$//' {} + && "
        "chmod +x /opt/rawlead/deploy/*.sh && "
        "chown -R rawlead:rawlead /opt/rawlead/src /opt/rawlead/deploy /opt/rawlead/scripts"
    )

    ssh.run(
        f"grep -q RAWLEAD_TG_BOT_ID /var/www/rawlead.ru/wp-config.php || "
        f"sed -i \"/^\\/\\* That's all/i define('RAWLEAD_TG_BOT_ID', '{_BOT_ID}');\" "
        f"/var/www/rawlead.ru/wp-config.php"
    )
    ssh.run(
        "grep -q \"RAWLEAD_TG_BOT_USERNAME\" /var/www/rawlead.ru/wp-config.php || "
        "sed -i \"/^\\/\\* That's all/i define('RAWLEAD_TG_BOT_USERNAME', 'rawlead_bot');\" "
        "/var/www/rawlead.ru/wp-config.php"
    )
    ssh.run(
        "grep -q \"RAWLEAD_API_URL\" /var/www/rawlead.ru/wp-config.php || "
        "sed -i \"/^\\/\\* That's all/i define('RAWLEAD_API_URL', 'http://127.0.0.1:8000');\" "
        "/var/www/rawlead.ru/wp-config.php"
    )

    ssh.run(
        f"grep -q '^TELEGRAM_BOT_USER_ID=' /opt/rawlead/.env.site && "
        f"sed -i 's/^TELEGRAM_BOT_USER_ID=.*/TELEGRAM_BOT_USER_ID={_BOT_ID}/' /opt/rawlead/.env.site || "
        f"echo 'TELEGRAM_BOT_USER_ID={_BOT_ID}' >> /opt/rawlead/.env.site"
    )
    ssh.run(
        "grep -q '^RAWLEAD_BOT_POLL_EXTERNAL=' /opt/rawlead/.env.site && "
        "sed -i 's/^RAWLEAD_BOT_POLL_EXTERNAL=.*/RAWLEAD_BOT_POLL_EXTERNAL=1/' /opt/rawlead/.env.site || "
        "echo 'RAWLEAD_BOT_POLL_EXTERNAL=1' >> /opt/rawlead/.env.site"
    )

    ssh.run(
        "cd /opt/rawlead && sudo -u rawlead .venv/bin/pip install -q -r requirements.txt"
    )

    ssh.run(
        "sed -i 's/\\r$//' /opt/rawlead/deploy/sudoers.d/rawlead-radar-ctl && "
        "cp /opt/rawlead/deploy/sudoers.d/rawlead-radar-ctl /etc/sudoers.d/rawlead-radar-ctl && "
        "chmod 440 /etc/sudoers.d/rawlead-radar-ctl && visudo -c"
    )

    ssh.run(
        "cp /opt/rawlead/deploy/systemd/rawlead-purge-leads.service /etc/systemd/system/ && "
        "cp /opt/rawlead/deploy/systemd/rawlead-purge-leads.timer /etc/systemd/system/ && "
        "cp /opt/rawlead/deploy/systemd/rawlead-bot-poll.service /etc/systemd/system/ && "
        "systemctl daemon-reload && "
        "systemctl enable --now rawlead-purge-leads.timer && "
        "systemctl enable --now rawlead-bot-poll"
    )

    ssh.run(
        "systemctl restart rawlead-api && "
        "systemctl restart rawlead-bot-poll && "
        "systemctl restart rawlead-radar && "
        "systemctl restart rawlead-radar-legacy"
    )

    theme = _ROOT / "scripts" / "deploy-wp-theme-vps.py"
    import subprocess

    rc = subprocess.call([sys.executable, str(theme)], cwd=_ROOT)
    if rc != 0:
        print("WARN theme deploy check failed")

    _, out, _ = ssh.run(
        "curl -s 'http://127.0.0.1:8000/v1/skills/catalog?mode=full&limit=5' | head -c 400; echo; "
        "curl -s 'http://127.0.0.1:8000/health'; echo; "
        "grep RAWLEAD_TG_BOT_ID /var/www/rawlead.ru/wp-config.php; "
        "grep TELEGRAM_BOT_USER_ID /opt/rawlead/.env.site; "
        "systemctl is-active rawlead-api rawlead-bot-poll rawlead-radar rawlead-radar-legacy; "
        "systemctl is-active rawlead-purge-leads.timer; "
        "DB_URL=$(grep '^DATABASE_URL=' /opt/rawlead/.env.site | head -1 | cut -d= -f2-) && "
        "[ -z \"$DB_URL\" ] && DB_URL=$(grep '^DATABASE_URL=' /opt/rawlead/.env | head -1 | cut -d= -f2-); "
        "psql \"$DB_URL\" -c \"\\d users\" 2>/dev/null | grep -E 'push_min_match|push_enabled' || "
        "echo 'WARN columns not found'",
        check=False,
    )
    print(out)
    if "canonical_tag" in out or "groups" in out:
        print("L3 DEPLOY OK")
        return 0
    print("L3 DEPLOY — verify catalog response manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
