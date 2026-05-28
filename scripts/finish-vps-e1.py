#!/usr/bin/env python3
"""Finish E1 on VPS: fix ownership, PYTHONPATH, env, restart API."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_STAGING = _ROOT / "data" / "vps-staging"


def main() -> int:
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(_ROOT / "scripts" / "prep-vps-env.ps1")],
        check=True,
        cwd=_ROOT,
    )
    sys.path.insert(0, str(_ROOT / "scripts"))
    import deploy_vps_ssh as ssh  # noqa: E402

    print("=== finish E1 ===")
    ssh.run("echo OK")

    # Minimal sync: src + deploy + scripts + requirements
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

    for name in (".env", ".env.site"):
        ssh.upload(_STAGING / name, f"/opt/rawlead/{name}")
        print("up", name)

    ssh.run(
        "chown -R rawlead:rawlead /opt/rawlead && "
        "chmod 600 /opt/rawlead/.env /opt/rawlead/.env.site && "
        "chmod +x /opt/rawlead/deploy/run-radar-site.sh"
    )

    ssh.run(
        "cd /opt/rawlead && sudo -u rawlead test -d .venv || sudo -u rawlead python3 -m venv .venv && "
        "sudo -u rawlead .venv/bin/pip install -q -r requirements.txt"
    )

    ssh.run(
        "cp /opt/rawlead/deploy/systemd/rawlead-api.service /etc/systemd/system/ && "
        "cp /opt/rawlead/deploy/systemd/rawlead-radar.service /etc/systemd/system/ && "
        "systemctl daemon-reload && systemctl enable rawlead-api && "
        "systemctl restart rawlead-api && "
        "ln -sf /opt/rawlead/deploy/nginx/api.rawlead.ru.conf /etc/nginx/sites-enabled/rawlead-api.conf && "
        "nginx -t && systemctl reload nginx"
    )

    _, out, _ = ssh.run("sleep 2; curl -s http://127.0.0.1:8000/health; systemctl is-active rawlead-api", check=False)
    print(out)
    if "ok" in (out or "").lower() and "active" in (out or ""):
        print("E1 OK")
        return 0
    _, log, _ = ssh.run("journalctl -u rawlead-api -n 8 --no-pager 2>&1 | tail -8", check=False)
    print(log)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
