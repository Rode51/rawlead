"""Список диалогов и id чатов (для docs/ops/SOURCES_POOLS.md)."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from tg_client import connect_client  # noqa: E402


def _safe_print(line: str) -> None:
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(
            sys.stdout.encoding or "utf-8", errors="replace"
        ))


async def _main() -> None:
    parser = argparse.ArgumentParser(description="List TG dialogs and chat ids")
    parser.add_argument(
        "--account",
        default="acc1",
        choices=("acc1", "acc2", "acc3"),
        help="Мониторинговый аккаунт из .env",
    )
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print(f"account: {args.account}")
    client = await connect_client(args.account)
    try:
        async for dialog in client.iter_dialogs():
            ent = dialog.entity
            title = dialog.title or dialog.name or "?"
            _safe_print(f"{ent.id}\t{title}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(_main())
