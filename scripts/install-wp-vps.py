#!/usr/bin/env python3
"""Install WordPress on VPS + theme + RAWLEAD_API_URL; try certbot if DNS ok."""
from __future__ import annotations

import secrets
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_THEME = _ROOT / "wordpress" / "rawlead-kadence-child"


def main() -> int:
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(_ROOT / "scripts" / "prep-vps-env.ps1")],
        check=True,
        cwd=_ROOT,
    )
    sys.path.insert(0, str(_ROOT / "scripts"))
    import deploy_vps_ssh as ssh  # noqa: E402

    wp_pass = secrets.token_urlsafe(16)
    db_pass = secrets.token_urlsafe(16)
    admin_pass = secrets.token_urlsafe(12)

    print("=== WP install on VPS ===")
    ssh.run("echo OK")

    # Detect php-fpm socket
    detect = r"""
PHP_SOCK=$(ls /var/run/php/php*-fpm.sock 2>/dev/null | head -1)
if [ -z "$PHP_SOCK" ]; then
  apt-get update -qq
  apt-get install -y -qq mariadb-server php-fpm php-mysql php-xml php-curl php-mbstring php-zip php-gd php-intl unzip curl
  PHP_SOCK=$(ls /var/run/php/php*-fpm.sock 2>/dev/null | head -1)
fi
echo PHP_SOCK=$PHP_SOCK
"""
    _, out, _ = ssh.run(detect, check=False)
    php_sock = "/var/run/php/php8.3-fpm.sock"
    for line in (out or "").splitlines():
        if line.startswith("PHP_SOCK="):
            php_sock = line.split("=", 1)[1].strip()
            break

    nginx_wp = f"""server {{
    listen 80;
    listen [::]:80;
    server_name rawlead.ru www.rawlead.ru;
    root /var/www/rawlead.ru;
    index index.php index.html;
    client_max_body_size 32M;
    location / {{
        try_files $uri $uri/ /index.php?$args;
    }}
    location ~ \\.php$ {{
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:{php_sock};
    }}
    location ~ /\\.ht {{ deny all; }}
}}
"""
    ssh.run(
        "export DEBIAN_FRONTEND=noninteractive; "
        "apt-get update -qq; apt-get install -y -qq mariadb-server php-fpm php-mysql php-xml php-curl "
        "php-mbstring php-zip php-gd php-intl unzip curl 2>/dev/null || true"
    )

    db_setup = f"""
mysql -e "CREATE DATABASE IF NOT EXISTS rawlead_wp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null || true
mysql -e "CREATE USER IF NOT EXISTS 'rawlead'@'localhost' IDENTIFIED BY '{db_pass}';" 2>/dev/null || true
mysql -e "GRANT ALL ON rawlead_wp.* TO 'rawlead'@'localhost'; FLUSH PRIVILEGES;" 2>/dev/null || true
"""
    ssh.run(db_setup)

    wp_install = f"""
set -e
mkdir -p /var/www/rawlead.ru
cd /var/www/rawlead.ru
if [ ! -f wp-settings.php ]; then
  curl -fsSL https://wordpress.org/latest.tar.gz -o /tmp/wp.tgz
  tar -xzf /tmp/wp.tgz -C /var/www/rawlead.ru --strip-components=1
  rm -f /tmp/wp.tgz
fi
chown -R www-data:www-data /var/www/rawlead.ru
"""
    ssh.run(wp_install)

    # Upload nginx site
    local_ngx = _ROOT / "data" / "vps-staging" / "rawlead.ru.nginx"
    local_ngx.parent.mkdir(parents=True, exist_ok=True)
    local_ngx.write_text(nginx_wp, encoding="utf-8")
    ssh.upload(local_ngx, "/etc/nginx/sites-available/rawlead.ru.conf")
    ssh.run(
        "ln -sf /etc/nginx/sites-available/rawlead.ru.conf /etc/nginx/sites-enabled/rawlead.ru.conf && "
        "nginx -t && systemctl reload nginx"
    )

    # wp-cli
    ssh.run(
        "curl -fsSL https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar "
        "-o /usr/local/bin/wp && chmod +x /usr/local/bin/wp"
    )

    wp_cfg = f"""
cd /var/www/rawlead.ru
if [ ! -f wp-config.php ]; then
  cp wp-config-sample.php wp-config.php
  wp config create --dbname=rawlead_wp --dbuser=rawlead --dbpass='{db_pass}' --dbhost=localhost --allow-root --skip-check
fi
grep -q RAWLEAD_API_URL wp-config.php || sed -i "/^\\/\\* That's all/i define('RAWLEAD_API_URL', 'http://127.0.0.1:8000');\\ndefine('RAWLEAD_TG_BOT_USERNAME', 'rawlead_bot');" wp-config.php
if ! wp core is-installed --allow-root 2>/dev/null; then
  wp core install --url='http://rawlead.ru' --title='RawLead' --admin_user='admin' --admin_password='{admin_pass}' --admin_email='admin@rawlead.ru' --skip-email --allow-root
fi
wp rewrite structure '/%postname%/' --allow-root 2>/dev/null || true
wp rewrite flush --allow-root 2>/dev/null || true
chown -R www-data:www-data /var/www/rawlead.ru
"""
    ssh.run(wp_cfg)

    # Theme upload
    print("upload theme...")
    n = ssh.sync_project(local_root=_THEME, remote_root="/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child")
    print(f"theme files: {n}")
    ssh.run(
        "chown -R www-data:www-data /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child && "
        "cd /var/www/rawlead.ru && wp theme install kadence --allow-root 2>/dev/null || true && "
        "wp theme activate rawlead-kadence-child --allow-root 2>/dev/null || true"
    )

    # Plugin skeleton (marketing pages)
    _PLUGIN = _ROOT / "wordpress" / "rawlead-landing"
    if _PLUGIN.is_dir():
        print("upload rawlead-landing plugin...")
        ssh.sync_project(
            local_root=_PLUGIN,
            remote_root="/var/www/rawlead.ru/wp-content/plugins/rawlead-landing",
        )
        ssh.run("chown -R www-data:www-data /var/www/rawlead.ru/wp-content/plugins/rawlead-landing")

    # Pages lenta / cabinet + marketing skeleton
    pages = r"""
cd /var/www/rawlead.ru
PLUGIN=/var/www/rawlead.ru/wp-content/plugins/rawlead-landing
if [ -d "$PLUGIN" ]; then
  wp plugin activate rawlead-landing --allow-root 2>/dev/null || true
else
  wp post list --post_type=page --name=lenta --field=ID --allow-root 2>/dev/null | grep -q . || \
    wp post create --post_type=page --post_title='Лента' --post_name=lenta --post_status=publish --allow-root
  wp post list --post_type=page --name=cabinet --field=ID --allow-root 2>/dev/null | grep -q . || \
    wp post create --post_type=page --post_title='Кабинет' --post_name=cabinet --post_status=publish --allow-root
fi
for slug in lenta cabinet; do
  pid=$(wp post list --post_type=page --name=$slug --field=ID --allow-root 2>/dev/null | head -1)
  [ -n "$pid" ] && wp post meta update $pid _wp_page_template page-$slug.php --allow-root 2>/dev/null || true
done
"""
    ssh.run(pages)

    # Upload deploy nginx api + systemd if needed
    ssh.upload(_ROOT / "deploy" / "nginx" / "api.rawlead.ru.conf", "/opt/rawlead/deploy/nginx/api.rawlead.ru.conf")
    ssh.run("ln -sf /opt/rawlead/deploy/nginx/api.rawlead.ru.conf /etc/nginx/sites-enabled/rawlead-api.conf && nginx -t && systemctl reload nginx")

    # DNS + certbot
    _, dns_out, _ = ssh.run("dig +short api.rawlead.ru A; dig +short rawlead.ru A", check=False)
    print("DNS:", (dns_out or "").strip() or "(empty)")
    if (dns_out or "").strip():
        _, cert_out, _ = ssh.run(
            "certbot --nginx -d api.rawlead.ru -d rawlead.ru -d www.rawlead.ru "
            "--non-interactive --agree-tos --register-unsafely-without-email "
            "--redirect 2>&1 | tail -15",
            check=False,
        )
        print(cert_out or "")
        ssh.run(
            "cd /var/www/rawlead.ru && wp option update siteurl 'https://rawlead.ru' --allow-root 2>/dev/null; "
            "wp option update home 'https://rawlead.ru' --allow-root 2>/dev/null || true",
            check=False,
        )
    else:
        print("certbot skipped: DNS not pointing to VPS yet")

    creds = f"""
WP admin: http://rawlead.ru/wp-admin/  user admin  pass {admin_pass}
DB rawlead_wp user rawlead pass {db_pass}
"""
    (_ROOT / "data" / "wp-vps-credentials.txt").write_text(creds, encoding="utf-8")
    print(creds)
    print("saved data/wp-vps-credentials.txt (local, gitignored via data/)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
