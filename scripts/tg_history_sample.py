"""O207-t2: read-only Telethon history sample from listen chats (no Neon / no notify)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import parse_telethon_chat_ids, telethon_chat_ids_path_for_account  # noqa: E402
from public_feed import filter_listen_chat_ids  # noqa: E402
from tg_client import connect_client  # noqa: E402
from tg_join_lib import load_chat_registry_from_queue  # noqa: E402
from tg_monitor import _listing_from_message, _listing_skip_reason  # noqa: E402
from telethon import utils  # noqa: E402


async def _resolve_entity(client, raw_id: int):
    candidates = [raw_id]
    if raw_id > 0:
        candidates.append(int(f"-100{raw_id}"))
    for cid in candidates:
        try:
            return await client.get_entity(cid)
        except Exception:
            continue
    return None


async def collect_history_sample(
    *,
    account: str,
    per_chat: int,
    max_chats: int,
    rate_limit_sec: float = 1.0,
) -> dict:
    ids_path = telethon_chat_ids_path_for_account(account)
    raw_ids = parse_telethon_chat_ids(str(ids_path))
    listen_ids = filter_listen_chat_ids(raw_ids)[:max_chats]
    chat_registry = load_chat_registry_from_queue()

    client = await connect_client(account)
    rows: list[dict] = []
    skipped_chats = 0
    try:
        for idx, raw_id in enumerate(listen_ids):
            if idx > 0:
                await asyncio.sleep(rate_limit_sec)
            entity = await _resolve_entity(client, raw_id)
            if entity is None:
                skipped_chats += 1
                continue
            peer_id = utils.get_peer_id(entity)
            chat_title = str(getattr(entity, "title", "") or getattr(entity, "username", "") or "")
            chat_username = str(getattr(entity, "username", "") or "").strip()
            try:
                messages = await client.get_messages(entity, limit=per_chat)
            except Exception as exc:
                skipped_chats += 1
                rows.append(
                    {
                        "account": account,
                        "chat_id": peer_id,
                        "msg_id": None,
                        "chat_title": chat_title,
                        "date_iso": "",
                        "title": "",
                        "body_preview": "",
                        "parse_ok": False,
                        "error": str(exc)[:120],
                    }
                )
                continue

            for message in messages:
                if message is None:
                    continue
                skip = _listing_skip_reason(message)
                if skip is not None:
                    continue
                project = _listing_from_message(
                    message,
                    chat_registry=chat_registry,
                    chat_title=chat_title,
                    chat_username=chat_username,
                    resolved_chat_id=peer_id,
                )
                body = (project.listing_snippet if project else "") or ""
                title = (project.title if project else "") or ""
                date_iso = ""
                if message.date:
                    date_iso = message.date.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                rows.append(
                    {
                        "account": account,
                        "chat_id": peer_id,
                        "msg_id": int(message.id),
                        "chat_title": chat_title,
                        "date_iso": date_iso,
                        "title": title,
                        "body_preview": body[:500],
                        "parse_ok": project is not None,
                    }
                )
    finally:
        await client.disconnect()

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "account": account,
        "per_chat": per_chat,
        "max_chats": max_chats,
        "listen_ids_in_file": len(raw_ids),
        "listen_ids_after_filter": len(filter_listen_chat_ids(raw_ids)),
        "chats_requested": len(listen_ids),
        "chats_skipped": skipped_chats,
        "rows": rows,
        "row_count": len(rows),
    }


async def _main_async(args: argparse.Namespace) -> None:
    report = await collect_history_sample(
        account=args.account,
        per_chat=args.per_chat,
        max_chats=args.max_chats,
        rate_limit_sec=args.rate_limit,
    )
    out = Path(args.out)
    if not out.is_absolute():
        out = _ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"wrote {out} rows={report['row_count']}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="TG history sample (O207-t2, read-only)")
    parser.add_argument("--account", default="acc1", choices=("acc1", "acc2", "acc3"))
    parser.add_argument("--per-chat", type=int, default=10)
    parser.add_argument("--max-chats", type=int, default=70)
    parser.add_argument("--rate-limit", type=float, default=1.0, help="Seconds between chats")
    parser.add_argument("--out", default="data/tg_history_sample.json")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    asyncio.run(_main_async(args))


if __name__ == "__main__":
    main()
