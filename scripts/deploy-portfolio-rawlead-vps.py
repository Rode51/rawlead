#!/usr/bin/env python3
"""Deploy portfolio static export to https://rawlead.ru/portfolio/ (temporary path)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PORTFOLIO = _ROOT / "portfolio"
_OUT = _PORTFOLIO / "out"
_REMOTE_WEB = "/var/www/rawlead.ru/portfolio"
_REMOTE_STAGING = "/opt/rawlead/portfolio-out-rawlead"
_NGINX_CONF = "/etc/nginx/sites-available/rawlead.ru.conf"
_MARKER = "# RAWLEAD_PORTFOLIO_STATIC"

sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

_PORTFOLIO_LOCATIONS = f"""
    {_MARKER}
    location = /portfolio {{
        return 301 /portfolio/;
    }}

    location /portfolio/ {{
        root /var/www/rawlead.ru;
        try_files $uri $uri/ /portfolio/index.html;
    }}
"""


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


def _ensure_nginx_portfolio() -> None:
    _, out, _ = ssh.run(f"grep -c '{_MARKER}' {_NGINX_CONF} || true", check=False)
    count = int((out or "0").strip() or "0")
    if count > 0:
        print(f"nginx: portfolio block already present ({count}x)")
        ssh.run("nginx -t && systemctl reload nginx")
        return

    ssh.run(f"cp {_NGINX_CONF} {_NGINX_CONF}.bak-pre-portfolio")
    patch = (
        f"python3 - <<'PY'\n"
        f"from pathlib import Path\n"
        f"conf = Path('{_NGINX_CONF}')\n"
        f"text = conf.read_text(encoding='utf-8')\n"
        f"block = '''{_PORTFOLIO_LOCATIONS.strip()}'''\n"
        f"needle = '    location / {{'\n"
        f"if block.strip() not in text:\n"
        f"    if needle not in text:\n"
        f"        raise SystemExit('missing location / block in nginx conf')\n"
        f"    text = text.replace(needle, block + '\\n\\n' + needle, 1)\n"
        f"    conf.write_text(text, encoding='utf-8')\n"
        f"    print('patched nginx (first server block)')\n"
        f"else:\n"
        f"    print('marker already in file')\n"
        f"PY"
    )
    ssh.run(patch)
    ssh.run("nginx -t && systemctl reload nginx")
    print("nginx: portfolio location enabled")


def _verify() -> None:
    _, out, _ = ssh.run(
        "curl -fsSI -m 15 https://rawlead.ru/portfolio/ 2>/dev/null | head -8",
        check=False,
    )
    print((out or "").strip())
    _, body, _ = ssh.run(
        "curl -fsS -m 15 https://rawlead.ru/portfolio/ 2>/dev/null | head -c 800",
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
        _ensure_nginx_portfolio()
        _verify()
        return 0

    if not skip_build:
        print("=== npm run build (portfolio, basePath=/portfolio) ===")
        _npm_build()
    elif not (_OUT / "index.html").is_file():
        print("FAIL: --skip-build but portfolio/out/index.html missing")
        return 1

    print("=== rsync portfolio/out -> VPS /var/www/rawlead.ru/portfolio ===")
    n = _upload_out()
    print(f"uploaded {n} files -> {_REMOTE_WEB}")

    print("=== nginx rawlead.ru /portfolio/ ===")
    _ensure_nginx_portfolio()

    print("=== verify ===")
    _verify()
    print("DEPLOY OK: https://rawlead.ru/portfolio/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
