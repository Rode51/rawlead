"""O205-t13: probe acc1 membership in TG test group + chat_ids file sync."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import (  # noqa: E402
    load_radar_env,
    parse_telethon_chat_ids,
    telethon_chat_ids_path_for_account,
)
from public_feed import _chat_id_keys  # noqa: E402
from tg_client import connect_client  # noqa: E402

_DEFAULT_TEST_CHAT = -5177575757


def _ids_file_has_chat(path: Path, chat_id: int) -> bool:
    if not path.is_file():
        return False
    listen = set(parse_telethon_chat_ids(str(path)))
    listen_keys: set[int] = set()
    for cid in listen:
        listen_keys |= _chat_id_keys(cid)
    return bool(_chat_id_keys(chat_id) & listen_keys)


async def _probe(account: str, chat_id: int) -> int:
    load_radar_env()
    ids_path = telethon_chat_ids_path_for_account(account)
    file_ok = _ids_file_has_chat(ids_path, chat_id)
    print(f"account={account} chat={chat_id}")
    print(f"ids_file={ids_path} present={ids_path.is_file()} listed={file_ok}")

    client = await connect_client(account)
    dialog_hit = False
    entity_title = ""
    try:
        entity = await client.get_entity(chat_id)
        entity_title = str(getattr(entity, "title", "") or getattr(entity, "username", "") or "")
        print(f"get_entity ok title={entity_title!r} id={getattr(entity, 'id', '?')}")
        target_keys = _chat_id_keys(chat_id)
        async for dialog in client.iter_dialogs(limit=500):
            if _chat_id_keys(dialog.id) & target_keys:
                dialog_hit = True
                print(f"dialog_match id={dialog.id} title={dialog.title!r}")
                break
        if not dialog_hit:
            print("dialog_match=no (not in recent dialogs)")
            print("hint=re-join via tg_monitor startup or join_one on invite")
    except Exception as exc:
        print(f"get_entity_fail={type(exc).__name__}: {exc}")
        return 1
    finally:
        await client.disconnect()

    ok = file_ok and dialog_hit
    print(f"membership_ok={ok}")
    return 0 if ok else 2


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe TG test group membership (O205-t13)")
    parser.add_argument("--account", default="acc1", choices=("acc1", "acc2", "acc3"))
    parser.add_argument("--chat-id", type=int, default=_DEFAULT_TEST_CHAT)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(asyncio.run(_probe(args.account, args.chat_id)))


if __name__ == "__main__":
    main()
