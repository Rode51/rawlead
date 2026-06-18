"""O262b: YouDo list-view trace + force click when map HTML is large."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from exchange_browser_fetch import (  # noqa: E402
    _YoudoListViewClickResult,
    _YoudoListViewResult,
    _fetch_youdo_ephemeral,
    _log_youdo_list_view_trace,
    _youdo_click_list_view_if_needed,
    _youdo_list_view_attempt,
)


class TestYoudoListViewTrace(unittest.TestCase):
    def setUp(self) -> None:
        self._env = os.environ.copy()
        os.environ["YOUDO_LIST_VIEW_CLICK"] = "1"
        os.environ["YOUDO_LIST_VIEW_FORCE_MIN_HTML"] = "50000"

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    def test_click_success_logs_list_view_trace(self) -> None:
        page = MagicMock()
        card_loc = MagicMock()
        card_loc.count.return_value = 0
        list_loc = MagicMock()
        list_loc.is_visible.return_value = True
        page.locator.return_value = card_loc
        page.get_by_text.return_value.first = list_loc
        page.content.return_value = "x" * 60_000
        page.wait_for_selector.return_value = None

        with patch(
            "exchange_browser_fetch._youdo_try_list_view_click",
            return_value=_YoudoListViewClickResult(
                True, "text:Показать списком", "primary", "Показать списком"
            ),
        ), patch(
            "exchange_browser_fetch._youdo_data_id_count",
            side_effect=[0, 12],
        ), patch("exchange_browser_fetch._log_youdo_list_view_trace") as mock_trace:
            result = _youdo_click_list_view_if_needed(page)

        self.assertTrue(result.clicked)
        mock_trace.assert_called_once()
        logged = mock_trace.call_args[0][0]
        self.assertIsInstance(logged, _YoudoListViewResult)
        self.assertEqual(logged.clicked, True)
        self.assertEqual(logged.data_id_count, 12)

    def test_force_click_path_when_large_html_no_cards(self) -> None:
        page = MagicMock()
        card_loc = MagicMock()
        card_loc.count.return_value = 0
        page.locator.return_value = card_loc
        page.content.return_value = "m" * 120_000
        page.wait_for_selector.return_value = None

        with patch(
            "exchange_browser_fetch._youdo_try_list_view_click",
            return_value=_YoudoListViewClickResult(
                True, "filter:списком", "primary", "Показать списком"
            ),
        ) as mock_try, patch(
            "exchange_browser_fetch._youdo_data_id_count",
            side_effect=[0, 3],
        ), patch("exchange_browser_fetch._log_youdo_list_view_trace"):
            result = _youdo_list_view_attempt(page)

        mock_try.assert_called_once()
        self.assertTrue(mock_try.call_args.kwargs["force"])
        self.assertTrue(result.clicked)

    def test_subprocess_json_includes_list_view_clicked(self) -> None:
        with patch("exchange_browser_fetch._youdo_is_camoufox", return_value=True), patch(
            "exchange_browser_fetch.subprocess.run",
            return_value=MagicMock(
                returncode=0,
                stdout='{"html":"<html>ok</html>","list_view_clicked":true,'
                '"data_id_count":5,"list_view_selector":"text:Показать списком",'
                '"list_view_debug_path":""}',
                stderr="",
            ),
        ), patch(
            "exchange_browser_fetch._validate_youdo_html",
            return_value=None,
        ), patch("exchange_browser_fetch._log_youdo_list_view_trace") as mock_trace, patch(
            "exchange_browser_fetch._on_playwright_thread",
            return_value=True,
        ):
            html = _fetch_youdo_ephemeral(
                "https://youdo.com/tasks-all-opened-all",
                user_agent="ua",
                timeout_sec=60.0,
                proxy_url="http://proxy:8000",
                stage="listing",
            )

        self.assertIn("ok", html)
        parsed = __import__("json").loads(
            '{"html":"<html>ok</html>","list_view_clicked":true,'
            '"data_id_count":5,"list_view_selector":"text:Показать списком",'
            '"list_view_debug_path":""}'
        )
        self.assertTrue(parsed["list_view_clicked"])
        self.assertEqual(parsed["data_id_count"], 5)
        mock_trace.assert_not_called()

    def test_click_fail_saves_debug_html(self) -> None:
        page = MagicMock()
        card_loc = MagicMock()
        card_loc.count.return_value = 0
        page.locator.return_value = card_loc
        big_html = "z" * 80_000
        page.content.return_value = big_html
        page.wait_for_selector.side_effect = Exception("timeout")

        with patch(
            "exchange_browser_fetch._youdo_try_list_view_click",
            return_value=_YoudoListViewClickResult(
                True, "text:Показать списком", "primary", "Показать списком"
            ),
        ), patch(
            "exchange_browser_fetch._youdo_data_id_count",
            return_value=0,
        ), patch(
            "youdo_parser._save_listing_html_debug",
            return_value="/tmp/youdo_list_view_fail_1.html",
        ) as mock_save, patch("exchange_browser_fetch._log_youdo_list_view_trace"):
            result = _youdo_list_view_attempt(page)

        mock_save.assert_called_once()
        self.assertEqual(mock_save.call_args.kwargs["tag"], "youdo_list_view_fail")
        self.assertTrue(result.debug_path.endswith(".html"))

    def test_log_youdo_list_view_trace_calls_path(self) -> None:
        result = _YoudoListViewResult(
            clicked=True,
            selector="text:Показать списком",
            data_id_count=7,
        )
        with patch("youdo_parser.log_youdo_trace_path") as mock_log:
            _log_youdo_list_view_trace(result)

        mock_log.assert_called_once()
        self.assertEqual(mock_log.call_args[0], (None, "list_view"))
        kwargs = mock_log.call_args.kwargs
        self.assertEqual(kwargs["clicked"], 1)
        self.assertEqual(kwargs["selector"], "text:Показать списком")
        self.assertEqual(kwargs["data_id"], 7)
        self.assertEqual(kwargs["html_len"], 0)
        self.assertEqual(kwargs["force"], 0)
        self.assertEqual(kwargs["pass"], 1)


if __name__ == "__main__":
    unittest.main()
