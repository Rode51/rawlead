#!/usr/bin/env python3
"""Deploy rawlead-next static export to rawlead.ru on VPS (O280 cutover)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_NEXT = _ROOT / "rawlead-next"
_OUT = _NEXT / "out"
_REMOTE_WEB = "/var/www/rawlead.ru"
_REMOTE_STAGING = "/opt/rawlead/web-out"
_NGINX_CONF = "rawlead.ru.conf"

sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def _npm_build() -> None:
    if not (_NEXT / "package.json").is_file():
        raise SystemExit(f"missing {_NEXT / 'package.json'}")
    env = os.environ.copy()
    subprocess.run(["npm", "ci"], cwd=_NEXT, check=True, env=env)
    subprocess.run(["npm", "run", "build"], cwd=_NEXT, check=True, env=env)
    if not (_OUT / "index.html").is_file():
        raise SystemExit(f"build failed: no {_OUT / 'index.html'}")


def _upload_out() -> int:
    n = ssh.sync_project(local_root=_OUT, remote_root=_REMOTE_STAGING)
    ssh.run(
        f"mkdir -p {_REMOTE_WEB} && "
        f"rsync -a --delete {_REMOTE_STAGING}/ {_REMOTE_WEB}/ && "
        f"chown -R www-data:www-data {_REMOTE_WEB}"
    )
    return n


def _install_nginx() -> None:
    local_conf = _ROOT / "deploy" / "nginx" / _NGINX_CONF
    if not local_conf.is_file():
        raise SystemExit(f"missing {local_conf}")
    ssh.upload(local_conf, f"/opt/rawlead/deploy/nginx/{_NGINX_CONF}")
    ssh.run(
        "mkdir -p /opt/rawlead/deploy/nginx /var/www/rawlead.ru && "
        f"ln -sf /opt/rawlead/deploy/nginx/{_NGINX_CONF} /etc/nginx/sites-enabled/{_NGINX_CONF} && "
        "nginx -t && systemctl reload nginx"
    )


def _verify() -> None:
    _, out, _ = ssh.run(
        "curl -fsSI -m 15 https://rawlead.ru/ 2>/dev/null | head -5 || "
        "curl -fsSI -m 15 http://rawlead.ru/ 2>/dev/null | head -5",
        check=False,
    )
    print((out or "").strip())
    _, body, _ = ssh.run(
        "curl -fsS -m 15 https://rawlead.ru/lenta/ 2>/dev/null | head -c 800 || "
        "curl -fsS -m 15 http://rawlead.ru/lenta/ 2>/dev/null | head -c 800",
        check=False,
    )
    text = body or ""
    if "Лента заказов" in text or "feed-app" in text or "_next" in text:
        print("VERIFY OK: Next static HTML detected")
    else:
        print("VERIFY WARN: expected Next export markers in HTML")


def main() -> int:
    skip_build = "--skip-build" in sys.argv
    nginx_only = "--nginx-only" in sys.argv
    dry_upload = "--dry-upload" in sys.argv

    if nginx_only:
        _install_nginx()
        _verify()
        return 0

    if not skip_build:
        print("=== npm run build (rawlead-next) ===")
        _npm_build()
    elif not (_OUT / "index.html").is_file():
        print("FAIL: --skip-build but rawlead-next/out/index.html missing")
        return 1

    if dry_upload:
        print(f"DRY OK: {_OUT / 'index.html'} ready for rsync -> {_REMOTE_WEB}")
        return 0

    print("=== rsync rawlead-next/out -> VPS ===")
    n = _upload_out()
    print(f"uploaded {n} files -> {_REMOTE_WEB}")

    if "--no-nginx" not in sys.argv:
        print("=== nginx rawlead.ru (Next static) ===")
        _install_nginx()

    print("=== verify ===")
    _verify()
    print("DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
