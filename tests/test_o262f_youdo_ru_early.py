"""O262f: ServicePipe early RU skip DC + RU carousel + tier wait."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from exchange_browser_fetch import (  # noqa: E402
    _fetch_youdo_listing_dc_first,
    _youdo_servicepipe_wait_sec,
)
from exchange_proxy import (  # noqa: E402
    _youdo_ru_retry_max,
    reset_cascade_state_for_tests,
    youdo_listing_slot_urls,
)
from html_fetch import HtmlFetchError  # noqa: E402

_DC = (
    "http://185.147.131.15:8000:u1:p1,"
    "http://194.0.0.2:8000:u2:p2,"
    "http://212.0.0.3:8000:u3:p3,"
    "http://213.0.0.4:8000:u4:p4"
)
_RU = ",".join(
    f"http://gate.node-proxy.com:{10000 + i}:ru{i}:rp{i}" for i in range(5)
)


def _dc_env(**extra: str) -> dict[str, str]:
    base = {
        "YOUDO_PROXY_URLS": f"{_DC},{_RU}",
        "YOUDO_DC_PROXY_URLS": _DC,
        "YOUDO_O191_DC_SLOTS": "4",
        "YOUDO_SLOT_RETRY_ON_TIMEOUT": "4",
        "YOUDO_RU_RETRY_MAX": "5",
        "YOUDO_SERVICEPIPE_EARLY_RU": "1",
    }
    base.update(extra)
    return base


@patch("exchange_proxy._storage")
def test_ru_retry_max_default_five(mock_storage: MagicMock) -> None:
    with patch.dict(os.environ, _dc_env(), clear=False):
        reset_cascade_state_for_tests()
        st = MagicMock()
        saved: dict[str, str] = {}
        st.get_setting.side_effect = lambda k, d="": saved.get(k, d)
        st.set_setting.side_effect = lambda k, v: saved.__setitem__(k, v)
        mock_storage.return_value = st
        assert _youdo_ru_retry_max() == 5


def test_servicepipe_wait_sec_by_tier() -> None:
    with patch.dict(
        os.environ,
        {
            "YOUDO_SERVICEPIPE_WAIT_SEC": "30",
            "YOUDO_SERVICEPIPE_WAIT_SEC_RU": "90",
        },
        clear=False,
    ):
        assert _youdo_servicepipe_wait_sec(tier="dc") == 30.0
        assert _youdo_servicepipe_wait_sec(tier="ru_fallback") == 90.0


@patch("exchange_browser_fetch._fetch_youdo_one_browser_slot")
@patch("youdo_parser.youdo_hard_reset")
@patch("exchange_proxy._storage")
def test_dc_servicepipe_x2_triggers_ru_carousel(
    mock_storage: MagicMock,
    mock_reset: MagicMock,
    mock_slot: MagicMock,
) -> None:
    sp_err = HtmlFetchError("ServicePipe antibot challenge (youdo).")
    ru_html = "<html>" + "x" * 9000 + '<a data-id="1" href="/t1">t</a></html>'
    calls: list[tuple[str, str]] = []

    def _side_effect(*_a, proxy_url: str, tier: str = "dc", **_kw):
        calls.append((tier, proxy_url))
        if tier.startswith("dc") or tier == "dc_hard_reset":
            raise sp_err
        return ru_html

    mock_slot.side_effect = _side_effect

    with patch.dict(os.environ, _dc_env(), clear=False):
        reset_cascade_state_for_tests()
        st = MagicMock()
        saved: dict[str, str] = {}
        st.get_setting.side_effect = lambda k, d="": saved.get(k, d)
        st.set_setting.side_effect = lambda k, v: saved.__setitem__(k, v)
        mock_storage.return_value = st

        html = _fetch_youdo_listing_dc_first(
            "https://youdo.com/tasks-all-opened-all",
            user_agent="Mozilla/5.0",
            timeout_sec=60.0,
        )
        assert "data-id" in html
        ru_attempts = [c for c in calls if c[0] == "ru_fallback"]
        assert len(ru_attempts) >= 1
        assert mock_reset.call_count == 0


@patch("exchange_browser_fetch._fetch_youdo_one_browser_slot")
@patch("exchange_proxy._storage")
def test_ru_listing_slots_respect_retry_max(
    mock_storage: MagicMock,
    mock_slot: MagicMock,
) -> None:
    mock_slot.return_value = "<html>" + "y" * 9000 + "</html>"

    with patch.dict(os.environ, _dc_env(YOUDO_RU_RETRY_MAX="3"), clear=False):
        reset_cascade_state_for_tests()
        st = MagicMock()
        saved: dict[str, str] = {}
        st.get_setting.side_effect = lambda k, d="": saved.get(k, d)
        st.set_setting.side_effect = lambda k, v: saved.__setitem__(k, v)
        mock_storage.return_value = st

        from exchange_proxy import _ban_url, _youdo_dc_pool

        for u in _youdo_dc_pool():
            _ban_url(u, source="youdo", reason="test")

        ru_slots = youdo_listing_slot_urls(include_ru=True)
        assert len(ru_slots) == 3
