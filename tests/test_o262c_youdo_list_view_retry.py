"""O262c: YouDo list-view wait after goto + second pass when HTML grows."""

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
    _log_youdo_list_view_trace,
    _youdo_list_view_attempt,
    _youdo_maybe_list_view_pass2,
    _youdo_post_goto_list_view_wait,
    _youdo_wait_listing_ready,
    _youdo_wait_listing_ready_async,
)


class TestYoudoListViewRetry(unittest.TestCase):
    def setUp(self) -> None:
        self._env = os.environ.copy()
        os.environ["YOUDO_LIST_VIEW_CLICK"] = "1"
        os.environ["YOUDO_LIST_VIEW_FORCE_MIN_HTML"] = "50000"

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    def test_post_goto_wait_prefers_networkidle(self) -> None:
        page = MagicMock()
        with patch("exchange_browser_fetch._youdo_wait_servicepipe_clear", return_value=True):
            _youdo_post_goto_list_view_wait(page)
        page.wait_for_load_state.assert_called_once_with("networkidle", timeout=15_000)
        page.wait_for_timeout.assert_not_called()

    def test_post_goto_wait_falls_back_to_timeout(self) -> None:
        page = MagicMock()
        page.wait_for_load_state.side_effect = Exception("busy")
        with patch("exchange_browser_fetch._youdo_wait_servicepipe_clear", return_value=True):
            _youdo_post_goto_list_view_wait(page)
        page.wait_for_timeout.assert_called_once_with(3000)

    def test_wait_listing_ready_waits_before_pass1(self) -> None:
        page = MagicMock()
        page.wait_for_selector.return_value = None

        with patch(
            "exchange_browser_fetch._youdo_post_goto_list_view_wait",
        ) as mock_wait, patch(
            "exchange_browser_fetch._youdo_list_view_attempt",
            return_value=_YoudoListViewResult(
                clicked=True,
                selector="text:Показать списком",
                data_id_count=0,
                pass_n=1,
            ),
        ) as mock_attempt, patch(
            "exchange_browser_fetch._youdo_maybe_list_view_pass2",
        ) as mock_pass2:
            _youdo_wait_listing_ready(page, 30_000)

        mock_wait.assert_called_once_with(page)
        mock_attempt.assert_called_once_with(page, pass_n=1)
        mock_pass2.assert_called_once()

    def test_pass2_when_large_html_still_no_cards(self) -> None:
        page = MagicMock()
        card_loc = MagicMock()
        card_loc.count.return_value = 0
        page.locator.return_value = card_loc
        page.content.return_value = "x" * 60_000

        out: list[_YoudoListViewResult] = []
        with patch(
            "exchange_browser_fetch._youdo_list_view_attempt",
            return_value=_YoudoListViewResult(
                clicked=False,
                selector="none",
                data_id_count=0,
                html_len=60_000,
                pass_n=2,
            ),
        ) as mock_attempt:
            from exchange_browser_fetch import _youdo_maybe_list_view_pass2

            _youdo_maybe_list_view_pass2(page, list_view_out=out)

        mock_attempt.assert_called_once_with(page, pass_n=2)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].pass_n, 2)

    def test_pass2_skipped_when_html_small(self) -> None:
        page = MagicMock()
        card_loc = MagicMock()
        card_loc.count.return_value = 0
        page.locator.return_value = card_loc
        page.content.return_value = "shell" * 200

        out: list[_YoudoListViewResult] = []
        with patch("exchange_browser_fetch._youdo_list_view_attempt") as mock_attempt:
            from exchange_browser_fetch import _youdo_maybe_list_view_pass2

            _youdo_maybe_list_view_pass2(page, list_view_out=out)

        mock_attempt.assert_not_called()
        self.assertEqual(out, [])

    def test_trace_includes_html_len_force_pass(self) -> None:
        result = _YoudoListViewResult(
            clicked=False,
            selector="none",
            data_id_count=0,
            html_len=1712,
            force=False,
            pass_n=1,
        )
        with patch("youdo_parser.log_youdo_trace_path") as mock_log:
            _log_youdo_list_view_trace(result)

        mock_log.assert_called_once()
        self.assertEqual(mock_log.call_args[0], (None, "list_view"))
        kwargs = mock_log.call_args.kwargs
        self.assertEqual(kwargs["clicked"], 0)
        self.assertEqual(kwargs["selector"], "none")
        self.assertEqual(kwargs["data_id"], 0)
        self.assertEqual(kwargs["html_len"], 1712)
        self.assertEqual(kwargs["force"], 0)
        self.assertEqual(kwargs["pass"], 1)

    def test_wait_listing_ready_async_second_pass(self) -> None:
        async def run() -> None:
            page = AsyncMock()
            page.wait_for_selector = AsyncMock(return_value=None)
            page.wait_for_timeout = AsyncMock(return_value=None)
            page.content = AsyncMock(return_value="y" * 55_000)

            with patch(
                "exchange_browser_fetch._youdo_post_goto_list_view_wait_async",
                new_callable=AsyncMock,
            ) as mock_wait, patch(
                "exchange_browser_fetch._youdo_list_view_attempt_async",
                new_callable=AsyncMock,
                return_value=_YoudoListViewResult(
                    clicked=False,
                    selector="none",
                    data_id_count=0,
                    pass_n=1,
                ),
            ) as mock_attempt, patch(
                "exchange_browser_fetch._youdo_maybe_list_view_pass2_async",
                new_callable=AsyncMock,
            ) as mock_pass2:
                await _youdo_wait_listing_ready_async(page, 30_000)

            mock_wait.assert_awaited_once_with(page)
            mock_attempt.assert_awaited_once_with(page, pass_n=1)
            mock_pass2.assert_awaited_once()

        import asyncio

        asyncio.run(run())

    def test_list_view_attempt_sets_trace_fields(self) -> None:
        page = MagicMock()
        card_loc = MagicMock()
        card_loc.count.return_value = 0
        list_loc = MagicMock()
        list_loc.is_visible.return_value = True
        page.locator.return_value = card_loc
        page.get_by_text.return_value.first = list_loc
        page.content.return_value = "m" * 80_000
        page.wait_for_selector.return_value = None

        with patch(
            "exchange_browser_fetch._youdo_try_list_view_click",
            return_value=_YoudoListViewClickResult(
                True, "text:Показать списком", "primary", "Показать списком"
            ),
        ), patch(
            "exchange_browser_fetch._youdo_data_id_count",
            side_effect=[0, 5],
        ), patch("exchange_browser_fetch._log_youdo_list_view_trace") as mock_trace:
            result = _youdo_list_view_attempt(page, pass_n=2)

        self.assertEqual(result.html_len, 80_000)
        self.assertTrue(result.force)
        self.assertEqual(result.pass_n, 2)
        logged = mock_trace.call_args[0][0]
        self.assertEqual(logged.html_len, 80_000)


if __name__ == "__main__":
    unittest.main()
