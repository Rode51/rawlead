#!/usr/bin/env python3
"""Mint JWT for local free-tier UI (Telethon acc2/acc3, plan=free)."""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path
from uuid import uuid4

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

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


async def _telethon_me(account: str) -> tuple[int, str | None, str | None]:
    from tg_client import connect_client

    client = await connect_client(account)
    try:
        me = await client.get_me()
        if me is None:
            raise RuntimeError("Telethon get_me returned None")
        return int(me.id), (me.username or "").strip() or None, (me.first_name or "").strip() or None
    finally:
        await client.disconnect()


def _upsert_free_user(cur, *, tg_user_id: int, username: str | None, first_name: str | None) -> str:
    cur.execute("SELECT id FROM users WHERE tg_user_id = %s", (tg_user_id,))
    row = cur.fetchone()
    if row:
        user_id = str(row[0])
        cur.execute(
            "UPDATE users SET tg_username = %s, tg_first_name = %s WHERE id = %s::uuid",
            (username, first_name, user_id),
        )
    else:
        user_id = str(uuid4())
        cur.execute(
            "INSERT INTO users (id, tg_user_id, tg_username, tg_first_name) VALUES (%s::uuid, %s, %s, %s)",
            (user_id, tg_user_id, username, first_name),
        )
    cur.execute(
        """
        INSERT INTO subscriptions (user_id, plan, is_active, active_until, paused_until)
        VALUES (%s::uuid, 'free', FALSE, NULL, NULL)
        ON CONFLICT (user_id) DO UPDATE
        SET plan = 'free', is_active = FALSE, active_until = NULL, paused_until = NULL
        """,
        (user_id,),
    )
    return user_id


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--account", default="acc2", choices=("acc1", "acc2", "acc3"))
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    _load_env()
    db_url = os.getenv("DATABASE_URL", "").strip()
    if not db_url:
        print("DATABASE_URL missing", file=sys.stderr)
        return 1

    try:
        tg_user_id, username, first_name = asyncio.run(_telethon_me(args.account))
    except Exception as exc:
        print(f"Telethon {args.account}: {exc}", file=sys.stderr)
        return 1

    import psycopg
    from jwt_auth import issue_access_token

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            user_id = _upsert_free_user(
                cur, tg_user_id=tg_user_id, username=username, first_name=first_name
            )
        conn.commit()

    if user_id.lower() == _OWNER_USER_ID.lower():
        print("ERROR: account maps to owner uuid", file=sys.stderr)
        return 1

    token = issue_access_token(user_id, tg_user_id=tg_user_id)
    print(f"account={args.account}")
    print(f"tg_user_id={tg_user_id}")
    if username:
        print(f"tg_username=@{username.lstrip('@')}")
    print(f"user_id={user_id}")
    print(f"token={token}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
