"""Allowlist user_id мониторинговых acc для relay ботом → владелец."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from config import _PROJECT_ROOT

__all__ = [
    "allowlist_path",
    "load_allowlist",
    "register_account_user_id",
    "refresh_allowlist_from_accounts",
    "is_allowlisted_user",
    "account_for_user_id",
    "mark_message_relayed",
    "was_message_relayed",
]

_ALLOWLIST_PATH = _PROJECT_ROOT / "data" / "tg_relay_allowlist.json"
_RELAYED_KEYS: set[tuple[int, int]] = set()
_RELAYED_KEYS_MAX = 800


def allowlist_path() -> Path:
    return _ALLOWLIST_PATH


def load_allowlist() -> dict[str, int]:
    path = allowlist_path()
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, int] = {}
    for key, val in raw.items():
        acc = str(key).strip().lower()
        if not acc:
            continue
        try:
            out[acc] = int(val)
        except (TypeError, ValueError):
            continue
    return out


def _save_allowlist(data: dict[str, int]) -> None:
    path = allowlist_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = {k: data[k] for k in sorted(data)}
    path.write_text(
        json.dumps(ordered, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def register_account_user_id(account: str, user_id: int) -> bool:
    """Записать acc → user_id. True если файл изменился."""
    acc = account.strip().lower()
    uid = int(user_id)
    data = load_allowlist()
    if data.get(acc) == uid:
        return False
    data[acc] = uid
    _save_allowlist(data)
    return True


def is_allowlisted_user(user_id: int) -> bool:
    uid = int(user_id)
    return uid in set(load_allowlist().values())


def account_for_user_id(user_id: int) -> str | None:
    uid = int(user_id)
    for acc, listed in load_allowlist().items():
        if listed == uid:
            return acc
    return None


def mark_message_relayed(from_chat_id: int, message_id: int) -> None:
    key = (int(from_chat_id), int(message_id))
    _RELAYED_KEYS.add(key)
    if len(_RELAYED_KEYS) > _RELAYED_KEYS_MAX:
        drop = len(_RELAYED_KEYS) - _RELAYED_KEYS_MAX // 2
        for _ in range(drop):
            _RELAYED_KEYS.pop()


def was_message_relayed(from_chat_id: int, message_id: int) -> bool:
    return (int(from_chat_id), int(message_id)) in _RELAYED_KEYS


async def refresh_allowlist_from_accounts(
    accounts: tuple[str, ...],
    *,
    log_fn: Callable[[str], None] | None = None,
) -> None:
    """get_me каждой сессии из TELETHON_MONITOR_ACCOUNTS → allowlist."""
    from tg_client import connect_client

    def _log(msg: str) -> None:
        if log_fn is not None:
            log_fn(msg)

    for acc in accounts:
        key = acc.strip().lower()
        if not key:
            continue
        try:
            client = await connect_client(key)
        except Exception as exc:
            _log(f"тг:allowlist:{key}:connect:{type(exc).__name__}")
            continue
        try:
            me = await client.get_me()
            uid = int(me.id)
        except Exception as exc:
            _log(f"тг:allowlist:{key}:get_me:{type(exc).__name__}")
            continue
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass
        if register_account_user_id(key, uid):
            _log(f"тг:allowlist:{key}:user_id={uid}")
        else:
            _log(f"тг:allowlist:{key}:ok user_id={uid}")
