"""O267: YouDo persistent profile + soft ServicePipe fail + ephemeral gate."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from exchange_browser_fetch import (  # noqa: E402
    _clear_youdo_soft_sp_fetch_fail,
    _fetch_youdo_one_browser_slot,
    _youdo_browser_slot_fail_limited,
    _youdo_goto_wait_until,
    _youdo_persistent_profile_dir,
    _youdo_servicepipe_wait_sec,
    _youdo_sticky_spawn_worker,
    _wipe_youdo_persistent_profiles,
    youdo_last_fetch_was_soft_servicepipe,
    youdo_persistent_profile_enabled,
)
from html_fetch import HtmlFetchError  # noqa: E402

_LISTING = "https://youdo.com/tasks-all-opened-all"
_PROXY = "http://u1:p1@185.147.128.237:8000"


@pytest.fixture(autouse=True)
def _reset_soft_sp() -> None:
    _clear_youdo_soft_sp_fetch_fail()


def test_persistent_profile_dir_stable_per_proxy() -> None:
    path1 = _youdo_persistent_profile_dir(_PROXY)
    path2 = _youdo_persistent_profile_dir(_PROXY)
    assert path1 == path2
    assert path1.name == "youdo_185.147.128.237:8000"
    assert path1.parent.name == "data"


def test_persistent_profile_env_gate() -> None:
    with patch.dict(os.environ, {"YOUDO_PERSISTENT_PROFILE": "1"}, clear=False):
        assert youdo_persistent_profile_enabled() is True
    with patch.dict(os.environ, {"YOUDO_PERSISTENT_PROFILE": "0"}, clear=False):
        assert youdo_persistent_profile_enabled() is False


def test_goto_wait_until_default_domcontentloaded() -> None:
    env = os.environ.copy()
    env.pop("YOUDO_GOTO_WAIT_UNTIL", None)
    with patch.dict(os.environ, env, clear=True):
        assert _youdo_goto_wait_until() == "domcontentloaded"


def test_servicepipe_wait_default_90_dc() -> None:
    env = os.environ.copy()
    env.pop("YOUDO_SERVICEPIPE_WAIT_SEC", None)
    with patch.dict(os.environ, env, clear=True):
        assert _youdo_servicepipe_wait_sec(tier="dc") == 90.0


@patch("exchange_browser_fetch._on_playwright_thread", return_value=True)
@patch("exchange_browser_fetch._youdo_is_camoufox", return_value=True)
@patch("exchange_browser_fetch._fetch_youdo_ephemeral")
@patch("exchange_browser_fetch._fetch_youdo_sticky_listing")
def test_slot1_ephemeral_when_persistent_on_o268(
    mock_sticky: MagicMock,
    mock_ephemeral: MagicMock,
    _mock_cf: MagicMock,
    _mock_pw: MagicMock,
) -> None:
    mock_ephemeral.return_value = "<html>" + "x" * 100_001 + "</html>"
    with patch.dict(
        os.environ,
        {
            "YOUDO_STICKY_SESSION": "1",
            "YOUDO_PERSISTENT_PROFILE": "1",
            "YOUDO_STICKY_AFTER_OK": "1",
            "YOUDO_EPHEMERAL": "0",
        },
        clear=False,
    ):
        _fetch_youdo_one_browser_slot(
            _LISTING,
            user_agent="Mozilla/5.0",
            timeout_sec=60.0,
            proxy_url=_PROXY,
            slots_tried=1,
        )
    mock_ephemeral.assert_called_once()
    mock_sticky.assert_not_called()


@patch("exchange_browser_fetch._on_playwright_thread", return_value=True)
@patch("exchange_browser_fetch._youdo_is_camoufox", return_value=True)
@patch("exchange_browser_fetch._fetch_youdo_sticky_listing")
def test_slot1_sticky_without_persistent_not_ephemeral(
    mock_sticky: MagicMock,
    _mock_cf: MagicMock,
    _mock_pw: MagicMock,
) -> None:
    mock_sticky.return_value = "<html>" + "x" * 9000 + "</html>"
    with patch.dict(
        os.environ,
        {
            "YOUDO_STICKY_SESSION": "1",
            "YOUDO_PERSISTENT_PROFILE": "0",
            "YOUDO_EPHEMERAL": "0",
        },
        clear=False,
    ):
        _fetch_youdo_one_browser_slot(
            _LISTING,
            user_agent="Mozilla/5.0",
            timeout_sec=60.0,
            proxy_url=_PROXY,
            slots_tried=1,
        )
    mock_sticky.assert_called_once()


@patch("exchange_browser_fetch._youdo_browser_slot_fail")
def test_soft_sp_skip_slot_ban_first_fail(mock_slot_fail: MagicMock) -> None:
    exc = HtmlFetchError("ServicePipe antibot challenge (youdo).")
    dc_bans = [0]
    ok = _youdo_browser_slot_fail_limited(
        _PROXY,
        exc,
        dc_bans_this_fetch=dc_bans,
        skip_slot_ban=True,
    )
    assert ok is True
    assert dc_bans[0] == 0
    mock_slot_fail.assert_not_called()


@patch("exchange_browser_fetch.subprocess.Popen")
def test_spawn_worker_sets_persistent_env(mock_popen: MagicMock) -> None:
    mock_popen.return_value = MagicMock()
    with patch.dict(
        os.environ,
        {"YOUDO_PERSISTENT_PROFILE": "1"},
        clear=False,
    ):
        _youdo_sticky_spawn_worker(
            proxy_url=_PROXY,
            user_agent="Mozilla/5.0",
        )
    _, kwargs = mock_popen.call_args
    env = kwargs["env"]
    assert env["YOUDO_PERSISTENT_PROFILE"] == "1"
    assert "YOUDO_PROFILE_DATA_DIR" in env


def test_wipe_persistent_profile_dir(tmp_path: Path) -> None:
    profile = tmp_path / "youdo_testhint"
    profile.mkdir()
    (profile / "cookies.sqlite").write_bytes(b"x" * 600)
    with patch(
        "exchange_browser_fetch._youdo_persistent_profile_dir",
        return_value=profile,
    ):
        wiped = _wipe_youdo_persistent_profiles(proxy_url=_PROXY)
    assert wiped == 1
    assert not profile.exists()


@patch("youdo_parser.youdo_hard_reset_on_fail_enabled", return_value=True)
@patch("youdo_parser._youdo_hard_reset_fail_threshold", return_value=1)
@patch("youdo_parser._get_youdo_fail_streak", return_value=0)
@patch("youdo_parser._bump_youdo_fail_streak", return_value=1)
@patch("youdo_parser.youdo_hard_reset")
def test_on_fetch_fail_skips_hard_reset_on_soft_sp_streak1(
    mock_reset: MagicMock,
    _mock_bump: MagicMock,
    _mock_get: MagicMock,
    _mock_thr: MagicMock,
    _mock_enabled: MagicMock,
) -> None:
    from config import Config
    from youdo_parser import _on_youdo_fetch_fail

    cfg = MagicMock(spec=Config)
    storage = MagicMock()
    with patch("exchange_browser_fetch.youdo_sticky_session_warm", return_value=False):
        with patch("exchange_browser_fetch.youdo_last_fetch_was_soft_servicepipe", return_value=True):
            with patch("youdo_parser.set_youdo_cooldown") as mock_cd:
                _on_youdo_fetch_fail(cfg, storage)
    mock_reset.assert_not_called()
    mock_cd.assert_called_once()


def test_mark_soft_sp_fetch_fail_flag() -> None:
    from exchange_browser_fetch import _mark_youdo_soft_sp_fetch_fail

    assert youdo_last_fetch_was_soft_servicepipe() is False
    _mark_youdo_soft_sp_fetch_fail()
    assert youdo_last_fetch_was_soft_servicepipe() is True
    _clear_youdo_soft_sp_fetch_fail()
    assert youdo_last_fetch_was_soft_servicepipe() is False
