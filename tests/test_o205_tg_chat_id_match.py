"""O205-t6: TG monitor chat_id peer normalization."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from tg_monitor import _message_chat_listened  # noqa: E402


def test_message_chat_listened_supergroup_peer() -> None:
    listen = {-5177575757}
    assert _message_chat_listened(-1005177575757, listen)
    assert _message_chat_listened(5177575757, listen)


def test_message_chat_listened_unrelated_chat() -> None:
    listen = {-5177575757}
    assert not _message_chat_listened(-1001234567890, listen)
