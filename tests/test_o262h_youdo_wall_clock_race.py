"""O262h: YouDo outer wall must exceed inner carousel budget; teardown on timeout."""

from __future__ import annotations

import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from exchange_browser_fetch import reset_playwright_thread_for_tests  # noqa: E402
from main import _fetch_source  # noqa: E402


class TestO262hWallBudget(unittest.TestCase):
    def setUp(self) -> None:
        self._env = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    def test_inner_wall_includes_carousel_extra(self) -> None:
        os.environ.pop("YOUDO_LISTING_TIMEOUT_SEC", None)
        os.environ["YOUDO_GOTO_TIMEOUT_SEC"] = "150"
        os.environ["YOUDO_SLOT_RETRY_ON_TIMEOUT"] = "3"
        os.environ["YOUDO_CAROUSEL_WALL_EXTRA_SEC"] = "150"
        from youdo_parser import _youdo_listing_wall_clock_sec

        self.assertGreaterEqual(_youdo_listing_wall_clock_sec(), 660.0)

    def test_outer_wall_exceeds_inner_grace(self) -> None:
        os.environ.pop("YOUDO_LISTING_TIMEOUT_SEC", None)
        os.environ["YOUDO_GOTO_TIMEOUT_SEC"] = "90"
        os.environ["YOUDO_SLOT_RETRY_ON_TIMEOUT"] = "3"
        os.environ["YOUDO_FETCH_OUTER_GRACE_SEC"] = "90"
        from youdo_parser import (
            _youdo_fetch_outer_grace_sec,
            _youdo_listing_wall_clock_sec,
            youdo_source_fetch_wall_sec,
        )

        inner = _youdo_listing_wall_clock_sec()
        outer = youdo_source_fetch_wall_sec()
        self.assertGreater(outer, inner)
        self.assertEqual(outer, inner + _youdo_fetch_outer_grace_sec())

    def test_radar_youdo_wall_uses_outer_budget(self) -> None:
        os.environ["RADAR_SOURCE_FETCH_WALL_SEC"] = "180"
        os.environ.pop("YOUDO_LISTING_TIMEOUT_SEC", None)
        os.environ["YOUDO_GOTO_TIMEOUT_SEC"] = "150"
        from main import _radar_source_fetch_wall_sec
        from youdo_parser import youdo_source_fetch_wall_sec

        self.assertEqual(_radar_source_fetch_wall_sec("youdo"), youdo_source_fetch_wall_sec())
        self.assertGreaterEqual(_radar_source_fetch_wall_sec("youdo"), 750.0)


class TestO262hWallTeardown(unittest.TestCase):
    def tearDown(self) -> None:
        reset_playwright_thread_for_tests()

    def test_youdo_wall_teardown_calls_browser_teardown(self) -> None:
        from exchange_browser_fetch import _youdo_wall_clock_teardown

        with patch("exchange_browser_fetch.youdo_browser_teardown") as mock_td:
            _youdo_wall_clock_teardown("youdo")
            mock_td.assert_called_once()

    def test_fl_wall_teardown_aborts_playwright_only(self) -> None:
        from exchange_browser_fetch import _youdo_wall_clock_teardown

        with patch("exchange_browser_fetch.youdo_browser_teardown") as mock_td:
            with patch("exchange_browser_fetch._abort_playwright_worker") as mock_abort:
                _youdo_wall_clock_teardown("fl")
                mock_td.assert_not_called()
                mock_abort.assert_called_once()


class TestO262hSourceFetchRace(unittest.TestCase):
    def setUp(self) -> None:
        self._env = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    @patch("main._radar_source_fetch_wall_sec", return_value=1.0)
    @patch("exchange_browser_fetch.youdo_browser_teardown")
    @patch("exchange_browser_fetch.close_all_browser_contexts")
    def test_youdo_source_timeout_teardown(
        self,
        _mock_close: MagicMock,
        mock_teardown: MagicMock,
        _mock_wall: MagicMock,
    ) -> None:
        def slow(_cfg: object, **_kw: object) -> list:
            time.sleep(30.0)
            return []

        cfg = MagicMock(radar_log_path=Path("/tmp/radar_o262h.log"))
        errors: list[str] = []
        stats = MagicMock(fetch_error="")

        result = _fetch_source("youdo", slow, cfg, errors, stats)
        self.assertIsNone(result)
        mock_teardown.assert_called_once()


if __name__ == "__main__":
    unittest.main()
