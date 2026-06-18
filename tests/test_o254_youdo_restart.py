"""O254: ops YouDo restart — hard reset keys + restart_source control."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from owner_admin import run_ops_control  # noqa: E402
from youdo_parser import (  # noqa: E402
    YOUDO_COOLDOWN_KEY,
    YOUDO_FAIL_STREAK_KEY,
    YOUDO_FETCH_CYCLE_KEY,
    YOUDO_TRAFFIC_GUARD_UNTIL_KEY,
    youdo_hard_reset,
)


def test_youdo_hard_reset_clears_guard_keys() -> None:
    storage = MagicMock()
    with patch(
        "exchange_browser_fetch.youdo_browser_teardown",
        return_value=2,
    ) as mock_teardown:
        youdo_hard_reset(reason="test", storage=storage)

    calls = {c.args[0]: c.args[1] for c in storage.set_setting.call_args_list}
    assert calls[YOUDO_FAIL_STREAK_KEY] == "0"
    assert calls[YOUDO_TRAFFIC_GUARD_UNTIL_KEY] == "0"
    assert calls[YOUDO_COOLDOWN_KEY] == "0"
    assert calls[YOUDO_FETCH_CYCLE_KEY] == "0"
    mock_teardown.assert_called_once()


def test_youdo_browser_teardown_aborts_worker_and_cleans_camoufox() -> None:
    from exchange_browser_fetch import youdo_browser_teardown

    with patch("exchange_browser_fetch.close_all_browser_contexts") as mock_close:
        with patch("exchange_browser_fetch._abort_playwright_worker") as mock_abort:
            with patch(
                "exchange_browser_fetch.cleanup_stale_youdo_browser_processes",
                return_value=1,
            ) as mock_cleanup:
                killed = youdo_browser_teardown()

    assert killed == 1
    mock_close.assert_called_once()
    mock_abort.assert_called_once()
    mock_cleanup.assert_called_once()


@patch("owner_admin._resolve_sqlite_path", return_value=Path("/tmp/projects.db"))
@patch("owner_admin.ProjectStorage")
@patch("youdo_parser.youdo_hard_reset")
@patch("owner_admin._run_systemctl", return_value=(True, "ok"))
def test_ops_restart_source_youdo_hard_resets(
    _mock_systemctl: MagicMock,
    mock_hard_reset: MagicMock,
    mock_storage_cls: MagicMock,
    _mock_sqlite: MagicMock,
) -> None:
    storage = MagicMock()
    mock_storage_cls.return_value = storage

    result = run_ops_control(target="youdo", action="restart_source")

    assert result["ok"] is True
    assert "cooldown" in result["message"].casefold()
    mock_hard_reset.assert_called_once_with(
        reason="ops_restart_source",
        storage=storage,
    )
    storage.set_setting.assert_any_call("restart_source_youdo", "1")


@patch("owner_admin._resolve_sqlite_path", return_value=Path("/tmp/projects.db"))
@patch("owner_admin.ProjectStorage")
def test_ops_restart_source_fl_no_hard_reset(
    mock_storage_cls: MagicMock,
    _mock_sqlite: MagicMock,
) -> None:
    storage = MagicMock()
    mock_storage_cls.return_value = storage

    with patch("youdo_parser.youdo_hard_reset") as mock_hard_reset:
        result = run_ops_control(target="fl", action="restart_source")

    assert result["ok"] is True
    mock_hard_reset.assert_not_called()
    storage.set_setting.assert_called_once_with("restart_source_fl", "1")


def test_on_youdo_fetch_fail_auto_hard_reset_at_threshold() -> None:
    from youdo_parser import _on_youdo_fetch_fail

    storage = MagicMock()
    cfg = MagicMock()
    cfg.radar_log_path = Path("/tmp/radar.log")

    with patch("youdo_parser._bump_youdo_fail_streak", return_value=3):
        with patch("youdo_parser.youdo_hard_reset_on_fail_enabled", return_value=True):
            with patch("youdo_parser._youdo_hard_reset_fail_threshold", return_value=3):
                with patch("youdo_parser.youdo_hard_reset") as mock_reset:
                    with patch("youdo_parser.set_youdo_cooldown") as mock_cooldown:
                        _on_youdo_fetch_fail(cfg, storage)

    mock_reset.assert_called_once()
    mock_cooldown.assert_not_called()
