#!/usr/bin/env python3
"""Deploy portfolio static export to https://rode51.ru (root)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PORTFOLIO = _ROOT / "portfolio"
_OUT = _PORTFOLIO / "out"
_REMOTE_WEB = "/var/www/rode51.ru"
_REMOTE_STAGING = "/opt/rawlead/portfolio-out-rode51"
_NGINX_CONF = "rode51.ru.conf"

sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402


def _npm_cmd() -> str:
    return "npm.cmd" if os.name == "nt" else "npm"


def _npm_build() -> None:
    if not (_PORTFOLIO / "package.json").is_file():
        raise SystemExit(f"missing {_PORTFOLIO / 'package.json'}")
    npm = _npm_cmd()
    env = os.environ.copy()
    subprocess.run([npm, "ci"], cwd=_PORTFOLIO, check=True, env=env, shell=os.name == "nt")
    subprocess.run([npm, "run", "build"], cwd=_PORTFOLIO, check=True, env=env, shell=os.name == "nt")
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
        "mkdir -p /opt/rawlead/deploy/nginx /var/www/certbot /var/www/rode51.ru && "
        f"ln -sf /opt/rawlead/deploy/nginx/{_NGINX_CONF} /etc/nginx/sites-enabled/{_NGINX_CONF} && "
        "nginx -t && systemctl reload nginx"
    )


def _maybe_certbot() -> str:
    _, out, _ = ssh.run(
        "test -f /etc/letsencrypt/live/rode51.ru/fullchain.pem && echo HAS_CERT || echo NO_CERT",
        check=False,
    )
    if "HAS_CERT" in (out or ""):
        return "cert: existing"
    _, curl_out, _ = ssh.run(
        "curl -fsSI -m 10 https://rode51.ru/ 2>/dev/null | head -1 || echo HTTPS_FAIL",
        check=False,
    )
    if "200" in (curl_out or ""):
        return "cert: https ok"
    return (
        "cert: run once on VPS: certbot --nginx -d rode51.ru -d www.rode51.ru "
        "(DNS must point to VPS)"
    )


def _verify() -> None:
    _, out, _ = ssh.run(
        "curl -fsSI -m 15 https://rode51.ru/ 2>/dev/null | head -5 || "
        "curl -fsSI -m 15 http://rode51.ru/ 2>/dev/null | head -5",
        check=False,
    )
    print((out or "").strip())
    _, body, _ = ssh.run(
        "curl -fsS -m 15 https://rode51.ru/ 2>/dev/null | head -c 800 || "
        "curl -fsS -m 15 http://rode51.ru/ 2>/dev/null | head -c 800",
        check=False,
    )
    text = body or ""
    if "Rode51" in text or "rode51" in text.lower():
        print("VERIFY OK: Rode51 in HTML")
    else:
        print("VERIFY WARN: Rode51 not found in first 800 bytes")


def main() -> int:
    skip_build = "--skip-build" in sys.argv
    nginx_only = "--nginx-only" in sys.argv

    if nginx_only:
        _install_nginx()
        print(_maybe_certbot())
        _verify()
        return 0

    if not skip_build:
        print("=== npm run build (portfolio, root export for rode51.ru) ===")
        _npm_build()
    elif not (_OUT / "index.html").is_file():
        print("FAIL: --skip-build but portfolio/out/index.html missing")
        return 1

    print("=== rsync portfolio/out -> VPS /var/www/rode51.ru ===")
    n = _upload_out()
    print(f"uploaded {n} files -> {_REMOTE_WEB}")

    print("=== nginx rode51.ru ===")
    _install_nginx()
    print(_maybe_certbot())

    print("=== verify ===")
    _verify()
    print("DEPLOY OK: https://rode51.ru/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
