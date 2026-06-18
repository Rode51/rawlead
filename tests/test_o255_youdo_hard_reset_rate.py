"""O255: YouDo auto hard reset — fail@1, rate limit, hourly cap."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from youdo_parser import (  # noqa: E402
    YOUDO_COOLDOWN_KEY,
    YOUDO_HARD_RESET_HOUR_COUNT_KEY,
    YOUDO_HARD_RESET_HOUR_START_KEY,
    YOUDO_LAST_HARD_RESET_AT_KEY,
    YOUDO_TRAFFIC_GUARD_UNTIL_KEY,
    _on_youdo_fetch_fail,
    _youdo_hard_reset_fail_threshold,
)


def test_hard_reset_fail_threshold_default_is_one() -> None:
    with patch.dict("os.environ", {}, clear=True):
        assert _youdo_hard_reset_fail_threshold() == 1


def test_on_youdo_fetch_fail_hard_reset_at_first_fail() -> None:
    storage = MagicMock()
    cfg = MagicMock()
    cfg.radar_log_path = Path("/tmp/radar.log")

    with patch("youdo_parser._bump_youdo_fail_streak", return_value=1):
        with patch("youdo_parser.youdo_hard_reset_on_fail_enabled", return_value=True):
            with patch("youdo_parser.youdo_hard_reset") as mock_reset:
                with patch("youdo_parser._record_auto_hard_reset") as mock_record:
                    with patch("youdo_parser.set_youdo_cooldown") as mock_cooldown:
                        with patch("youdo_parser.log_youdo_trace") as mock_trace:
                            _on_youdo_fetch_fail(cfg, storage)

    mock_reset.assert_called_once_with(
        reason="auto_fail_streak=1",
        storage=storage,
    )
    mock_record.assert_called_once_with(storage)
    mock_cooldown.assert_not_called()
    mock_trace.assert_called_once()
    assert mock_trace.call_args.args[1] == "hard_reset"


def test_on_youdo_fetch_fail_rate_limited_short_cooldown() -> None:
    storage = MagicMock()
    cfg = MagicMock()
    cfg.radar_log_path = Path("/tmp/radar.log")
    now = time.time()
    storage.get_setting.side_effect = lambda key, default="0": {
        YOUDO_LAST_HARD_RESET_AT_KEY: str(now - 30),
        YOUDO_HARD_RESET_HOUR_START_KEY: str(now - 60),
        YOUDO_HARD_RESET_HOUR_COUNT_KEY: "1",
    }.get(key, default)

    with patch("youdo_parser._bump_youdo_fail_streak", return_value=1):
        with patch("youdo_parser.youdo_hard_reset_on_fail_enabled", return_value=True):
            with patch("youdo_parser._youdo_hard_reset_min_sec", return_value=120.0):
                with patch("youdo_parser._youdo_short_cooldown_min", return_value=5):
                    with patch("youdo_parser.youdo_hard_reset") as mock_reset:
                        with patch("youdo_parser.set_youdo_short_cooldown") as mock_short:
                            with patch("youdo_parser.set_youdo_cooldown") as mock_cooldown:
                                with patch("youdo_parser.log_youdo_trace") as mock_trace:
                                    _on_youdo_fetch_fail(cfg, storage)

    mock_reset.assert_not_called()
    mock_short.assert_called_once_with(storage)
    mock_cooldown.assert_not_called()
    mock_trace.assert_called_once()
    assert mock_trace.call_args.args[1] == "hard_reset_rate_limited"


def test_on_youdo_fetch_fail_hourly_cap_triggers_traffic_guard() -> None:
    storage = MagicMock()
    cfg = MagicMock()
    cfg.radar_log_path = Path("/tmp/radar.log")
    now = time.time()
    storage.get_setting.side_effect = lambda key, default="0": {
        YOUDO_LAST_HARD_RESET_AT_KEY: str(now - 600),
        YOUDO_HARD_RESET_HOUR_START_KEY: str(now - 120),
        YOUDO_HARD_RESET_HOUR_COUNT_KEY: "8",
    }.get(key, default)

    with patch("youdo_parser._bump_youdo_fail_streak", return_value=1):
        with patch("youdo_parser.youdo_hard_reset_on_fail_enabled", return_value=True):
            with patch("youdo_parser._youdo_hard_reset_max_per_hour", return_value=8):
                with patch(
                    "youdo_parser._youdo_traffic_guard_cooldown_sec",
                    return_value=5400.0,
                ):
                    with patch("youdo_parser.youdo_hard_reset") as mock_reset:
                        with patch("youdo_parser.set_youdo_cooldown") as mock_cooldown:
                            with patch("youdo_parser.log_youdo_trace") as mock_trace:
                                _on_youdo_fetch_fail(cfg, storage)

    mock_reset.assert_not_called()
    mock_cooldown.assert_not_called()
    guard_calls = [
        c
        for c in storage.set_setting.call_args_list
        if c.args[0] == YOUDO_TRAFFIC_GUARD_UNTIL_KEY
    ]
    assert len(guard_calls) == 1
    assert float(guard_calls[0].args[1]) > now
    mock_trace.assert_called_once()
    assert mock_trace.call_args.args[1] == "hard_reset_hourly_cap"
