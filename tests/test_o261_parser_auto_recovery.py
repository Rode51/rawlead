"""O261: FL dead-proxy rotate, YouDo DC ban limit, auto-unban, ops clear-youdo-bans."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from exchange_browser_fetch import (  # noqa: E402
    _is_fl_dead_proxy_error,
    fetch_listing_html_browser_slots,
)
from exchange_proxy import (  # noqa: E402
    _ban_url,
    _is_banned,
    clear_fl_source_bans,
    clear_youdo_source_bans,
    exchange_fetch_begin,
    exchange_get,
    fl_browser_dead_proxy_fail,
    is_proxy_connection_error,
    reset_cascade_state_for_tests,
    youdo_dc_alive_urls,
    youdo_maybe_auto_unban_dc,
)
from html_fetch import HtmlFetchError  # noqa: E402
from proxy_ops import run_proxy_control  # noqa: E402


def _dc4_env() -> dict[str, str]:
    dc = (
        "http://185.147.131.15:8000:u1:p1,"
        "http://194.0.0.2:8000:u2:p2,"
        "http://212.0.0.3:8000:u3:p3,"
        "http://213.0.0.4:8000:u4:p4"
    )
    ru = "http://5.6.7.8:8000:ru1:rp1"
    return {
        "FL_PROXY_URLS": dc,
        "YOUDO_PROXY_URLS": f"{dc},{ru}",
        "YOUDO_DC_PROXY_URLS": dc,
        "YOUDO_O191_DC_SLOTS": "4",
        "YOUDO_SLOT_RETRY_ON_TIMEOUT": "4",
        "FL_SLOT_RETRY_MAX": "4",
        "FL_HARD_RESET_ON_BAN": "1",
    }


def test_is_fl_dead_proxy_error() -> None:
    exc = HtmlFetchError("Page.goto: net::ERR_PROXY_CONNECTION_FAILED")
    assert _is_fl_dead_proxy_error(exc)
    assert is_proxy_connection_error(
        requests.exceptions.ProxyError("Cannot connect to proxy")
    )


@patch("exchange_proxy._storage")
def test_fl_dead_proxy_bans_short_ttl_and_rotates(mock_storage: MagicMock) -> None:
    with patch.dict(os.environ, _dc4_env(), clear=False):
        reset_cascade_state_for_tests()
        st = MagicMock()
        saved: dict[str, str] = {}
        st.get_setting.side_effect = lambda k, d="": saved.get(k, d)
        st.set_setting.side_effect = lambda k, v: saved.__setitem__(k, v)
        mock_storage.return_value = st

        _, _, urls = __import__("exchange_proxy")._urls_for_source("fl")
        dc1, dc2 = urls[0], urls[1]

        ok = fl_browser_dead_proxy_fail(dc1, reason="dead_proxy:test")
        assert ok
        assert _is_banned(dc1, "fl")
        assert not _is_banned(dc2, "fl")


@patch("exchange_browser_fetch._abort_playwright_worker")
@patch("exchange_browser_fetch.fetch_listing_html_browser")
@patch("exchange_proxy._storage")
def test_fl_browser_dead_proxy_rotates_not_antibot(
    mock_storage: MagicMock,
    mock_fetch: MagicMock,
    mock_abort: MagicMock,
) -> None:
    with patch.dict(os.environ, _dc4_env(), clear=False):
        reset_cascade_state_for_tests()
        st = MagicMock()
        saved: dict[str, str] = {}
        st.get_setting.side_effect = lambda k, d="": saved.get(k, d)
        st.set_setting.side_effect = lambda k, v: saved.__setitem__(k, v)
        mock_storage.return_value = st

        _, _, urls = __import__("exchange_proxy")._urls_for_source("fl")
        dc1, dc2 = urls[0], urls[1]

        mock_fetch.side_effect = [
            HtmlFetchError("net::ERR_PROXY_CONNECTION_FAILED"),
            "<html>b-page__lenta_item</html>",
        ]

        with patch("exchange_browser_fetch.fl_hard_reset") as mock_reset:
            html = fetch_listing_html_browser_slots(
                "fl",
                "https://www.fl.ru/projects/",
                user_agent="ua",
            )
            assert "b-page__lenta_item" in html
            mock_reset.assert_not_called()
            assert mock_fetch.call_count == 2
            assert mock_fetch.call_args_list[1].kwargs.get("proxy_url") == dc2


@patch("exchange_browser_fetch._youdo_browser_slot_fail")
@patch("exchange_browser_fetch._fetch_youdo_one_browser_slot")
@patch("exchange_proxy._storage")
def test_youdo_dc_ban_limit_stops_second_ban_in_same_fetch(
    mock_storage: MagicMock,
    mock_one_slot: MagicMock,
    mock_slot_fail: MagicMock,
) -> None:
    env = {**_dc4_env(), "YOUDO_MAX_DC_BANS_PER_FETCH": "1", "YOUDO_ONE_SLOT_PER_CYCLE": "1"}
    with patch.dict(os.environ, env, clear=False):
        reset_cascade_state_for_tests()
        st = MagicMock()
        saved: dict[str, str] = {}
        st.get_setting.side_effect = lambda k, d="": saved.get(k, d)
        st.set_setting.side_effect = lambda k, v: saved.__setitem__(k, v)
        mock_storage.return_value = st

        mock_one_slot.side_effect = HtmlFetchError("SPA shell without task cards")

        with patch("exchange_browser_fetch._on_playwright_thread", return_value=True):
            with pytest.raises(HtmlFetchError):
                fetch_listing_html_browser_slots(
                    "youdo",
                    "https://youdo.com/tasks-all-opened-all",
                    user_agent="ua",
                )

        assert mock_slot_fail.call_count == 1


@patch("youdo_parser.youdo_hard_reset")
@patch("exchange_proxy._storage")
def test_youdo_auto_unban_after_dc_zero_minutes(
    mock_storage: MagicMock,
    mock_reset: MagicMock,
) -> None:
    env = {**_dc4_env(), "YOUDO_AUTO_UNBAN_MIN": "20"}
    with patch.dict(os.environ, env, clear=False):
        reset_cascade_state_for_tests()
        st = MagicMock()
        saved: dict[str, str] = {}
        st.get_setting.side_effect = lambda k, d="": saved.get(k, d)
        st.set_setting.side_effect = lambda k, v: saved.__setitem__(k, v)
        mock_storage.return_value = st

        _, source, urls = __import__("exchange_proxy")._urls_for_source("youdo")
        for u in urls[:4]:
            _ban_url(u, source=source, reason="test", slot_idx=0)

        saved["youdo_dc_banned_since"] = str(time.time() - 1300)

        assert len(youdo_dc_alive_urls()) == 0
        assert youdo_maybe_auto_unban_dc()
        assert len(youdo_dc_alive_urls()) == 4
        mock_reset.assert_called_once()


@patch("youdo_parser.youdo_hard_reset")
@patch("exchange_proxy._storage")
def test_ops_clear_youdo_bans_only_youdo(
    mock_storage: MagicMock,
    mock_reset: MagicMock,
) -> None:
    with patch.dict(os.environ, _dc4_env(), clear=False):
        reset_cascade_state_for_tests()
        st = MagicMock()
        saved: dict[str, str] = {}
        st.get_setting.side_effect = lambda k, d="": saved.get(k, d)
        st.set_setting.side_effect = lambda k, v: saved.__setitem__(k, v)
        mock_storage.return_value = st

        shared = "http://185.147.131.15:8000:u1:p1"
        _ban_url(shared, source="youdo", reason="test", slot_idx=0)
        _ban_url(shared, source="fl", reason="test", slot_idx=0)

        result = run_proxy_control(action="clear-youdo-bans")
        assert result["ok"]
        assert result["cleared"] >= 1
        assert not _is_banned(shared, "youdo")
        assert _is_banned(shared, "fl")
        mock_reset.assert_called_once()
