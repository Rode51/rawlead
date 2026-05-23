"""Один supervisor join для acc2/acc3/acc4 (не monitor account)."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import load_tg_join_config, tg_join_daemon_accounts  # noqa: E402
from tg_join_registry import monitor_join_handles_tick  # noqa: E402
from tg_join_runner import log_join, run_join_tick  # noqa: E402


def _parse_accounts(raw: str | None) -> list[str]:
    if raw is None or not str(raw).strip():
        return tg_join_daemon_accounts()
    return [a.strip().lower() for a in str(raw).split(",") if a.strip()]


async def _run_daemon(accounts: list[str]) -> None:
    cfg = load_tg_join_config()
    log_join(cfg, f"join:daemon:старт accounts={','.join(accounts)}")
    while True:
        for account in accounts:
            if monitor_join_handles_tick(account):
                log_join(cfg, f"join:skip account={account} reason=monitor_active")
                continue
            await run_join_tick(account, cfg=cfg)
        await asyncio.sleep(cfg.daemon_interval_sec)


async def _main() -> None:
    parser = argparse.ArgumentParser(
        description="Join supervisor: один процесс для нескольких acc",
    )
    parser.add_argument(
        "--accounts",
        default=None,
        help="acc2,acc3 или env TG_JOIN_DAEMON_ACCOUNTS",
    )
    args = parser.parse_args()

    accounts = _parse_accounts(args.accounts)
    if not accounts:
        print(
            "Нет аккаунтов: задайте --accounts acc2,acc3 "
            "или TG_JOIN_DAEMON_ACCOUNTS в .env",
            flush=True,
        )
        raise SystemExit(1)

    await _run_daemon(accounts)


if __name__ == "__main__":
    asyncio.run(_main())
