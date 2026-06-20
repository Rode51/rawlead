#!/usr/bin/env python3
"""O271: Fresh VPS Postgres — schema, owner seed, optional SQLite lead backfill.

Run on VPS as root (install) or rawlead (schema only):
  python scripts/migrate_neon_to_vps_postgres.py --apply
  python scripts/migrate_neon_to_vps_postgres.py --apply --backfill-leads --backfill-limit 500
  python scripts/migrate_neon_to_vps_postgres.py --scrub-root-env
"""
from __future__ import annotations

import argparse
import os
import re
import secrets
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.site", override=True)

import psycopg  # noqa: E402

_OWNER_UUID = "00000000-0000-0000-0000-000000000001"
_ENV_SITE = Path(os.environ.get("RAWLEAD_ENV_SITE", "/opt/rawlead/.env.site"))
_SQL_DIR = _ROOT / "sql"
_CRED_FILE = Path(os.environ.get("RAWLEAD_PG_CRED", "/opt/rawlead/data/.pg_local_credentials"))
_NEON_BAK = _ENV_SITE.with_suffix(".site.neon-bak")


def _sql_files() -> list[Path]:
    files = list(_SQL_DIR.glob("*.sql"))
    files.sort(key=lambda p: int(p.name.split("_", 1)[0]))
    return files


def _read_env_site() -> str:
    if _ENV_SITE.is_file():
        return _ENV_SITE.read_text(encoding="utf-8")
    return ""


def _get_env_key(text: str, key: str) -> str:
    for line in text.splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return ""


def _set_env_key(text: str, key: str, value: str) -> str:
    line = f"{key}={value}"
    out: list[str] = []
    found = False
    for raw in text.splitlines():
        if raw.startswith(f"{key}="):
            if not found:
                out.append(line)
                found = True
            continue
        out.append(raw)
    if not found:
        out.append(line)
    return "\n".join(out).rstrip() + "\n"


def _local_db_url(user: str, password: str, db: str) -> str:
    from urllib.parse import quote

    pw = quote(password, safe="")
    return f"postgresql://{user}:{pw}@127.0.0.1:5432/{db}?sslmode=disable"


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd[:3]), ("..." if len(cmd) > 3 else ""))
    return subprocess.run(cmd, check=check, text=True, capture_output=True)


def install_postgresql() -> None:
    if Path("/usr/bin/psql").is_file() and _run(["systemctl", "is-active", "postgresql"], check=False).returncode == 0:
        print("postgresql: already installed/active")
        return
    _run(["apt-get", "update", "-qq"])
    env = os.environ.copy()
    env["DEBIAN_FRONTEND"] = "noninteractive"
    subprocess.run(
        ["apt-get", "install", "-y", "-qq", "postgresql", "postgresql-contrib", "postgresql-client"],
        check=True,
        env=env,
    )
    _run(["systemctl", "enable", "--now", "postgresql"])


def ensure_role_and_db(*, user: str, password: str, db: str) -> None:
    check = _run(
        ["sudo", "-u", "postgres", "psql", "-tAc", f"SELECT 1 FROM pg_roles WHERE rolname='{user}'"],
        check=False,
    )
    if (check.stdout or "").strip() != "1":
        _run(["sudo", "-u", "postgres", "psql", "-c", f"CREATE USER {user} WITH PASSWORD '{password}';"])
    else:
        _run(["sudo", "-u", "postgres", "psql", "-c", f"ALTER USER {user} WITH PASSWORD '{password}';"])

    check_db = _run(
        ["sudo", "-u", "postgres", "psql", "-tAc", f"SELECT 1 FROM pg_database WHERE datname='{db}'"],
        check=False,
    )
    if (check_db.stdout or "").strip() != "1":
        _run(["sudo", "-u", "postgres", "psql", "-c", f"CREATE DATABASE {db} OWNER {user};"])
    _run(["sudo", "-u", "postgres", "psql", "-c", f"GRANT ALL PRIVILEGES ON DATABASE {db} TO {user};"])


def apply_schema(db_url: str) -> None:
    files = _sql_files()
    if not files:
        raise SystemExit(f"no sql in {_SQL_DIR}")
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            for path in files:
                sql = path.read_text(encoding="utf-8")
                print(f"schema: {path.name}")
                cur.execute(sql)
        conn.commit()
    print(f"schema: applied {len(files)} files")


def bootstrap_owner(db_url: str, tg_chat_id: int | None) -> None:
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            if tg_chat_id is not None:
                cur.execute(
                    """
                    UPDATE users
                    SET tg_user_id = %s, tg_username = COALESCE(tg_username, 'owner')
                    WHERE id = %s::uuid
                    """,
                    (tg_chat_id, _OWNER_UUID),
                )
            cur.execute(
                """
                UPDATE subscriptions
                SET plan = 'owner', is_active = TRUE
                WHERE user_id = %s::uuid
                """,
                (_OWNER_UUID,),
            )
            cur.execute("SELECT COUNT(*) FROM users WHERE id = %s::uuid", (_OWNER_UUID,))
            n_users = int(cur.fetchone()[0])
            cur.execute(
                "SELECT plan, is_active FROM subscriptions WHERE user_id = %s::uuid",
                (_OWNER_UUID,),
            )
            sub = cur.fetchone()
        conn.commit()
    print(f"owner: uuid={_OWNER_UUID} tg_chat_id={tg_chat_id} users={n_users} sub={sub}")


