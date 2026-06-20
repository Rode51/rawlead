#!/usr/bin/env python3
"""O185: trial→790 checkout · payment claim · cabinet copy — VPS deploy."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
import deploy_vps_ssh as ssh  # noqa: E402

THEME_VER = "1.18.66"
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
)

_THEME_FILES = (
    "wordpress/rawlead-kadence-child/functions.php",
    "wordpress/rawlead-kadence-child/page-cabinet.php",
    "wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js",
    "wordpress/rawlead-kadence-child/style.css",
)

_SQL_FILES = (
    "022_yookassa_processing_status.sql",
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
    if "YOOKASSA_SAVE_PAYMENT_METHOD" not in local:
        local["YOOKASSA_SAVE_PAYMENT_METHOD"] = "0"
    parts = [_ensure_env_line(k, local[k]) for k in _ENV_KEYS if local.get(k)]
    parts.append("chmod 600 /opt/rawlead/.env.site")
    parts.append("grep '^YOOKASSA_SHOP_ID=' /opt/rawlead/.env.site")
    parts.append(
        "grep '^YOOKASSA_WEBHOOK_SECRET=' /opt/rawlead/.env.site | "
        "sed 's/=.\\{0,4\\}/=****/'"
    )
    _, out, err = ssh.run(" && ".join(parts), check=False)
    return (out or err or "").strip()


def _apply_neon_migrations() -> str:
    results: list[str] = []
    for name in _SQL_FILES:
        local_sql = _ROOT / "sql" / name
        if not local_sql.is_file():
            results.append(f"SKIP sql/{name} missing")
            continue
        remote = f"/opt/rawlead/sql/{name}"
        ssh.upload(local_sql, remote)
        _, out, err = ssh.run(
            "DB_URL=$(grep '^DATABASE_URL=' /opt/rawlead/.env.site 2>/dev/null | head -1 | cut -d= -f2-) && "
            "[ -z \"$DB_URL\" ] && DB_URL=$(grep '^DATABASE_URL=' /opt/rawlead/.env 2>/dev/null | head -1 | cut -d= -f2-); "
            'if [ -z "$DB_URL" ]; then echo "SKIP: DATABASE_URL missing"; exit 0; fi; '
            'export DATABASE_URL="$DB_URL"; '
            "/opt/rawlead/.venv/bin/python - <<'PY'\n"
            "import os, pathlib, psycopg\n"
            "url = os.environ.get('DATABASE_URL') or ''\n"
            f"sql = pathlib.Path('{remote}').read_text(encoding='utf-8')\n"
            "with psycopg.connect(url) as conn:\n"
            "    with conn.cursor() as cur:\n"
            "        cur.execute(sql)\n"
            "    conn.commit()\n"
            f"print('NEON-{name} OK')\n"
            "PY",
            check=False,
        )
        results.append((out or err or "").strip())
    return "\n".join(results)


def main() -> int:
    print("=== O185 pre-launch deploy (t1/t2/t7) ===")
    print("--- env sync (webhook secret) ---")
    print(sync_yookassa_env())

    print("--- Neon migrations ---")
    print(_apply_neon_migrations())

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
        "grep -c _claim_payment_row /opt/rawlead/src/yookassa_billing.py && "
        f"grep RAWLEAD_CHILD_VERSION "
        "/var/www/rawlead.ru/wp-content/themes/rawlead-kadence-child/functions.php | head -1 && "
        "curl -s http://127.0.0.1:8000/health",
        check=False,
    )
    print((out or "").strip())
    ok = "active" in (out or "") and THEME_VER in (out or "")
    print("O185 DEPLOY OK" if ok else "O185 DEPLOY — verify manually")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
