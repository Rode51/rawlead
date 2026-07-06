#!/usr/bin/env python3
"""E2 deploy: sync code, env, Telethon sessions, enable site + legacy radars on VPS."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_STAGING = _ROOT / "data" / "vps-staging"
_SESSIONS_PC = Path(os.environ.get("TELETHON_SESSIONS_DIR", "./data/sessions"))
_SESSION_FILES = (
    "acc1_telethon.session",
    "acc2_telethon.session",
    "acc3_telethon.session",
    "acc4_telethon.session",
    "acc5_telethon.session",
)


def main() -> int:
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(_ROOT / "scripts" / "prep-vps-env.ps1"),
        ],
        check=True,
        cwd=_ROOT,
    )
    sys.path.insert(0, str(_ROOT / "scripts"))
    import deploy_vps_ssh as ssh  # noqa: E402

    print("=== finish E2 (site + legacy radars) ===")
    ssh.run("echo OK")

    for rel in ("src", "deploy", "scripts", "requirements.txt", "sql"):
        local = _ROOT / rel
        if not local.exists():
            continue
        if local.is_file():
            ssh.upload(local, f"/opt/rawlead/{rel}")
            print("up", rel)
        else:
            n = ssh.sync_project(local_root=local, remote_root=f"/opt/rawlead/{rel}")
            print(f"up {rel}: {n} files")

    for name in (".env", ".env.site", ".env.legacy"):
        path = _STAGING / name
        if not path.is_file():
            print("SKIP missing staging", name)
            continue
        ssh.upload(path, f"/opt/rawlead/{name}")
        print("up", name)

    ssh.run("mkdir -p /opt/rawlead/data/sessions /opt/rawlead/data")
    for fname in _SESSION_FILES:
        local = _SESSIONS_PC / fname
        if not local.is_file():
            print("WARN missing session", local)
            continue
        remote = f"/opt/rawlead/data/sessions/{fname}"
        ssh.upload(local, remote)
        print("up session", fname)

    ssh.run(
        "chown -R rawlead:rawlead /opt/rawlead && "
        "chmod 600 /opt/rawlead/.env /opt/rawlead/.env.site /opt/rawlead/.env.legacy && "
        "sed -i 's/\\r$//' /opt/rawlead/deploy/run-radar-site.sh /opt/rawlead/deploy/run-radar-legacy.sh && "
        "chmod +x /opt/rawlead/deploy/run-radar-site.sh /opt/rawlead/deploy/run-radar-legacy.sh"
    )

    ssh.run(
        "cd /opt/rawlead && sudo -u rawlead test -d .venv || sudo -u rawlead python3 -m venv .venv && "
        "sudo -u rawlead .venv/bin/pip install -q -r requirements.txt"
    )

    ssh.run(
        "cp /opt/rawlead/deploy/systemd/rawlead-api.service /etc/systemd/system/ && "
        "cp /opt/rawlead/deploy/systemd/rawlead-radar.service /etc/systemd/system/ && "
        "cp /opt/rawlead/deploy/systemd/rawlead-radar-legacy.service /etc/systemd/system/ && "
        "systemctl daemon-reload && "
        "systemctl enable rawlead-api rawlead-radar rawlead-radar-legacy && "
        "systemctl restart rawlead-api && "
        "systemctl restart rawlead-radar && "
        "systemctl restart rawlead-radar-legacy"
    )

    _, out, _ = ssh.run(
        "sleep 3; "
        "curl -s http://127.0.0.1:8000/health; echo; "
        "systemctl is-active rawlead-api rawlead-radar rawlead-radar-legacy; "
        "ls -la /opt/rawlead/data/sessions/ | head -6",
        check=False,
    )
    print(out)

    _, logs, _ = ssh.run(
        "tail -5 /opt/rawlead/data/radar_site.log 2>/dev/null || "
        "journalctl -u rawlead-radar -n 8 --no-pager 2>&1 | tail -8",
        check=False,
    )
    print("--- site log ---")
    print(logs)

    _, llogs, _ = ssh.run(
        "tail -5 /opt/rawlead/data/radar_legacy.log 2>/dev/null || "
        "journalctl -u rawlead-radar-legacy -n 8 --no-pager 2>&1 | tail -8",
        check=False,
    )
    print("--- legacy log ---")
    sys.stdout.buffer.write((llogs or "").encode("utf-8", errors="replace"))

    ok = "ok" in (out or "").lower() and out.count("active") >= 3
    if ok:
        print("E2 OK")
        return 0
    print("E2 CHECK FAILED — см. логи выше")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