def cutover_env(db_url: str) -> None:
    text = _read_env_site()
    old_url = _get_env_key(text, "DATABASE_URL")
    if old_url and "neon" in old_url.lower():
        if not _NEON_BAK.is_file():
            _NEON_BAK.write_text(text, encoding="utf-8")
            print(f"backup: {_NEON_BAK}")
        text = _set_env_key(text, "NEON_DATABASE_URL", old_url)
    text = _set_env_key(text, "DATABASE_URL", db_url)
    _ENV_SITE.write_text(text, encoding="utf-8")
    print(f"env: DATABASE_URL -> 127.0.0.1 ({_ENV_SITE})")


def smoke(db_url: str) -> None:
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM leads")
            leads = int(cur.fetchone()[0])
            cur.execute("SELECT plan FROM subscriptions WHERE user_id = %s::uuid", (_OWNER_UUID,))
            plan = cur.fetchone()
    print(f"smoke: leads={leads} owner_plan={plan[0] if plan else None}")


def backfill_leads(limit: int) -> int:
    cmd = [
        str(_ROOT / ".venv" / "bin" / "python"),
        str(_ROOT / "scripts" / "replay_neon_lite_site.py"),
        "--profile",
        "site",
        "--backfill-missing",
        "--limit",
        str(limit),
    ]
    print("+ backfill:", " ".join(cmd[-6:]))
    return subprocess.run(cmd, cwd=str(_ROOT), check=False).returncode


_ENV_ROOT = Path(os.environ.get("RAWLEAD_ENV_ROOT", "/opt/rawlead/.env"))


def scrub_root_env() -> None:
    """O272: comment DATABASE_URL in root .env — Neon stays in NEON_DATABASE_URL only."""
    path = _ENV_ROOT
    if not path.is_file():
        print(f"scrub: {path} missing — skip")
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    changed = False
    for raw in lines:
        if raw.startswith("DATABASE_URL="):
            out.append(f"# O272 scrubbed: {raw}")
            changed = True
        else:
            out.append(raw)
    if changed:
        path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
        print(f"scrub: commented DATABASE_URL in {path}")
    else:
        print(f"scrub: no active DATABASE_URL in {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="install + schema + owner + cutover")
    parser.add_argument("--schema-only", action="store_true", help="apply sql to DATABASE_URL")
    parser.add_argument(
        "--scrub-root-env",
        action="store_true",
        help="comment DATABASE_URL in /opt/rawlead/.env (Neon → NEON_DATABASE_URL only)",
    )
    parser.add_argument("--backfill-leads", action="store_true")
    parser.add_argument("--backfill-limit", type=int, default=500)
    parser.add_argument("--db-user", default="rawlead")
    parser.add_argument("--db-name", default="rawlead")
    args = parser.parse_args()

    if args.scrub_root_env:
        scrub_root_env()
        if not args.apply and not args.schema_only:
            return 0

    if not args.apply and not args.schema_only and not args.scrub_root_env:
        parser.print_help()
        return 0

    tg_raw = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    tg_chat_id = int(tg_raw) if tg_raw.isdigit() else None
    if tg_chat_id is None:
        print("WARN: TELEGRAM_CHAT_ID not set — owner row without tg_user_id until TG login", file=sys.stderr)

    password = ""
    if _CRED_FILE.is_file():
        for line in _CRED_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("password="):
                password = line.split("=", 1)[1].strip()
    if not password:
        password = secrets.token_urlsafe(24)
        _CRED_FILE.parent.mkdir(parents=True, exist_ok=True)
        _CRED_FILE.write_text(
            f"user={args.db_user}\ndb={args.db_name}\npassword={password}\n",
            encoding="utf-8",
        )
        _CRED_FILE.chmod(0o600)
        try:
            import pwd

            uid = pwd.getpwnam("rawlead").pw_uid
            gid = pwd.getpwnam("rawlead").pw_gid
            os.chown(_CRED_FILE, uid, gid)
        except (ImportError, KeyError, OSError):
            pass
        print(f"credentials: {_CRED_FILE}")

    if args.apply:
        install_postgresql()
        ensure_role_and_db(user=args.db_user, password=password, db=args.db_name)

    db_url = _local_db_url(args.db_user, password, args.db_name)
    apply_schema(db_url)
    bootstrap_owner(db_url, tg_chat_id)

    if args.apply:
        cutover_env(db_url)
        smoke(db_url)

    if args.backfill_leads:
        rc = backfill_leads(args.backfill_limit)
        if rc != 0:
            print(f"backfill exit {rc}", file=sys.stderr)
            return rc
        smoke(db_url)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
