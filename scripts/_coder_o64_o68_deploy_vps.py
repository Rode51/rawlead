#!/usr/bin/env python3
"""O64–O68: sync src/sql/scripts + env + restart API/radar + theme v1.11.13."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def _sync_code() -> None:
    for rel in ("src", "sql", "scripts/l1_backlog_report.py", "scripts/clear_l1_backlog.py"):
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


def _env_legacy_poll() -> None:
    ssh.run(
        "grep -q '^LEGACY_NEON_POLL_SEC=' /opt/rawlead/.env.site && "
        "sed -i 's/^LEGACY_NEON_POLL_SEC=.*/LEGACY_NEON_POLL_SEC=60/' /opt/rawlead/.env.site || "
        "echo 'LEGACY_NEON_POLL_SEC=60' >> /opt/rawlead/.env.site"
    )
    _, out, _ = ssh.run("grep LEGACY_NEON_POLL_SEC /opt/rawlead/.env.site | tail -1", check=False)
    print(out.strip())


def main() -> int:
    print("=== O64–O68 VPS deploy ===")
    _sync_code()
    _env_legacy_poll()
    ssh.run(
        r"find /opt/rawlead/deploy -name '*.sh' -exec sed -i 's/\r$//' {} + && "
        "chmod +x /opt/rawlead/deploy/*.sh && "
        "chown -R rawlead:rawlead /opt/rawlead/src /opt/rawlead/sql /opt/rawlead/scripts"
    )
    for marker, path in (
        ("delist_checker", "/opt/rawlead/src/delist_checker.py"),
        ("radar_status L1", "/opt/rawlead/src/radar_status.py"),
        ("neon_legacy", "/opt/rawlead/src/neon_legacy_consumer.py"),
    ):
        _, out, _ = ssh.run(f"test -f {path} && grep -c '{marker.split()[0]}' {path} | head -1", check=False)
        print(marker, ":", (out or "").strip())

    ssh.run(
        "systemctl restart rawlead-api && sleep 2 && "
        "systemctl restart rawlead-radar && "
        "systemctl restart rawlead-radar-legacy && sleep 2"
    )
    _, out, _ = ssh.run(
        "systemctl is-active rawlead-api rawlead-radar rawlead-radar-legacy",
        check=False,
    )
    print("units:", (out or "").strip())

    theme_rc = subprocess.call(
        [sys.executable, str(_ROOT / "scripts" / "deploy-wp-theme-vps.py")],
        cwd=_ROOT,
    )
    if theme_rc != 0:
        print("WARN theme deploy check script exit", theme_rc)

    _, smoke, _ = ssh.run(
        "curl -s http://127.0.0.1:8000/health; echo; "
        "grep \"define('RAWLEAD_CHILD_VERSION'\" "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1; "
        "grep -c replyCtaHtml "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/assets/js/rawlead-feed.js; "
        "cd /opt/rawlead && sudo -u rawlead .venv/bin/python -c \""
        "import sys; sys.path.insert(0,'src'); "
        "from dotenv import load_dotenv; load_dotenv('.env.site'); load_dotenv('.env'); "
        "from config import load_config; from storage import storage_from_config; "
        "from radar_status import format_status_message; "
        "c=load_config(); m=format_status_message(c, storage_from_config(c)); "
        "print('---STATUS---'); print(m[:1200])\" 2>&1 | tail -40",
        check=False,
    )
    print(smoke)
    s = smoke or ""
    health_ok = '"status"' in s and "ok" in s and "draft_fail_per_hour" in s
    theme_ok = "1.11.13" in s
    status_ok = "L1 48ч" in s or "ИИ:" in s
    units_ok = (out or "").count("active") >= 3
    if units_ok and health_ok and theme_ok:
        print("DEPLOY SMOKE OK", "status_line" if status_ok else "status_check_skip")
        return 0
    print("DEPLOY SMOKE — verify manually")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
