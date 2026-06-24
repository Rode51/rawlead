#!/usr/bin/env python3
"""Deploy YOUDO-IMAP-DISCOVERY to VPS (§ YOUDO-IMAP-DISCOVERY).

Usage:
    .venv/Scripts/python scripts/deploy-youdo-imap-vps.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_DEPLOY_DIR = _ROOT / "deploy" / "systemd"

_SYSTEMD_UNIT = """\
[Unit]
Description=YouDo IMAP Discovery Poller
After=network.target

[Service]
Type=oneshot
User=rawlead
WorkingDirectory=/opt/rawlead
EnvironmentFile=/opt/rawlead/.env.site
ExecStart=/opt/rawlead/.venv/bin/python scripts/youdo_imap_poller.py --once
"""

_SYSTEMD_TIMER = """\
[Unit]
Description=YouDo IMAP Discovery Timer (90s)

[Timer]
OnBootSec=60
OnUnitActiveSec=90
AccuracySec=10
Unit=rawlead-youdo-imap.service

[Install]
WantedBy=timers.target
"""


def main() -> int:
    print("=== YOUDO-IMAP-DISCOVERY deploy ===")

    # Write systemd files locally for review
    _DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
    unit_path = _DEPLOY_DIR / "rawlead-youdo-imap.service"
    timer_path = _DEPLOY_DIR / "rawlead-youdo-imap.timer"

    unit_path.write_text(_SYSTEMD_UNIT, encoding="utf-8")
    timer_path.write_text(_SYSTEMD_TIMER, encoding="utf-8")
    print(f"Written: {unit_path}")
    print(f"Written: {timer_path}")

    # Upload via deploy_vps_ssh
    sys.path.insert(0, str(_ROOT / "scripts"))
    from deploy_vps_ssh import connect

    client = connect()
    try:
        sftp = client.open_sftp()

        # Upload src/youdo_imap.py → /opt/rawlead/src/
        for rel in (
            "src/youdo_imap.py",
            "src/lead_pipeline.py",
            "src/pg_storage.py",
        ):
            src_file = _ROOT / rel
            if src_file.exists():
                remote_path = f"/opt/rawlead/{rel}"
                sftp.put(str(src_file), remote_path)
                print(f"SCP: {rel} → {remote_path}")

        # Upload scripts/youdo_imap_poller.py → /opt/rawlead/scripts/
        poller_file = _ROOT / "scripts" / "youdo_imap_poller.py"
        if poller_file.exists():
            remote_path = "/opt/rawlead/scripts/youdo_imap_poller.py"
            sftp.put(str(poller_file), remote_path)
            print(f"SCP: scripts/youdo_imap_poller.py → {remote_path}")

        sftp.close()

        # Upload systemd units
        for unit_file in [unit_path, timer_path]:
            sftp = client.open_sftp()
            remote = f"/etc/systemd/system/{unit_file.name}"
            sftp.put(str(unit_file), remote)
            sftp.close()
            print(f"SCP: {unit_file.name} → {remote}")

        # Enable + start timer
        _, stdout, stderr = client.exec_command(
            "systemctl daemon-reload && systemctl enable --now rawlead-youdo-imap.timer"
        )
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        if out.strip():
            print(f"systemctl: {out.strip()}")
        if err.strip():
            print(f"  stderr: {err.strip()}")

        _, stdout, _ = client.exec_command(
            "systemctl restart rawlead-radar && systemctl status rawlead-youdo-imap.timer --no-pager"
        )
        print(f"status:\n{stdout.read().decode('utf-8', errors='replace')}")

    finally:
        client.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
