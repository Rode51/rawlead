"""Очередь join по docs/ops/TG_JOIN_QUEUE.csv с лимитами в час."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
os.environ.setdefault("RADAR_PROFILE", "site")

from config import (  # noqa: E402
    load_tg_join_config,
    telethon_monitor_accounts,
    tg_join_in_tg_main,
)
from tg_join_runner import run_join_tick  # noqa: E402


async def _main() -> None:
    parser = argparse.ArgumentParser(description="Join TG chats from queue CSV")
    parser.add_argument(
        "--account",
        required=True,
        choices=("acc1", "acc2", "acc3"),
        help="Мониторинговый аккаунт",
    )
    parser.add_argument(
        "--max-per-hour",
        type=int,
        default=None,
        help="Лимит join в текущий час (по умолчанию TG_JOIN_MAX_PER_HOUR)",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Цикл: тик раз в TG_JOIN_DAEMON_INTERVAL_SEC (по умолчанию 3600)",
    )
    args = parser.parse_args()

    cfg = load_tg_join_config()
    if args.max_per_hour is not None and args.max_per_hour < 1:
        print("--max-per-hour: минимум 1")
        raise SystemExit(1)

    account = args.account.strip().lower()
    if tg_join_in_tg_main() and account in telethon_monitor_accounts():
        print(
            f"{account} join в отдельном процессе запрещён (database locked). "
            "Используйте tg_main с TG_JOIN_IN_TG_MAIN=1.",
            flush=True,
        )
        raise SystemExit(1)

    if args.daemon:
        while True:
            await run_join_tick(
                account,
                max_per_hour=args.max_per_hour,
                cfg=cfg,
            )
            await asyncio.sleep(cfg.daemon_interval_sec)
    else:
        await run_join_tick(
            account,
            max_per_hour=args.max_per_hour,
            cfg=cfg,
        )


if __name__ == "__main__":
    asyncio.run(_main())
