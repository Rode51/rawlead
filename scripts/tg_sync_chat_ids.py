"""Пересобрать data/telethon_chat_ids_accN.txt из TG_JOIN_QUEUE.csv (done + account)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import (  # noqa: E402
    _join_queue_csv_paths,
    _seed_chat_ids_from_queue_paths,
    load_tg_join_config,
    telethon_chat_ids_path_for_account,
    telethon_monitor_accounts,
)


def _write_ids(path: Path, account: str, ids: list[int], *, dry_run: bool) -> None:
    print(f"account={account} ids={ids} path={path}")
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# Telethon chat ids для tg_main ({account}, один id на строку)\n"]
    for cid in ids:
        lines.append(f"{cid}\n")
    path.write_text("".join(lines), encoding="utf-8")
    print(f"Записано {len(ids)} id в {path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Пересобрать listen-файлы из очереди join",
    )
    parser.add_argument(
        "--account",
        default="all",
        choices=("acc1", "acc2", "acc3", "all"),
        help="Какой аккаунт (или all из TELETHON_MONITOR_ACCOUNTS)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только показать id, файл не перезаписывать",
    )
    args = parser.parse_args()

    cfg = load_tg_join_config()
    queue_paths = _join_queue_csv_paths() or [cfg.queue_csv]
    if args.account == "all":
        targets = list(telethon_monitor_accounts())
    else:
        targets = [args.account]

    wrote_any = False
    for account in targets:
        ids = _seed_chat_ids_from_queue_paths(queue_paths, account)
        if not ids:
            print(f"Нет done-строк с chat_id для account={account} в {cfg.queue_csv}")
            continue
        ids_path = telethon_chat_ids_path_for_account(account)
        _write_ids(ids_path, account, ids, dry_run=args.dry_run)
        wrote_any = True

    if not wrote_any:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
