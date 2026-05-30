#!/usr/bin/env python3
"""O71: nginx SSL for api.rawlead.ru + smoke curl https."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

NGINX_CONF = _ROOT / "deploy" / "nginx" / "api.rawlead.ru.conf"
REMOTE_CONF = "/opt/rawlead/deploy/nginx/api.rawlead.ru.conf"
ENABLED = "/etc/nginx/sites-enabled/api.rawlead.ru.conf"


def _cert_paths() -> tuple[str, str]:
    """Pick live cert dir: api.rawlead.ru or combined rawlead.ru SAN."""
    for name in ("api.rawlead.ru", "rawlead.ru"):
        chain = f"/etc/letsencrypt/live/{name}/fullchain.pem"
        _, out, _ = ssh.run(f"test -f {chain} && echo OK || echo MISSING", check=False)
        if "OK" in (out or ""):
            return (
                f"/etc/letsencrypt/live/{name}/fullchain.pem",
                f"/etc/letsencrypt/live/{name}/privkey.pem",
            )
    return (
        "/etc/letsencrypt/live/api.rawlead.ru/fullchain.pem",
        "/etc/letsencrypt/live/api.rawlead.ru/privkey.pem",
    )


def _patch_conf_cert_paths(chain: str, key: str) -> None:
    text = NGINX_CONF.read_text(encoding="utf-8")
    lines = text.splitlines()
    out: list[str] = []
    for line in lines:
        if line.strip().startswith("ssl_certificate "):
            out.append(f"    ssl_certificate     {chain};")
        elif line.strip().startswith("ssl_certificate_key "):
            out.append(f"    ssl_certificate_key {key};")
        else:
            out.append(line)
    patched = "\n".join(out) + "\n"
    tmp = _ROOT / "data" / "_o71_api_nginx.conf"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(patched, encoding="utf-8")
    ssh.upload(tmp, REMOTE_CONF)


def _ensure_cert() -> None:
    chain, _ = _cert_paths()
    _, out, _ = ssh.run(f"test -f {chain} && echo HAS || echo NO", check=False)
    if "HAS" in (out or ""):
        print("cert exists:", chain)
        return
    print("obtaining cert via certbot …")
    # Temp HTTP-only vhost so nginx -t passes before cert exists.
    bootstrap = """server {
    listen 80;
    listen [::]:80;
    server_name api.rawlead.ru;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""
    tmp = _ROOT / "data" / "_o71_api_nginx_bootstrap.conf"
    tmp.write_text(bootstrap, encoding="utf-8")
    ssh.upload(tmp, REMOTE_CONF)
    ssh.run(f"ln -sf {REMOTE_CONF} {ENABLED}")
    ssh.run("nginx -t && systemctl reload nginx")
    ssh.run(
        "certbot certonly --nginx -d api.rawlead.ru "
        "--non-interactive --agree-tos --register-unsafely-without-email",
        check=False,
    )
    _, out2, _ = ssh.run(f"test -f {chain} && echo HAS || echo NO", check=False)
    if "HAS" not in (out2 or ""):
        raise RuntimeError("certbot failed — no cert at " + chain)


def _smoke() -> str:
    _, out, _ = ssh.run(
        "for u in "
        "'https://api.rawlead.ru/health' "
        "'https://api.rawlead.ru/v1/feed?limit=1' "
        "'https://api.rawlead.ru/v1/skills/catalog'; do "
        "code=$(curl -sS -o /tmp/o71_body -w '%{http_code}' \"$u\"); "
        "echo \"$u -> $code $(head -c 80 /tmp/o71_body)\"; done",
        check=False,
    )
    return out or ""


def main() -> int:
    print("=== O71 api.rawlead.ru SSL ===")
    ssh.run("mkdir -p /opt/rawlead/deploy/nginx /var/www/certbot")
    _ensure_cert()
    chain, key = _cert_paths()
    _patch_conf_cert_paths(chain, key)
    ssh.run(f"ln -sf {REMOTE_CONF} {ENABLED}")
    ssh.run("nginx -t && systemctl reload nginx")
    smoke = _smoke()
    print(smoke)
    ok = all(
        f"{path} -> 200" in smoke.replace("\r", "")
        for path in (
            "https://api.rawlead.ru/health",
            "https://api.rawlead.ru/v1/feed?limit=1",
            "https://api.rawlead.ru/v1/skills/catalog",
        )
    )
    if ok:
        print("O71 SSL SMOKE OK")
        return 0
    print("O71 SSL SMOKE FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
