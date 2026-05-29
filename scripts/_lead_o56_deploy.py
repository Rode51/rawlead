#!/usr/bin/env python3
"""O56: API + draft_jobs migration + WP theme v1.10.8."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def main() -> int:
    print("=== O56 API deploy ===")
    n = ssh.sync_project()
    print(f"synced {n} files -> /opt/rawlead")
    ssh.run(
        r"find /opt/rawlead/deploy -name '*.sh' -exec sed -i 's/\r$//' {} \; && "
        "chmod +x /opt/rawlead/deploy/*.sh"
    )
    ssh.run("chown -R rawlead:rawlead /opt/rawlead/src /opt/rawlead/scripts /opt/rawlead/tests")
    _, out, _ = ssh.run(
        "test -f /opt/rawlead/src/draft_async.py && echo OK || echo MISSING",
        check=False,
    )
    print("draft_async.py:", (out or "").strip())
    _, mig, _ = ssh.run(
        r"cd /opt/rawlead && python3 -c \""
        "import sys; sys.path.insert(0,'src'); "
        "from config import load_config, load_radar_env, apply_profile_argv; "
        "from draft_async import _ensure_draft_tables; "
        "apply_profile_argv(); load_radar_env(); c=load_config(); "
        "_ensure_draft_tables(c.database_url); print('draft_jobs OK')\"",
        check=False,
    )
    print("migration:", (mig or "").strip())
    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-bot-poll && sleep 3 && "
        "systemctl is-active rawlead-api rawlead-bot-poll",
        check=False,
    )
    print("services:", (out or "").strip())
    _, code, _ = ssh.run(
        "curl -s -o /dev/null -w '%{http_code}' 'http://127.0.0.1:8000/v1/feed?limit=1'",
        check=False,
    )
    print("feed HTTP:", (code or "").strip())

    print("=== O56 theme deploy ===")
    theme = Path(__file__).resolve().parents[1] / "wordpress" / "rawlead-kadence-child"
    tn = ssh.sync_project(local_root=theme, remote_root="/opt/rawlead/wordpress/rawlead-kadence-child")
    print(f"theme synced {tn} files")
    ssh.run(
        "rsync -a /opt/rawlead/wordpress/rawlead-kadence-child/ "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/ && "
        "chown -R www-data:www-data /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child"
    )
    _, ver, _ = ssh.run(
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1",
        check=False,
    )
    print("theme version:", (ver or "").strip())

    active = (out or "").count("active") >= 2
    ok_api = active and (code or "").strip() == "200" and "OK" in (mig or "")
    ok_theme = "1.10.8" in (ver or "")
    return 0 if ok_api and ok_theme else 1


if __name__ == "__main__":
    raise SystemExit(main())
