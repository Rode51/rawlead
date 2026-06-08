"""O156: YouDo human path — browser-only, one slot, cooldown."""

from __future__ import annotations

import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from exchange_browser_fetch import (  # noqa: E402
    fetch_listing_html_browser_slots,
    youdo_browser_only,
    youdo_one_slot_per_cycle,
)
from exchange_proxy import reset_cascade_state_for_tests  # noqa: E402
from youdo_parser import (  # noqa: E402
    YOUDO_COOLDOWN_KEY,
    fetch_listing_projects,
    fetch_project_page_html,
    set_youdo_cooldown,
    youdo_cooldown_active,
)


class TestYoudoHuman(unittest.TestCase):
    def setUp(self) -> None:
        self._env = os.environ.copy()
        os.environ["EXCHANGE_LISTING_BROWSER"] = "1"
        os.environ["YOUDO_BROWSER_ONLY"] = "1"
        os.environ["YOUDO_ONE_SLOT_PER_CYCLE"] = "1"
        reset_cascade_state_for_tests()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)
        reset_cascade_state_for_tests()

    def test_youdo_browser_only_default_on(self) -> None:
        os.environ.pop("YOUDO_BROWSER_ONLY", None)
        self.assertTrue(youdo_browser_only())

    def test_one_slot_default_on(self) -> None:
        os.environ.pop("YOUDO_ONE_SLOT_PER_CYCLE", None)
        self.assertTrue(youdo_one_slot_per_cycle())

    @patch("youdo_parser.fetch_listing_html_browser_slots")
    def test_cooldown_skip_returns_empty(self, mock_fetch: MagicMock) -> None:
        storage = MagicMock()
        storage.get_setting.side_effect = lambda key, default="": (
            str(time.time() + 1800) if key == YOUDO_COOLDOWN_KEY else default
        )
        cfg = MagicMock()
        cfg.radar_log_path = Path("/tmp/radar.log")
        cfg.sqlite_path = Path("/tmp/projects.db")
        with patch("youdo_parser._storage_for_cfg", return_value=storage):
            out = fetch_listing_projects(cfg, storage=storage)
        self.assertEqual(out, [])
        mock_fetch.assert_not_called()

    @patch("youdo_parser.fetch_youdo_detail_html")
    def test_detail_browser_only_no_exchange_get(self, mock_detail: MagicMock) -> None:
        mock_detail.return_value = (
            '<html><body><a data-id="123" href="/t123">Task</a>'
            + "x" * 600
            + "</body></html>"
        )
        cfg = MagicMock()
        cfg.http_user_agent = "Mozilla/5.0 Chrome/122"
        with patch("youdo_parser.exchange_get") as mock_get:
            html, ok = fetch_project_page_html("https://youdo.com/t123", cfg)
        mock_get.assert_not_called()
        mock_detail.assert_called_once()
        self.assertTrue(ok)
        self.assertGreater(len(html), 500)

    @patch("exchange_browser_fetch.fetch_youdo_html_browser")
    @patch("exchange_browser_fetch.exchange_primary_proxy_url", return_value="http://u:p@1.2.3.4:8000")
    @patch("exchange_browser_fetch.exchange_alive_proxy_urls")
    def test_one_slot_uses_primary_only(
        self,
        mock_alive: MagicMock,
        _mock_primary: MagicMock,
        mock_human: MagicMock,
    ) -> None:
        mock_alive.return_value = [
            "http://u:p@1.2.3.4:8000",
            "http://u:p@5.6.7.8:8000",
        ]
        mock_human.return_value = "<html>" + "x" * 600 + "</html>"
        fetch_listing_html_browser_slots(
            "youdo",
            "https://youdo.com/tasks-all-opened-all",
            user_agent="Mozilla/5.0 Chrome/122",
        )
        mock_human.assert_called_once()
        self.assertEqual(
            mock_human.call_args.kwargs.get("proxy_url"),
            "http://u:p@1.2.3.4:8000",
        )

    def test_set_and_check_cooldown(self) -> None:
        storage = MagicMock()
        storage.get_setting.return_value = "0"
        set_youdo_cooldown(storage)
        saved = storage.set_setting.call_args[0][1]
        storage.get_setting.return_value = saved
        active, msg = youdo_cooldown_active(storage)
        self.assertTrue(active)
        self.assertIn("cooldown", msg)


if __name__ == "__main__":
    unittest.main()
