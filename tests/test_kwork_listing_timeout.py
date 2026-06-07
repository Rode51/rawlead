"""O117: Kwork Playwright wall-clock timeout → httpx fallback."""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

import exchange_browser_fetch as ebf  # noqa: E402
from exchange_browser_fetch import (  # noqa: E402
    fetch_listing_html_browser_wall_clock,
    reset_browser_contexts_for_tests,
)
from html_fetch import HtmlFetchError  # noqa: E402
from kwork_parser import fetch_listing_projects  # noqa: E402

_WANTS_HTML = (
    '<html><script>var x = {"wants":[{"id":42,"name":"Test","description":"d",'
    '"priceLimit":1000,"isHigherPrice":false,"date_create":"2026-01-01"}]};</script></html>'
)


class TestKworkListingWallClock(unittest.TestCase):
    def tearDown(self) -> None:
        reset_browser_contexts_for_tests()
        if ebf._PLAYWRIGHT is not None:
            try:
                ebf._PLAYWRIGHT.stop()
            except Exception:
                pass
        ebf._PLAYWRIGHT = None

    @patch("exchange_browser_fetch.fetch_listing_html_browser")
    def test_wall_clock_raises_before_hang_completes(self, mock_fetch: MagicMock) -> None:
        def slow(*_args: object, **_kwargs: object) -> str:
            time.sleep(3.0)
            return "x" * 600

        mock_fetch.side_effect = slow
        started = time.monotonic()
        with self.assertRaises(HtmlFetchError) as ctx:
            fetch_listing_html_browser_wall_clock(
                "kwork",
                "https://kwork.ru/projects",
                user_agent="test",
                wall_clock_sec=0.5,
            )
        elapsed = time.monotonic() - started
        self.assertIn("timeout", str(ctx.exception).lower())
        self.assertLess(elapsed, 2.5)

    @patch("kwork_parser.exchange_get")
    @patch("kwork_parser.fetch_listing_html_browser_wall_clock")
    @patch("kwork_parser.listing_browser_enabled", return_value=True)
    def test_playwright_timeout_falls_back_to_httpx(
        self,
        _browser_on: MagicMock,
        mock_wall: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        mock_wall.side_effect = HtmlFetchError("wall-clock timeout after 2s (kwork)")
        resp = MagicMock(status_code=200, encoding="utf-8")
        resp.content = _WANTS_HTML.encode("utf-8")
        mock_get.return_value = resp
        cfg = MagicMock(
            kwork_projects_url="https://kwork.ru/projects?c=41",
            http_user_agent="FLRadar/test",
            radar_log_path=None,
        )
        projects = fetch_listing_projects(cfg, timeout_sec=30.0)
        mock_get.assert_called_once()
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0].project_id, 42)


if __name__ == "__main__":
    unittest.main()
