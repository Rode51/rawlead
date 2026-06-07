"""O37c-a: mint JWT for preprod — Telethon acc1 → Neon paid user → .env.site.

  .venv\\Scripts\\python.exe scripts\\preprod_mint_token.py --account acc1 --write-env-site
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from uuid import uuid4

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

_ENV_SITE = _ROOT / ".env.site"
_TOKEN_KEY = "RAWLEAD_PREPROD_ACCESS_TOKEN"
_OWNER_USER_ID = "164786fe-b979-4bfa-a9dc-42416465f503"


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        for name in (".env", ".env.site"):
            p = _ROOT / name
            if p.is_file():
                load_dotenv(p, override=(name == ".env.site"))
    except ImportError:
        pass


def _write_env_site(env_path: Path, key: str, value: str) -> None:
    lines: list[str] = []
    if env_path.is_file():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    prefix = f"{key}="
    out: list[str] = []
    found = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(prefix):
            out.append(f"{prefix}{value}")
            found = True
        else:
            out.append(line)
    if not found:
        if out and out[-1].strip():
            out.append("")
        out.append(f"# {key} — O37c-a acc1 mint (local only, not git)")
        out.append(f"{prefix}{value}")

    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def _upsert_preprod_user(
    cur,
    *,
    tg_user_id: int,
    username: str | None,
    first_name: str | None,
    plan: str = "agent",
) -> str:
    cur.execute("SELECT id FROM users WHERE tg_user_id = %s", (tg_user_id,))
    row = cur.fetchone()
    if row:
        user_id = str(row[0])
        cur.execute(
            """
            UPDATE users
            SET tg_username = %s, tg_first_name = %s
            WHERE id = %s::uuid
            """,
            (username, first_name, user_id),
        )
    else:
        user_id = str(uuid4())
        cur.execute(
            """
            INSERT INTO users (id, tg_user_id, tg_username, tg_first_name)
            VALUES (%s::uuid, %s, %s, %s)
            """,
            (user_id, tg_user_id, username, first_name),
        )

    if plan == "free":
        cur.execute(
            """
            INSERT INTO subscriptions (user_id, plan, is_active)
            VALUES (%s::uuid, 'free', FALSE)
            ON CONFLICT (user_id) DO UPDATE
            SET plan = 'free', is_active = FALSE, active_until = NULL, paused_until = NULL
            """,
            (user_id,),
        )
    else:
        cur.execute(
            """
            INSERT INTO subscriptions (user_id, plan, is_active)
            VALUES (%s::uuid, 'agent', TRUE)
            ON CONFLICT (user_id) DO UPDATE
            SET plan = 'agent', is_active = TRUE, paused_until = NULL
            """,
            (user_id,),
        )
    return user_id


async def _telethon_me(account: str) -> tuple[int, str | None, str | None]:
    from tg_client import connect_client

    client = await connect_client(account)
    try:
        me = await client.get_me()
        if me is None:
            raise RuntimeError("Telethon get_me returned None")
        tg_user_id = int(me.id)
        username = (me.username or "").strip() or None
        first_name = (me.first_name or "").strip() or None
        return tg_user_id, username, first_name
    finally:
        await client.disconnect()


def main() -> int:
    parser = argparse.ArgumentParser(description="O37c-a: mint preprod JWT for Telethon acc")
    parser.add_argument("--account", default="acc1", choices=("acc1", "acc2", "acc3"))
    parser.add_argument(
        "--plan",
        default="agent",
        choices=("free", "agent"),
        help="free = logged-in без premium; agent = premium (default)",
    )
    parser.add_argument(
        "--write-env-site",
        action="store_true",
        help="Write token to .env.site under --env-key",
    )
    parser.add_argument(
        "--env-key",
        default="RAWLEAD_PREPROD_ACCESS_TOKEN",
        help="Key in .env.site when --write-env-site",
    )
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    _load_env()

    db_url = os.getenv("DATABASE_URL", "").strip()
    if not db_url:
        print("DATABASE_URL not set (.env)", file=sys.stderr)
        return 1

    try:
        tg_user_id, username, first_name = asyncio.run(_telethon_me(args.account))
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 1
    except Exception as exc:
        print(f"Telethon {args.account}: {exc}", file=sys.stderr)
        return 1

    import psycopg
    from jwt_auth import issue_access_token

    try:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                user_id = _upsert_preprod_user(
                    cur,
                    tg_user_id=tg_user_id,
                    username=username,
                    first_name=first_name,
                    plan=args.plan,
                )
            conn.commit()
    except Exception as exc:
        print(f"Neon upsert failed: {exc}", file=sys.stderr)
        return 1

    if user_id.lower() == _OWNER_USER_ID.lower():
        print(
            f"ERROR: user_id={user_id} is owner — acc1 TG совпадает с владельцем; "
            "нужен отдельный test acc (см. PREPROD_ACCOUNTS.md)",
            file=sys.stderr,
        )
        return 1

    try:
        token = issue_access_token(user_id, tg_user_id=tg_user_id)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.write_env_site:
        _write_env_site(_ENV_SITE, args.env_key, token)
        print(f"token written → {_ENV_SITE.name} ({args.env_key})")

    print(f"account={args.account}")
    print(f"plan={args.plan}")
    print(f"tg_user_id={tg_user_id}")
    print(f"user_id={user_id}")
    if username:
        print(f"tg_username=@{username.lstrip('@')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
