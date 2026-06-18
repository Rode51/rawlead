"""O259: YouDo DC carousel — rotate 4 DC on SPA shell before hard_reset / RU tier."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from exchange_browser_fetch import (  # noqa: E402
    _is_youdo_slot_retryable,
    fetch_listing_html_browser_slots,
)
from exchange_proxy import (  # noqa: E402
    _ban_url,
    _is_banned,
    _urls_for_source,
    clear_youdo_source_bans,
    exchange_primary_proxy_url,
    reset_cascade_state_for_tests,
    youdo_browser_slot_fail,
    youdo_dc_alive_urls,
)
from html_fetch import HtmlFetchError  # noqa: E402
from youdo_parser import _on_youdo_fetch_fail  # noqa: E402


def _dc_env() -> dict[str, str]:
    dc = (
        "http://185.147.131.15:8000:u1:p1,"
        "http://194.0.0.2:8000:u2:p2,"
        "http://212.0.0.3:8000:u3:p3,"
        "http://213.0.0.4:8000:u4:p4"
    )
    ru = "http://5.6.7.8:8000:ru1:rp1,http://9.10.11.12:8000:ru2:rp2"
    return {
        "YOUDO_PROXY_URLS": f"{dc},{ru}",
        "YOUDO_DC_PROXY_URLS": dc,
        "YOUDO_O191_DC_SLOTS": "4",
        "YOUDO_SLOT_RETRY_ON_TIMEOUT": "4",
    }


def test_spa_shell_without_task_cards_is_retryable() -> None:
    exc = HtmlFetchError("SPA shell without task cards (youdo).")
    assert _is_youdo_slot_retryable(exc)


@patch("exchange_proxy._storage")
def test_youdo_dc_fail_bans_and_advances_within_dc_not_ru(mock_storage: MagicMock) -> None:
    with patch.dict(os.environ, _dc_env(), clear=False):
        reset_cascade_state_for_tests()
        st = MagicMock()
        saved: dict[str, str] = {}
        st.get_setting.side_effect = lambda k, d="": saved.get(k, d)
        st.set_setting.side_effect = lambda k, v: saved.__setitem__(k, v)
        mock_storage.return_value = st

        pool_key, source, urls = _urls_for_source("youdo")
        dc1 = urls[0]
        dc2 = urls[1]
        ru1 = urls[4]

        ok = youdo_browser_slot_fail(dc1, reason="browser:SPA shell")
        assert ok
        assert _is_banned(dc1, source)
        assert not _is_banned(ru1, source)
        primary = exchange_primary_proxy_url("youdo")
        assert primary == dc2
        assert primary != dc1

        cleared = clear_youdo_source_bans()
        assert cleared >= 1


@patch("exchange_proxy._storage")
def test_fl_ban_untouched_when_youdo_bans_same_host(mock_storage: MagicMock) -> None:
    with patch.dict(os.environ, _dc_env(), clear=False):
        reset_cascade_state_for_tests()
        st = MagicMock()
        saved: dict[str, str] = {}
        st.get_setting.side_effect = lambda k, d="": saved.get(k, d)
        st.set_setting.side_effect = lambda k, v: saved.__setitem__(k, v)
        mock_storage.return_value = st

        shared = "http://185.147.131.15:8000:u1:p1"
        os.environ["FL_PROXY_URLS"] = shared
        reset_cascade_state_for_tests()

        youdo_browser_slot_fail(shared, reason="browser:SPA shell")
        assert _is_banned(shared, "youdo")
        assert not _is_banned(shared, "fl")


@patch("exchange_browser_fetch._youdo_browser_slot_fail")
@patch("exchange_browser_fetch._abort_playwright_worker")
@patch("exchange_browser_fetch._fetch_youdo_ephemeral")
@patch("exchange_browser_fetch.fetch_youdo_html_browser")
def test_spa_shell_slot1_retries_slot2_without_hard_reset(
    mock_human: MagicMock,
    mock_ephemeral: MagicMock,
    mock_abort: MagicMock,
    mock_youdo_ban: MagicMock,
) -> None:
    dc1 = "http://u:p@185.147.131.15:8000"
    dc2 = "http://u:p@194.0.0.2:8000"
    mock_human.side_effect = HtmlFetchError("SPA shell without task cards (youdo).")
    card = '<a data-id="99001" href="https://youdo.com/t99001">Task</a>'
    mock_ephemeral.return_value = "<html><body>" + card + ("x" * 2000) + "</body></html>"

    with patch(
        "exchange_browser_fetch._youdo_fetch_tier_plan",
        return_value=[(dc1, "dc"), (dc2, "dc")],
    ):
        fetch_listing_html_browser_slots(
            "youdo",
            "https://youdo.com/tasks-all-opened-all",
            user_agent="Mozilla/5.0 Chrome/122",
        )

    mock_human.assert_called_once()
    mock_ephemeral.assert_called_once()
    mock_youdo_ban.assert_called_once()
    mock_abort.assert_called_once()


def test_on_youdo_fetch_fail_hard_reset_after_fetch_exhausted_even_if_dc_alive() -> None:
    storage = MagicMock()
    cfg = MagicMock()
    cfg.radar_log_path = Path("/tmp/radar.log")

    with patch("youdo_parser._bump_youdo_fail_streak", return_value=1):
        with patch("youdo_parser.youdo_hard_reset_on_fail_enabled", return_value=True):
            with patch("youdo_parser._youdo_dc_carousel_has_alive", return_value=True):
                with patch("youdo_parser.youdo_hard_reset") as mock_reset:
                    with patch("youdo_parser.set_youdo_cooldown") as mock_cooldown:
                        _on_youdo_fetch_fail(cfg, storage)

    mock_reset.assert_called_once()
    mock_cooldown.assert_not_called()


@patch("exchange_proxy._storage")
def test_all_dc_banned_dc_alive_empty(mock_storage: MagicMock) -> None:
    with patch.dict(os.environ, _dc_env(), clear=False):
        reset_cascade_state_for_tests()
        st = MagicMock()
        saved: dict[str, str] = {}
        st.get_setting.side_effect = lambda k, d="": saved.get(k, d)
        st.set_setting.side_effect = lambda k, v: saved.__setitem__(k, v)
        mock_storage.return_value = st

        _, source, urls = _urls_for_source("youdo")
        for u in urls[:4]:
            _ban_url(u, source=source, reason="test", slot_idx=0)

        assert len(youdo_dc_alive_urls()) == 0
