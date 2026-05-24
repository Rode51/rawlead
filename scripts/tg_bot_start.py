"""Отправить /start боту с мониторинговых acc (Telethon, без телефона)."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from tg_bot_start import ensure_bot_started, resolve_bot_start_accounts  # noqa: E402
from tg_client import connect_client  # noqa: E402


async def _run_account(account: str, *, force: bool) -> bool:
    print(f"[{account}] connect…", flush=True)
    try:
        client = await connect_client(account)
    except SystemExit:
        raise
    except Exception as exc:
        msg = str(exc).lower()
        if "database is locked" in msg or "locked" in msg:
            print(
                f"[{account}] сессия занята — останови tg_main/пульт и повтори",
                file=sys.stderr,
                flush=True,
            )
        else:
            print(f"[{account}] connect: {exc}", file=sys.stderr, flush=True)
        return False
    try:
        ok = await ensure_bot_started(
            client,
            account,
            force=force,
            log_fn=lambda msg: print(f"[{account}] {msg}", flush=True),
        )
        return ok
    finally:
        await client.disconnect()


async def _main() -> int:
    parser = argparse.ArgumentParser(
        description="Отправить /start боту с acc-сессии (Telethon, без телефона)"
    )
    parser.add_argument(
        "--account",
        required=True,
        choices=("acc1", "acc2", "acc3", "all"),
        help="acc1|acc2|acc3|all (all = все три acc)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Отправить /start даже если есть data/.tg_bot_started_<acc>",
    )
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    accounts = resolve_bot_start_accounts(args.account)
    if not accounts:
        print("[!] Нет аккаунтов для /start", file=sys.stderr, flush=True)
        return 1

    ok_all = True
    for acc in accounts:
        try:
            ok = await _run_account(acc, force=args.force)
        except SystemExit:
            print(f"[{acc}] ошибка конфигурации или сессии", file=sys.stderr, flush=True)
            ok = False
        if not ok:
            ok_all = False

    if ok_all:
        print("Готово: /start отправлен.", flush=True)
        return 0
    print("[!] Есть ошибки — см. вывод выше.", file=sys.stderr, flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
