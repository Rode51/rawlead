"""O222: FL hard reset on first ban — no multi-slot cascade in one cycle."""

from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from exchange_browser_fetch import (  # noqa: E402
    fetch_listing_html_browser_slots,
    fl_hard_reset,
    fl_listing_user_agent,
    reset_playwright_thread_for_tests,
)
from exchange_proxy import (  # noqa: E402
    ExchangeFetchSession,
    _shared_exchange_pool,
    clear_fl_source_bans,
    reset_cascade_state_for_tests,
)
from html_fetch import HtmlFetchError  # noqa: E402


class TestFlHardReset(unittest.TestCase):
    def setUp(self) -> None:
        reset_cascade_state_for_tests()
        reset_playwright_thread_for_tests()
        self._env = os.environ.copy()
        os.environ["EXCHANGE_PROXY_URLS"] = (
            "http://185.0.0.1:8000:u1:p1,"
            "http://194.0.0.2:8000:u2:p2,"
            "http://212.0.0.3:8000:u3:p3"
        )
        os.environ["FL_PROXY_URLS"] = ""
        os.environ["FL_HARD_RESET_ON_BAN"] = "1"
        os.environ["FL_SLOT_RETRY_MAX"] = "1"
        os.environ["FL_ROTATE_UA"] = "1"

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)
        reset_cascade_state_for_tests()
        reset_playwright_thread_for_tests()

    @patch("exchange_browser_fetch.fl_hard_reset")
    def test_advance_failover_fl_ban_hard_resets_no_second_slot(
        self, mock_reset: MagicMock
    ) -> None:
        urls = _shared_exchange_pool()
        session = ExchangeFetchSession(pool_key="fl", source="fl", urls=urls, slot=0)
        ok = session.advance_failover(reason="http_403", banned_url=urls[0])
        self.assertFalse(ok)
        self.assertEqual(session.slot, 0)
        mock_reset.assert_called_once()
        self.assertEqual(mock_reset.call_args.kwargs.get("reason"), "http_403")

    @patch("exchange_browser_fetch.fl_hard_reset")
    def test_advance_failover_fl_res_hard_resets_skips_ban(
        self, mock_reset: MagicMock
    ) -> None:
        urls = ["http://212.0.0.3:8000:u3:p3"]
        session = ExchangeFetchSession(
            pool_key="fl", source="fl_res", urls=urls, slot=0
        )
        ok = session.advance_failover(reason="timeout", banned_url=urls[0])
        self.assertFalse(ok)
        mock_reset.assert_called_once()

    @patch("exchange_browser_fetch.fetch_listing_html_browser")
    @patch("exchange_browser_fetch.exchange_alive_proxy_urls")
    def test_browser_slots_one_attempt_on_antibot(
        self, mock_alive: MagicMock, mock_fetch: MagicMock
    ) -> None:
        proxy_a = "http://185.0.0.1:8000:u1:p1"
        proxy_b = "http://194.0.0.2:8000:u2:p2"
        mock_alive.return_value = [proxy_a, proxy_b]
        mock_fetch.side_effect = HtmlFetchError("FL listing без карточек ленты")

        with patch("exchange_browser_fetch.fl_hard_reset") as mock_reset:
            with self.assertRaises(HtmlFetchError):
                fetch_listing_html_browser_slots(
                    "fl",
                    "https://www.fl.ru/projects/",
                    user_agent="Mozilla/5.0 (compatible; FLRadar/1.0)",
                    timeout_sec=30.0,
                )

        self.assertEqual(mock_fetch.call_count, 1)
        mock_reset.assert_called_once()

    def test_fl_listing_user_agent_rotates_when_enabled(self) -> None:
        os.environ["FL_ROTATE_UA"] = "1"
        ua = fl_listing_user_agent("Mozilla/5.0 (compatible; FLRadar/1.0)")
        self.assertNotIn("flradar", ua.casefold())

    def test_fl_hard_reset_wipes_fl_profiles(self) -> None:
        profile_root = Path(tempfile.mkdtemp())
        (profile_root / "fl_1_2_3_4").mkdir()
        (profile_root / "kwork_9_9_9").mkdir()
        with patch("exchange_browser_fetch._data_root", return_value=profile_root):
            with patch("exchange_browser_fetch.close_all_browser_contexts"):
                with patch("exchange_browser_fetch._abort_playwright_worker"):
                    with patch("exchange_proxy.clear_fl_source_bans", return_value=0):
                        fl_hard_reset(reason="test")

    def test_clear_fl_source_bans_drops_fl_keys(self) -> None:
        import exchange_proxy as ex

        reset_cascade_state_for_tests()
        ex._banned_until.clear()
        ex._ban_meta.clear()
        ex._banned_until["fl:1.2.3.4:8000"] = time.time() + 3600
        ex._ban_meta["fl:1.2.3.4:8000"] = {"reason": "test"}
        ex._banned_until["kwork:9.9.9.9:8000"] = time.time() + 3600
        ex._ban_meta["kwork:9.9.9.9:8000"] = {"reason": "test"}
        ex._persistence_loaded = True
        with patch.object(ex, "_persist_bans"):
            n = clear_fl_source_bans()
        self.assertEqual(n, 1)
        self.assertNotIn("fl:1.2.3.4:8000", ex._banned_until)
        self.assertIn("kwork:9.9.9.9:8000", ex._banned_until)

    def test_fl_hard_reset_sets_restart_flag(self) -> None:
        storage = MagicMock()
        with patch("exchange_browser_fetch.close_all_browser_contexts"):
            with patch("exchange_browser_fetch._abort_playwright_worker"):
                with patch("exchange_browser_fetch._wipe_fl_profile_dirs", return_value=0):
                    with patch(
                        "exchange_proxy.clear_fl_source_bans",
                        return_value=2,
                    ):
                        fl_hard_reset(reason="ban", storage=storage)
        storage.set_setting.assert_called_once_with("restart_source_fl", "1")


if __name__ == "__main__":
    unittest.main()
