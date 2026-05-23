"""Вступление в чаты по invite-ссылкам (фаза 1). Не подключён к main.py."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from tg_client import connect_client  # noqa: E402
from tg_join_lib import join_one, read_invite_links  # noqa: E402


async def _main() -> None:
    parser = argparse.ArgumentParser(description="Join TG chats by invite link")
    parser.add_argument(
        "--account",
        default="acc1",
        choices=("acc1", "acc2", "acc3"),
        help="Мониторинговый аккаунт из .env",
    )
    parser.add_argument("links", nargs="*", help="Ссылки t.me (иначе TG_JOIN_LINKS.txt)")
    args = parser.parse_args()

    invites = read_invite_links(args.links)
    if not invites:
        print("Нет ссылок. --account acc2 + ссылки или docs/ops/TG_JOIN_LINKS.txt")
        raise SystemExit(1)

    print(f"account: {args.account}")
    client = await connect_client(args.account)
    try:
        for link in invites:
            print(f"join: {link}")
            result = await join_one(client, link)
            if result.ok:
                suffix = " (already in chat)" if result.already else ""
                cid = f", chat_id={result.chat_id}" if result.chat_id else ""
                print(f"  ok{suffix}{cid}")
            else:
                print(f"  fail: {link} — {result.error}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(_main())
