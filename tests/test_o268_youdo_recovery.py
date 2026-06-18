"""O268: YouDo recovery — ephemeral-first, profile poison wipe, RU burst cap."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from exchange_browser_fetch import (  # noqa: E402
    _consume_youdo_ru_burst,
    _fetch_youdo_listing_dc_first,
    _fetch_youdo_one_browser_slot,
    _wipe_youdo_persistent_profiles,
    _youdo_ephemeral_first_slot1,
    _youdo_goto_wait_until,
    _youdo_persistent_profile_dir,
    _youdo_ru_burst_allowed,
    _youdo_should_use_sticky_listing,
    _youdo_sticky_reload_sp_abort_sec,
    reset_youdo_sticky_for_tests,
    youdo_sticky_after_ok_enabled,
)
from html_fetch import HtmlFetchError  # noqa: E402

_LISTING = "https://youdo.com/tasks-all-opened-all"
_PROXY = "http://u1:p1@194.226.236.197:8000"
_RU_PROXY = "http://u1:p1@5.6.7.8:8000"
_BIG_HTML = "<html><body>" + ("x" * 100_001) + "</body></html>"


@pytest.fixture(autouse=True)
def _reset_session() -> None:
    reset_youdo_sticky_for_tests()


def test_goto_wait_until_default_domcontentloaded() -> None:
    env = os.environ.copy()
    env.pop("YOUDO_GOTO_WAIT_UNTIL", None)
    with patch.dict(os.environ, env, clear=True):
        assert _youdo_goto_wait_until() == "domcontentloaded"


def test_profile_dir_generation_suffix() -> None:
    with patch.dict(os.environ, {"YOUDO_PROFILE_GENERATION": "2"}, clear=False):
        path = _youdo_persistent_profile_dir(_PROXY)
    assert path.name == "youdo_194.226.236.197:8000_g2"


def test_ephemeral_first_slot1_when_persistent_without_session_ok() -> None:
    with patch.dict(
        os.environ,
        {
            "YOUDO_PERSISTENT_PROFILE": "1",
            "YOUDO_STICKY_AFTER_OK": "1",
        },
        clear=False,
    ):
        with patch("exchange_browser_fetch._youdo_is_camoufox", return_value=True):
            assert _youdo_ephemeral_first_slot1(slots_tried=1) is True
            assert _youdo_should_use_sticky_listing(
                slots_tried=1,
                use_ephemeral=False,
            ) is False


@patch("exchange_browser_fetch._on_playwright_thread", return_value=True)
@patch("exchange_browser_fetch._youdo_is_camoufox", return_value=True)
@patch("exchange_browser_fetch._fetch_youdo_ephemeral")
@patch("exchange_browser_fetch._fetch_youdo_sticky_listing")
def test_slot1_ephemeral_when_persistent_on(
    mock_sticky: MagicMock,
    mock_ephemeral: MagicMock,
    _mock_cf: MagicMock,
    _mock_pw: MagicMock,
) -> None:
    mock_ephemeral.return_value = _BIG_HTML
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
        html = _fetch_youdo_one_browser_slot(
            _LISTING,
            user_agent="Mozilla/5.0",
            timeout_sec=60.0,
            proxy_url=_PROXY,
            slots_tried=1,
        )
    assert html == _BIG_HTML
    mock_ephemeral.assert_called_once()
    mock_sticky.assert_not_called()


@patch("exchange_browser_fetch._on_playwright_thread", return_value=True)
@patch("exchange_browser_fetch._youdo_is_camoufox", return_value=True)
@patch("exchange_browser_fetch._fetch_youdo_ephemeral")
@patch("exchange_browser_fetch._fetch_youdo_sticky_listing")
def test_slot1_sticky_after_session_ok(
    mock_sticky: MagicMock,
    mock_ephemeral: MagicMock,
    _mock_cf: MagicMock,
    _mock_pw: MagicMock,
) -> None:
    mock_sticky.return_value = _BIG_HTML
    mock_ephemeral.return_value = _BIG_HTML
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
        _fetch_youdo_one_browser_slot(
            _LISTING,
            user_agent="Mozilla/5.0",
            timeout_sec=60.0,
            proxy_url=_PROXY,
            slots_tried=1,
        )
    mock_sticky.assert_called_once()
    assert mock_ephemeral.call_count == 1


def test_wipe_logs_profile_wiped_sp(tmp_path: Path) -> None:
    profile = tmp_path / "youdo_testhint_g2"
    profile.mkdir()
    (profile / "cookies.sqlite").write_bytes(b"x" * 600)
    with patch(
        "exchange_browser_fetch._youdo_persistent_profile_dir",
        return_value=profile,
    ):
        wiped = _wipe_youdo_persistent_profiles(proxy_url=_PROXY, reason="sp")
    assert wiped == 1
    assert not profile.exists()


def test_sticky_reload_sp_abort_default_15() -> None:
    env = os.environ.copy()
    env.pop("YOUDO_STICKY_RELOAD_SP_ABORT_SEC", None)
    with patch.dict(os.environ, env, clear=True):
        assert _youdo_sticky_reload_sp_abort_sec() == 15.0


@patch("exchange_proxy._storage")
def test_ru_burst_cap_blocks_third_attempt(mock_storage: MagicMock) -> None:
    saved: dict[str, str] = {}
    st = MagicMock()
    st.get_setting.side_effect = lambda k, d="": saved.get(k, d)
    st.set_setting.side_effect = lambda k, v: saved.__setitem__(k, v)
    mock_storage.return_value = st

    with patch.dict(os.environ, {"YOUDO_RU_BURST_MAX_PER_DAY": "2"}, clear=False):
        assert _youdo_ru_burst_allowed()[0] is True
        _consume_youdo_ru_burst()
        _consume_youdo_ru_burst()
        allowed, count, max_per = _youdo_ru_burst_allowed()
        assert allowed is False
        assert count == 2
        assert max_per == 2


@patch("exchange_browser_fetch._fetch_youdo_one_browser_slot")
@patch("exchange_proxy._storage")
def test_ru_only_after_dc_exhausted_respects_burst_cap(
    mock_storage: MagicMock,
    mock_slot: MagicMock,
) -> None:
    sp_err = HtmlFetchError("ServicePipe antibot challenge (youdo).")
    ru_html = "<html>" + "x" * 9000 + '<a data-id="1" href="/t1">t</a></html>'
    calls: list[str] = []

    def _side_effect(*_a, proxy_url: str, tier: str = "dc", **_kw):
        calls.append(tier)
        if tier.startswith("dc") or tier == "dc_hard_reset":
            raise sp_err
        return ru_html

    mock_slot.side_effect = _side_effect

    saved: dict[str, str] = {}
    st = MagicMock()
    st.get_setting.side_effect = lambda k, d="": saved.get(k, d)
    st.set_setting.side_effect = lambda k, v: saved.__setitem__(k, v)
    mock_storage.return_value = st

    env = {
        "YOUDO_DC_PROXY_URLS": _PROXY,
        "YOUDO_PROXY_URLS": f"{_PROXY},{_RU_PROXY}",
        "YOUDO_O191_DC_SLOTS": "1",
        "YOUDO_SERVICEPIPE_EARLY_RU": "0",
        "YOUDO_SOFT_SERVICEPIPE_BAN": "0",
        "YOUDO_RU_RETRY_MAX": "1",
        "YOUDO_RU_BURST_MAX_PER_DAY": "2",
        "YOUDO_SLOT_RETRY_ON_TIMEOUT": "1",
    }
    with patch.dict(os.environ, env, clear=False):
        from exchange_proxy import reset_cascade_state_for_tests

        reset_cascade_state_for_tests()
        html = _fetch_youdo_listing_dc_first(
            _LISTING,
            user_agent="Mozilla/5.0",
            timeout_sec=60.0,
        )
    assert "data-id" in html
    assert calls.count("ru_fallback") == 1


def test_sticky_after_ok_env_gate() -> None:
    with patch.dict(os.environ, {"YOUDO_STICKY_AFTER_OK": "1"}, clear=False):
        assert youdo_sticky_after_ok_enabled() is True
    with patch.dict(os.environ, {"YOUDO_STICKY_AFTER_OK": "0"}, clear=False):
        assert youdo_sticky_after_ok_enabled() is False
