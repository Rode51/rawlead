"""Join через client монитора: один connect на аккаунт."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

from config import load_tg_join_config, radar_timestamp

GetClient = Callable[[], Awaitable[Any]]

_get_client: dict[str, GetClient] = {}


def _monitor_state_path():
    cfg = load_tg_join_config()
    return cfg.state_path.parent / "tg_join_monitor.json"


def _read_monitor_state() -> dict[str, dict]:
    path = _monitor_state_path()
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _write_monitor_state(account: str, *, active: bool) -> None:
    path = _monitor_state_path()
    state = _read_monitor_state()
    account = account.strip().lower()
    if active:
        state[account] = {"active": True, "ts": radar_timestamp()}
    else:
        state.pop(account, None)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def register_monitor_join(account: str, get_client: GetClient) -> None:
    """tg_monitor вызывает при connect, до цикла join."""
    account = account.strip().lower()
    _get_client[account] = get_client
    _write_monitor_state(account, active=True)


def unregister_monitor_join(account: str) -> None:
    account = account.strip().lower()
    _get_client.pop(account, None)
    _write_monitor_state(account, active=False)


def monitor_join_handles_tick(account: str) -> bool:
    """Supervisor не открывает вторую сессию, если join у монитора."""
    account = account.strip().lower()
    if account in _get_client:
        return True
    entry = _read_monitor_state().get(account, {})
    return bool(entry.get("active"))
