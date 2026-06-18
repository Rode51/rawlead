"""O262d: YouDo list-view selector gate + pass2 on false click."""

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
    _youdo_list_view_allow_class_fallback,
    _youdo_list_view_selector_attempts,
    _youdo_maybe_list_view_pass2,
    _youdo_should_run_list_view_pass2,
    _youdo_try_list_view_click,
    _youdo_wait_listing_ready,
)


class TestYoudoListViewSelector(unittest.TestCase):
    def setUp(self) -> None:
        self._env = os.environ.copy()
        os.environ["YOUDO_LIST_VIEW_CLICK"] = "1"
        os.environ["YOUDO_LIST_VIEW_FORCE_MIN_HTML"] = "50000"
        os.environ["YOUDO_LIST_VIEW_ALLOW_CLASS_FALLBACK"] = "1"

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    def test_class_list_rejected_when_text_not_spiskom(self) -> None:
        page = MagicMock()
        class_loc = MagicMock()
        class_loc.is_visible.return_value = True
        class_loc.inner_text.return_value = "Random map link"
        class_loc.get_attribute.return_value = "/map"

        with patch(
            "exchange_browser_fetch._youdo_list_view_selector_attempts",
            return_value=[("class:list", class_loc)],
        ), patch("exchange_browser_fetch._youdo_data_id_count", return_value=0):
            result = _youdo_try_list_view_click(page, force=False)

        self.assertFalse(result.clicked)
        self.assertEqual(result.selector, "none")
        class_loc.click.assert_called_once()

    def test_text_click_verified_primary_tier(self) -> None:
        page = MagicMock()
        card_loc = MagicMock()
        card_loc.count.return_value = 0
        text_loc = MagicMock()
        text_loc.is_visible.return_value = True
        text_loc.inner_text.return_value = "Показать списком"
        text_loc.get_attribute.return_value = ""
        page.locator.return_value = card_loc
        page.get_by_text.return_value.first = text_loc
        page.get_by_role.return_value.first = MagicMock(is_visible=MagicMock(return_value=False))

        result = _youdo_try_list_view_click(page, force=False)

        self.assertTrue(result.clicked)
        self.assertEqual(result.selector, "text:Показать списком")
        self.assertEqual(result.selector_tier, "primary")
        self.assertIn("списком", result.target_snip.casefold())

    def test_pass2_when_pass1_clicked_but_no_cards(self) -> None:
        page = MagicMock()
        card_loc = MagicMock()
        card_loc.count.return_value = 0
        page.locator.return_value = card_loc
        page.content.return_value = "x" * 60_000

        pass1 = _YoudoListViewResult(
            clicked=True,
            selector="class:list",
            data_id_count=0,
            html_len=60_000,
            pass_n=1,
            selector_tier="fallback",
        )
        out: list[_YoudoListViewResult] = [pass1]

        with patch(
            "exchange_browser_fetch._youdo_list_view_attempt",
            return_value=_YoudoListViewResult(
                clicked=True,
                selector="text:Показать списком",
                data_id_count=50,
                pass_n=2,
                selector_tier="primary",
            ),
        ) as mock_attempt:
            _youdo_maybe_list_view_pass2(page, list_view_out=out)

        self.assertTrue(_youdo_should_run_list_view_pass2(page, list_view_out=out))
        mock_attempt.assert_called_once_with(page, pass_n=2)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[-1].pass_n, 2)

    def test_trace_includes_selector_tier(self) -> None:
        result = _YoudoListViewResult(
            clicked=True,
            selector="text:Показать списком",
            data_id_count=50,
            html_len=120_000,
            force=True,
            pass_n=1,
            selector_tier="primary",
            target_snip="Показать списком",
        )
        with patch("youdo_parser.log_youdo_trace_path") as mock_log:
            _log_youdo_list_view_trace(result)

        kwargs = mock_log.call_args.kwargs
        self.assertEqual(kwargs["selector_tier"], "primary")
        self.assertEqual(kwargs["target_snip"], "Показать списком")
        self.assertEqual(kwargs["html_len"], 120_000)
        self.assertEqual(kwargs["force"], 1)
        self.assertEqual(kwargs["pass"], 1)

    def test_class_fallback_disabled_by_env(self) -> None:
        os.environ["YOUDO_LIST_VIEW_ALLOW_CLASS_FALLBACK"] = "0"
        page = MagicMock()
        attempts = _youdo_list_view_selector_attempts(page)
        names = [name for name, _ in attempts]
        self.assertNotIn("class:list", names)
        self.assertFalse(_youdo_list_view_allow_class_fallback())

    def test_wait_listing_ready_early_pass2_on_false_click(self) -> None:
        page = MagicMock()
        page.wait_for_selector.return_value = None

        pass1 = _YoudoListViewResult(
            clicked=True,
            selector="class:list",
            data_id_count=0,
            html_len=80_000,
            pass_n=1,
        )

        with patch(
            "exchange_browser_fetch._youdo_post_goto_list_view_wait",
        ), patch(
            "exchange_browser_fetch._youdo_list_view_attempt",
            return_value=pass1,
        ), patch(
            "exchange_browser_fetch._youdo_maybe_list_view_pass2",
        ) as mock_pass2, patch(
            "exchange_browser_fetch._youdo_data_id_count",
            return_value=0,
        ):
            _youdo_wait_listing_ready(page, 30_000)

        mock_pass2.assert_called_once()


if __name__ == "__main__":
    unittest.main()
