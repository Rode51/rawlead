"""O257: soft reset does NOT set restart_source_fl when subprocess enabled.

The restart loop: fl_hard_reset sets restart_source_fl=1 → main.py closes contexts
every cycle → no-op for subprocess → subprocess still empty → streak → hard reset again.

Fix: set_restart_source=False when subprocess enabled so the deferred context-close
flag is not set — teardown already happened inline in fl_hard_reset.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from fl_parser import _maybe_fl_soft_antibot_reset, _maybe_fl_parsed_zero_recovery  # noqa: E402


def _cfg(tmp_path: Path) -> MagicMock:
    cfg = MagicMock()
    cfg.radar_log_path = tmp_path / "radar.log"
    cfg.radar_log_path.parent.mkdir(parents=True, exist_ok=True)
    return cfg


# ---------------------------------------------------------------------------
# Subprocess enabled → set_restart_source=False
# ---------------------------------------------------------------------------

def test_soft_antibot_no_restart_source_when_subprocess(tmp_path: Path) -> None:
    """When FL_LISTING_SUBPROCESS=1, soft antibot reset must NOT set restart_source_fl."""
    cfg = _cfg(tmp_path)
    storage = MagicMock()

    with patch("fl_parser._fl_count_source_bans", return_value=0), \
         patch("fl_parser.fl_listing_subprocess_enabled", return_value=True), \
         patch("exchange_browser_fetch.fl_hard_reset") as mock_reset:
        result = _maybe_fl_soft_antibot_reset(cfg, storage, streak=5)

    assert result is True
    mock_reset.assert_called_once()
    call_kwargs = mock_reset.call_args.kwargs
    assert call_kwargs.get("set_restart_source") is False, (
        "set_restart_source should be False when subprocess enabled to avoid restart loop"
    )


def test_soft_antibot_sets_restart_source_when_no_subprocess(tmp_path: Path) -> None:
    """When subprocess disabled (persistent context mode), restart_source should be set."""
    cfg = _cfg(tmp_path)
    storage = MagicMock()

    with patch("fl_parser._fl_count_source_bans", return_value=0), \
         patch("fl_parser.fl_listing_subprocess_enabled", return_value=False), \
         patch("exchange_browser_fetch.fl_hard_reset") as mock_reset:
        result = _maybe_fl_soft_antibot_reset(cfg, storage, streak=5)

    assert result is True
    call_kwargs = mock_reset.call_args.kwargs
    assert call_kwargs.get("set_restart_source") is True, (
        "set_restart_source should be True in persistent context mode"
    )


def test_parsed_zero_recovery_no_restart_source_when_subprocess(tmp_path: Path) -> None:
    """parsed_zero recovery (O233) also must not set restart_source when subprocess."""
    cfg = _cfg(tmp_path)
    storage = MagicMock()
    storage.get_setting.return_value = "0"

    with patch("fl_parser._fl_fetch_pool_ok", return_value=True), \
         patch("fl_parser._fl_streak_get", return_value=3), \
         patch("fl_parser._fl_auto_ban_clear_enabled", return_value=True), \
         patch("fl_parser._fl_last_auto_clear_at", return_value=0.0), \
         patch("fl_parser.fl_listing_subprocess_enabled", return_value=True), \
         patch("fl_parser._fl_count_source_bans", return_value=0), \
         patch("fl_parser.listing_browser_enabled", return_value=True), \
         patch("exchange_proxy.clear_fl_source_bans", return_value=1, create=True), \
         patch("exchange_browser_fetch.fl_hard_reset") as mock_reset:
        _maybe_fl_parsed_zero_recovery(cfg, storage, parsed_cards=0)

    if mock_reset.called:
        call_kwargs = mock_reset.call_args.kwargs
        assert call_kwargs.get("set_restart_source") is False, (
            "parsed_zero recovery must not set restart_source when subprocess enabled"
        )


# ---------------------------------------------------------------------------
# fl_hard_reset set_restart_source parameter
# ---------------------------------------------------------------------------

def test_fl_hard_reset_set_restart_source_false_does_not_set_flag() -> None:
    """fl_hard_reset(set_restart_source=False) must not write restart_source_fl=1."""
    storage = MagicMock()

    with patch("exchange_browser_fetch.close_all_browser_contexts"), \
         patch("exchange_browser_fetch._abort_playwright_worker"), \
         patch("exchange_browser_fetch._wipe_fl_profile_dirs", return_value=0), \
         patch("exchange_browser_fetch.clear_fl_source_bans", return_value=0, create=True):
        from exchange_browser_fetch import fl_hard_reset
        fl_hard_reset(reason="test", storage=storage, set_restart_source=False)

    # set_setting should not have been called with restart_source_fl
    for c in storage.set_setting.call_args_list:
        key = c.args[0] if c.args else c.kwargs.get("key", "")
        assert "restart_source_fl" not in str(key), (
            "restart_source_fl must NOT be set when set_restart_source=False"
        )


def test_fl_hard_reset_set_restart_source_true_sets_flag() -> None:
    """fl_hard_reset(set_restart_source=True) must set restart_source_fl=1."""
    storage = MagicMock()

    with patch("exchange_browser_fetch.close_all_browser_contexts"), \
         patch("exchange_browser_fetch._abort_playwright_worker"), \
         patch("exchange_browser_fetch._wipe_fl_profile_dirs", return_value=0), \
         patch("exchange_browser_fetch.clear_fl_source_bans", return_value=0, create=True):
        from exchange_browser_fetch import fl_hard_reset
        fl_hard_reset(reason="test", storage=storage, set_restart_source=True)

    set_calls = [str(c) for c in storage.set_setting.call_args_list]
    assert any("restart_source_fl" in s for s in set_calls), (
        "restart_source_fl=1 should be set when set_restart_source=True"
    )


# ---------------------------------------------------------------------------
# Anti-regression: O256 soft_antibot_reset streak threshold still works
# ---------------------------------------------------------------------------

def test_soft_antibot_not_triggered_below_threshold(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    storage = MagicMock()

    with patch("fl_parser._fl_count_source_bans", return_value=0), \
         patch("fl_parser.fl_listing_subprocess_enabled", return_value=True), \
         patch("exchange_browser_fetch.fl_hard_reset") as mock_reset:
        result = _maybe_fl_soft_antibot_reset(cfg, storage, streak=4)

    assert result is False
    mock_reset.assert_not_called()


def test_soft_antibot_not_triggered_with_bans(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    storage = MagicMock()

    with patch("fl_parser._fl_count_source_bans", return_value=2), \
         patch("exchange_browser_fetch.fl_hard_reset") as mock_reset:
        result = _maybe_fl_soft_antibot_reset(cfg, storage, streak=10)

    assert result is False
    mock_reset.assert_not_called()
