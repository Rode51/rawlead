#!/usr/bin/env python3
"""O174b: YooKassa env sync + billing deploy.

Webhook (YooKassa LK): POST https://api.rawlead.ru/v1/webhooks/yookassa · event payment.succeeded
Recurring/autopay: set YOOKASSA_SAVE_PAYMENT_METHOD=1 only after YooKassa manager enables
recurring payments for the shop (otherwise checkout shows "can't make recurring payments").
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

THEME_VER = "1.18.65"
_ENV_KEYS = (
    "YOOKASSA_SHOP_ID",
    "YOOKASSA_SECRET_KEY",
    "YOOKASSA_RETURN_URL",
    "YOOKASSA_WEBHOOK_SECRET",
    "YOOKASSA_SAVE_PAYMENT_METHOD",
)

_SRC_FILES = (
    "api_server.py",
    "config.py",
    "yookassa_billing.py",
    "trial_subscription.py",
    "telegram_control.py",
)

_THEME_FILES = (
    "wordpress/rawlead-kadence-child/functions.php",
    "wordpress/rawlead-kadence-child/inc/rawlead-api.php",
    "wordpress/rawlead-kadence-child/inc/marketing.php",
    "wordpress/rawlead-kadence-child/page-cabinet.php",
    "wordpress/rawlead-kadence-child/template-parts/rawlead/pricing-card.php",
    "wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js",
    "wordpress/rawlead-kadence-child/assets/js/rawlead-pricing.js",
    "wordpress/rawlead-kadence-child/assets/css/rawlead.css",
)


def _read_local_env_site() -> dict[str, str]:
    path = _ROOT / ".env.site"
    if not path.is_file():
        raise FileNotFoundError(path)
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key in _ENV_KEYS:
            out[key] = val.strip()
    return out


def _shell_escape(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _ensure_env_line(key: str, value: str) -> str:
    esc = _shell_escape(value)
    return (
        f"grep -q '^{key}=' /opt/rawlead/.env.site && "
        f"sed -i 's|^{key}=.*|{key}={esc}|' /opt/rawlead/.env.site || "
        f"echo '{key}={esc}' >> /opt/rawlead/.env.site"
    )


def sync_yookassa_env() -> str:
    local = _read_local_env_site()
    if not local.get("YOOKASSA_SHOP_ID") or not local.get("YOOKASSA_SECRET_KEY"):
        raise RuntimeError("YOOKASSA_SHOP_ID / YOOKASSA_SECRET_KEY missing in local .env.site")
    # Default off: shop must have recurring enabled in YooKassa LK before =1
    if "YOOKASSA_SAVE_PAYMENT_METHOD" not in local:
        local["YOOKASSA_SAVE_PAYMENT_METHOD"] = "0"
    parts = [_ensure_env_line(k, local[k]) for k in _ENV_KEYS if local.get(k)]
    parts.append("chmod 600 /opt/rawlead/.env.site")
    parts.append("grep '^YOOKASSA_SHOP_ID=' /opt/rawlead/.env.site")
    parts.append(
        "grep '^YOOKASSA_SECRET_KEY=' /opt/rawlead/.env.site | "
        "sed 's/\\(live_\\).\\{4\\}/\\1****/;s/\\(test_\\).\\{4\\}/\\1****/'"
    )
    _, out, err = ssh.run(" && ".join(parts), check=False)
    return (out or err or "").strip()


def _apply_neon_migration() -> str:
    local_sql = _ROOT / "sql" / "021_yookassa_payments.sql"
    if not local_sql.is_file():
        return "SKIP sql/021 missing"
    ssh.upload(local_sql, "/opt/rawlead/sql/021_yookassa_payments.sql")
    _, out, _ = ssh.run(
        "set -a && source /opt/rawlead/.env.site 2>/dev/null; set +a; "
        'if [ -z "$DATABASE_URL" ]; then echo "SKIP: DATABASE_URL missing in .env.site"; exit 0; fi; '
        "/opt/rawlead/.venv/bin/python - <<'PY'\n"
        "import os, pathlib, psycopg\n"
        "url = os.environ.get('DATABASE_URL') or ''\n"
        "sql = pathlib.Path('/opt/rawlead/sql/021_yookassa_payments.sql').read_text(encoding='utf-8')\n"
        "with psycopg.connect(url) as conn:\n"
        "    with conn.cursor() as cur:\n"
        "        cur.execute(sql)\n"
        "    conn.commit()\n"
        "print('NEON-021 OK')\n"
        "PY",
        check=False,
    )
    return (out or "").strip()


def main() -> int:
    print("=== O174b YooKassa deploy ===")
    print("--- t0 env sync ---")
    print(sync_yookassa_env())

    print("--- Neon 021 ---")
    print(_apply_neon_migration())

    for name in _SRC_FILES:
        local = _ROOT / "src" / name
        remote = f"/opt/rawlead/src/{name}"
        ssh.upload(local, remote)
        ssh.run(f"chown rawlead:rawlead {remote}")
        print(f"up src/{name}")

    for rel in _THEME_FILES:
        local = _ROOT / rel
        remote = "/opt/rawlead/" + rel
        ssh.upload(local, remote)
        print(f"up {rel}")

    ssh.run(
        "rsync -a /opt/rawlead/wordpress/rawlead-kadence-child/ "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/ && "
        "chown -R www-data:www-data /var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child"
    )

    _, out, _ = ssh.run(
        "systemctl restart rawlead-api rawlead-bot-poll && sleep 3 && "
        "systemctl is-active rawlead-api rawlead-bot-poll && "
        "grep -c yookassa_billing /opt/rawlead/src/api_server.py && "
        "grep -c checkout /opt/rawlead/wordpress/rawlead-kadence-child/inc/rawlead-api.php && "
        f"grep RAWLEAD_CHILD_VERSION "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "curl -s http://127.0.0.1:8000/health",
        check=False,
    )
    print((out or "").strip())
    ok = "active" in (out or "") and THEME_VER in (out or "")
    print("O174b DEPLOY OK" if ok else "O174b DEPLOY — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
