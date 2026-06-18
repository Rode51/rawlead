"""O206-t3: resolve message chat_id from event when message.chat_id is None."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from tg_monitor import (  # noqa: E402
    _message_chat_listened,
    _resolve_message_chat_id,
)


def test_message_chat_listened_none_returns_false() -> None:
    assert not _message_chat_listened(None, {-5177575757})


def test_resolve_message_chat_id_from_event() -> None:
    message = SimpleNamespace(chat_id=None)
    event = SimpleNamespace(chat_id=-1005177575757)
    assert _resolve_message_chat_id(message, event) == -1005177575757


def test_resolve_message_chat_id_prefers_message() -> None:
    message = SimpleNamespace(chat_id=-5177575757)
    event = SimpleNamespace(chat_id=-1005177575757)
    assert _resolve_message_chat_id(message, event) == -5177575757
