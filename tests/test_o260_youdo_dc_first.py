"""O260: YouDo DC-first tier canon — DC primary, RU only when all DC banned."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from exchange_proxy import (  # noqa: E402
    _active_slot,
    _ban_url,
    _banned_until,
    _ban_meta,
    _hint_from_url,
    _is_banned,
    _urls_for_source,
    _youdo_ru_pool,
    exchange_primary_proxy_url,
    proxy_log_hint,
    reset_cascade_state_for_tests,
    youdo_browser_slot_fail,
    youdo_dc_alive_urls,
    youdo_listing_slot_urls,
    youdo_realign_to_dc_tier,
)
from html_fetch import HtmlFetchError  # noqa: E402


def _dc_env() -> dict[str, str]:
    dc = (
        "http://185.147.131.15:8000:u1:p1,"
        "http://194.0.0.2:8000:u2:p2,"
        "http://212.0.0.3:8000:u3:p3,"
        "http://213.0.0.4:8000:u4:p4"
    )
    ru = ",".join(
        f"http://gate.node-proxy.com:{10000 + i}:ru{i}:rp{i}" for i in range(3)
    )
    return {
        "YOUDO_PROXY_URLS": f"{dc},{ru}",
        "YOUDO_DC_PROXY_URLS": dc,
        "YOUDO_O191_DC_SLOTS": "4",
        "YOUDO_SLOT_RETRY_ON_TIMEOUT": "4",
    }


@patch("exchange_proxy._storage")
def test_dc_alive_primary_never_ru(mock_storage: MagicMock) -> None:
    with patch.dict(os.environ, _dc_env(), clear=False):
        reset_cascade_state_for_tests()
        st = MagicMock()
        saved: dict[str, str] = {"exchange_proxy_active_slot_v1": '{"youdo": 6}'}
        st.get_setting.side_effect = lambda k, d="": saved.get(k, d)
        st.set_setting.side_effect = lambda k, v: saved.__setitem__(k, v)
        mock_storage.return_value = st

        from exchange_proxy import _load_persistence

        _load_persistence()

        primary = exchange_primary_proxy_url("youdo")
        ru_pool = _youdo_ru_pool()
        assert primary
        assert primary not in ru_pool
        slots = youdo_listing_slot_urls(include_ru=False)
        assert slots
        assert all(s not in ru_pool for s in slots)
        assert _active_slot.get("youdo", 0) < 4


@patch("exchange_proxy._storage")
def test_proxy_log_hint_dc_slot_not_full_list(mock_storage: MagicMock) -> None:
    with patch.dict(os.environ, _dc_env(), clear=False):
        reset_cascade_state_for_tests()
        st = MagicMock()
        saved: dict[str, str] = {}
        st.get_setting.side_effect = lambda k, d="": saved.get(k, d)
        st.set_setting.side_effect = lambda k, v: saved.__setitem__(k, v)
        mock_storage.return_value = st

        hint = proxy_log_hint("youdo")
        assert "tier=dc" in hint
        assert "slot=1/4" in hint or "slot=2/4" in hint
        assert "/26" not in hint
        assert "gate.node-proxy" not in hint.split("ru_alive")[0]


@patch("exchange_proxy._storage")
def test_listing_slots_no_ru_while_dc_alive(mock_storage: MagicMock) -> None:
    with patch.dict(os.environ, _dc_env(), clear=False):
        reset_cascade_state_for_tests()
        st = MagicMock()
        saved: dict[str, str] = {}
        st.get_setting.side_effect = lambda k, d="": saved.get(k, d)
        st.set_setting.side_effect = lambda k, v: saved.__setitem__(k, v)
        mock_storage.return_value = st

        dc_only = youdo_listing_slot_urls(include_ru=False)
        with_ru = youdo_listing_slot_urls(include_ru=True)
        ru_pool = set(_youdo_ru_pool())
        assert len(youdo_dc_alive_urls()) == 4
        assert dc_only
        assert all(u not in ru_pool for u in dc_only)
        assert with_ru == dc_only


@patch("exchange_proxy._storage")
def test_all_dc_banned_one_ru_slot(mock_storage: MagicMock) -> None:
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
        with patch.dict(os.environ, {"YOUDO_RU_RETRY_MAX": "1"}, clear=False):
            ru_slots = youdo_listing_slot_urls(include_ru=True)
            assert len(ru_slots) == 1
        assert ru_slots[0] in _youdo_ru_pool()


@patch("exchange_proxy._storage")
def test_ban_expiry_dc_restored(mock_storage: MagicMock) -> None:
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
        dc1 = urls[0]
        key = f"youdo:{_hint_from_url(dc1)}"
        _banned_until[key] = time.time() - 1

        from exchange_proxy import _prune_expired_bans

        _prune_expired_bans()
        assert len(youdo_dc_alive_urls()) >= 1
        assert youdo_realign_to_dc_tier() or exchange_primary_proxy_url("youdo")


@patch("exchange_browser_fetch._youdo_browser_slot_fail")
@patch("exchange_browser_fetch._abort_playwright_worker")
@patch("youdo_parser.youdo_hard_reset")
@patch("exchange_browser_fetch._fetch_youdo_ephemeral")
@patch("exchange_browser_fetch.fetch_youdo_html_browser")
def test_dc_fetch_exhausted_hard_reset_no_ru(
    mock_human: MagicMock,
    mock_ephemeral: MagicMock,
    mock_hard_reset: MagicMock,
    mock_abort: MagicMock,
    mock_ban: MagicMock,
) -> None:
    from exchange_browser_fetch import fetch_listing_html_browser_slots

    dc1 = "http://u:p@185.147.131.15:8000"
    dc2 = "http://u:p@194.0.0.2:8000"
    mock_human.side_effect = HtmlFetchError("SPA shell without task cards (youdo).")
    mock_ephemeral.side_effect = HtmlFetchError("SPA shell without task cards (youdo).")

    with patch.dict(os.environ, _dc_env(), clear=False):
        with patch(
            "exchange_browser_fetch._youdo_fetch_tier_plan",
            return_value=[(dc1, "dc"), (dc2, "dc")],
        ):
            with patch(
                "exchange_proxy.youdo_dc_alive_urls",
                return_value=[dc1, dc2],
            ):
                with patch(
                    "exchange_proxy.youdo_listing_slot_urls",
                    side_effect=lambda *, include_ru=False: [dc1, dc2]
                    if not include_ru
                    else [],
                ):
                    with pytest.raises(HtmlFetchError):
                        fetch_listing_html_browser_slots(
                            "youdo",
                            "https://youdo.com/tasks-all-opened-all",
                            user_agent="Mozilla/5.0",
                        )

    mock_hard_reset.assert_called()


@patch("exchange_proxy._storage")
def test_youdo_dc_fail_advances_within_dc_pool_only(mock_storage: MagicMock) -> None:
    with patch.dict(os.environ, _dc_env(), clear=False):
        reset_cascade_state_for_tests()
        st = MagicMock()
        saved: dict[str, str] = {}
        st.get_setting.side_effect = lambda k, d="": saved.get(k, d)
        st.set_setting.side_effect = lambda k, v: saved.__setitem__(k, v)
        mock_storage.return_value = st

        _, source, urls = _urls_for_source("youdo")
        dc1, dc2 = urls[0], urls[1]
        ru1 = urls[4]

        youdo_browser_slot_fail(dc1, reason="browser:SPA shell")
        assert _is_banned(dc1, source)
        assert not _is_banned(ru1, source)
        assert exchange_primary_proxy_url("youdo") == dc2
