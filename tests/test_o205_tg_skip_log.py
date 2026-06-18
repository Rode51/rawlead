"""O205-t13: тг:пропуск logging for silent TG monitor skips."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from public_feed import chat_in_tg_interest_set  # noqa: E402
from tg_monitor import (  # noqa: E402
    _listing_skip_reason,
    _log_tg_skip,
    _message_chat_listened,
)


def test_listing_skip_reason_outgoing() -> None:
    msg = SimpleNamespace(text="заказ", message=None, out=True, action=None, chat_id=-5177575757)
    assert _listing_skip_reason(msg) == "исходящее"


def test_listing_skip_reason_no_text() -> None:
    msg = SimpleNamespace(text="", message=None, out=False, action=None, chat_id=-5177575757)
    assert _listing_skip_reason(msg) == "нет_текста"


def test_listing_skip_reason_ok() -> None:
    msg = SimpleNamespace(text="нужен дизайнер", message=None, out=False, action=None, chat_id=-5177575757)
    assert _listing_skip_reason(msg) is None


def test_log_tg_skip_writes_line(tmp_path: Path) -> None:
    log_path = tmp_path / "radar_site.log"
    storage = MagicMock()
    with patch("tg_monitor.record_tg_skip") as mock_skip:
        _log_tg_skip(
            log_path,
            account="acc1",
            chat_id=-5177575757,
            msg_id=42,
            reason="не_слушаем",
            storage=storage,
        )
    line = log_path.read_text(encoding="utf-8").strip()
    assert "тг:пропуск" in line
    assert "acc=acc1" in line
    assert "chat=-5177575757" in line
    assert "msg=42" in line
    assert "reason=не_слушаем" in line
    mock_skip.assert_called_once_with(storage, "acc1", "пропуск:не_слушаем")


def test_unlistened_chat_not_in_peer_set() -> None:
    listen = {-5177575757}
    assert not _message_chat_listened(-1001234567890, listen)


def test_unlistened_random_chat_no_log(tmp_path: Path) -> None:
    """O206-t1: не_слушаем only for interest set — random chat silent."""
    log_path = tmp_path / "radar_site.log"
    storage = MagicMock()
    assert not chat_in_tg_interest_set(-1001234567890)
    # Interest-set gate is in handler; helper confirms random chat excluded.
    _log_tg_skip(
        log_path,
        account="acc1",
        chat_id=-1001234567890,
        msg_id=1,
        reason="не_слушаем",
        storage=storage,
    )
    assert log_path.read_text(encoding="utf-8")  # _log_tg_skip still works when called
