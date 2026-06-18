#!/usr/bin/env python3
"""Deploy portfolio static export to labs.rawlead.ru on VPS."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PORTFOLIO = _ROOT / "portfolio"
_OUT = _PORTFOLIO / "out"
_REMOTE_WEB = "/var/www/labs.rawlead.ru"
_REMOTE_STAGING = "/opt/rawlead/portfolio-out"
_NGINX_CONF = "labs.rawlead.ru.conf"

sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def _npm_build() -> None:
    if not (_PORTFOLIO / "package.json").is_file():
        raise SystemExit(f"missing {_PORTFOLIO / 'package.json'}")
    env = os.environ.copy()
    subprocess.run(["npm", "ci"], cwd=_PORTFOLIO, check=True, env=env)
    subprocess.run(["npm", "run", "build"], cwd=_PORTFOLIO, check=True, env=env)
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
        "mkdir -p /opt/rawlead/deploy/nginx /var/www/certbot /var/www/labs.rawlead.ru && "
        f"ln -sf /opt/rawlead/deploy/nginx/{_NGINX_CONF} /etc/nginx/sites-enabled/{_NGINX_CONF} && "
        "nginx -t && systemctl reload nginx"
    )


def _maybe_certbot() -> str:
    _, out, _ = ssh.run(
        "test -f /etc/letsencrypt/live/labs.rawlead.ru/fullchain.pem && echo HAS_CERT || echo NO_CERT",
        check=False,
    )
    if "HAS_CERT" in (out or ""):
        return "cert: existing"
    _, curl_out, _ = ssh.run(
        "curl -fsSI -m 10 https://labs.rawlead.ru/ 2>/dev/null | head -1 || echo HTTPS_FAIL",
        check=False,
    )
    if "200" in (curl_out or ""):
        return "cert: https ok"
    return (
        "cert: run once on VPS: certbot --nginx -d labs.rawlead.ru "
        "(DNS must point to VPS)"
    )


def _verify() -> None:
    _, out, _ = ssh.run(
        "curl -fsSI -m 15 https://labs.rawlead.ru/ 2>/dev/null | head -5 || "
        "curl -fsSI -m 15 http://labs.rawlead.ru/ 2>/dev/null | head -5",
        check=False,
    )
    print((out or "").strip())
    _, body, _ = ssh.run(
        "curl -fsS -m 15 https://labs.rawlead.ru/ 2>/dev/null | head -c 500 || "
        "curl -fsS -m 15 http://labs.rawlead.ru/ 2>/dev/null | head -c 500",
        check=False,
    )
    text = body or ""
    if "Rode51" in text:
        print("VERIFY OK: title Rode51 in HTML")
    else:
        print("VERIFY WARN: Rode51 not found in first 500 bytes")


def main() -> int:
    skip_build = "--skip-build" in sys.argv
    nginx_only = "--nginx-only" in sys.argv

    if nginx_only:
        _install_nginx()
        print(_maybe_certbot())
        _verify()
        return 0

    if not skip_build:
        print("=== npm run build (portfolio) ===")
        _npm_build()
    else:
        if not (_OUT / "index.html").is_file():
            print("FAIL: --skip-build but portfolio/out/index.html missing")
            return 1

    print("=== rsync portfolio/out -> VPS ===")
    n = _upload_out()
    print(f"uploaded {n} files -> {_REMOTE_WEB}")

    print("=== nginx labs.rawlead.ru ===")
    _install_nginx()
    print(_maybe_certbot())

    print("=== verify ===")
    _verify()
    print("DEPLOY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
