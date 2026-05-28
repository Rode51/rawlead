#!/usr/bin/env python3
"""E1 deploy: API on Beget VPS. Uses VPS_SSH_* from .env (password or key)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_STAGING = _ROOT / "data" / "vps-staging"


def _prep_env() -> None:
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(_ROOT / "scripts" / "prep-vps-env.ps1")],
        check=True,
        cwd=_ROOT,
    )


def main() -> int:
    sys.path.insert(0, str(_ROOT / "scripts"))
    import deploy_vps_ssh as ssh  # noqa: E402

    repo = ssh._env("VPS_GIT_URL", "https://github.com/Rode51/uisness.git")

    print("=== RawLead E1 deploy ===")
    try:
        ssh.run("echo OK")
    except Exception as e:
        print("SSH failed:", e)
        print("Add VPS_SSH_PASSWORD=... to .env (root password from Beget email)")
        return 2

    ssh.install_pubkey_if_password()

    setup = (
        "set -e; export DEBIAN_FRONTEND=noninteractive; "
        "apt-get update -qq; apt-get install -y -qq git python3 python3-venv python3-pip "
        "nginx certbot python3-certbot-nginx rsync; "
        "if ! swapon --show | grep -q swapfile; then "
        "fallocate -l 1G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=1024; "
        "chmod 600 /swapfile; mkswap /swapfile; swapon /swapfile; "
        'grep -q swapfile /etc/fstab || echo "/swapfile none swap sw 0 0" >> /etc/fstab; fi; '
        'id rawlead >/dev/null 2>&1 || adduser --disabled-password --gecos "" rawlead; '
        "mkdir -p /opt/rawlead/data/sessions; chown -R rawlead:rawlead /opt/rawlead"
    )
    print("apt + rawlead user...")
    ssh.run(setup)

    print("sync code from PC (GitHub repo is private)...")
    ssh.run("rm -rf /opt/rawlead && mkdir -p /opt/rawlead && chown -R rawlead:rawlead /opt/rawlead")
    n = ssh.sync_project()
    print(f"uploaded {n} files")

    print("venv + pip...")
    ssh.run(
        "cd /opt/rawlead && sudo -u rawlead test -d .venv || sudo -u rawlead python3 -m venv .venv && "
        "sudo -u rawlead .venv/bin/pip install -q -r requirements.txt && "
        "chmod +x deploy/run-radar-site.sh"
    )

    print("upload .env...")
    for name in (".env", ".env.site"):
        local = _STAGING / name
        if not local.is_file():
            raise FileNotFoundError(local)
        ssh.upload(local, f"/opt/rawlead/{name}")

    ssh.run(
        "chmod 600 /opt/rawlead/.env /opt/rawlead/.env.site && "
        "chown rawlead:rawlead /opt/rawlead/.env /opt/rawlead/.env.site"
    )

    print("systemd + nginx...")
    ssh.run(
        "cp /opt/rawlead/deploy/systemd/rawlead-api.service /etc/systemd/system/ && "
        "cp /opt/rawlead/deploy/systemd/rawlead-radar.service /etc/systemd/system/ && "
        "systemctl daemon-reload && systemctl enable --now rawlead-api && "
        "ln -sf /opt/rawlead/deploy/nginx/api.rawlead.ru.conf /etc/nginx/sites-enabled/rawlead-api.conf && "
        "nginx -t && systemctl reload nginx"
    )

    _, out, _ = ssh.run("curl -s http://127.0.0.1:8000/health || true", check=False)
    print("health:", out.strip() or "(empty)")
    print("Done E1. Next: certbot --nginx -d api.rawlead.ru on VPS")
    return 0


if __name__ == "__main__":
    _prep_env()
    raise SystemExit(main())
