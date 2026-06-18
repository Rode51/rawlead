"""O262: YouDo map UI — click «Показать списком» before waiting for cards."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from exchange_browser_fetch import (  # noqa: E402
    _YoudoListViewResult,
    _youdo_click_list_view_if_needed,
    _youdo_click_list_view_if_needed_async,
    _youdo_wait_listing_ready,
    _youdo_wait_listing_ready_async,
    youdo_list_view_click_enabled,
)


class TestYoudoListView(unittest.TestCase):
    def setUp(self) -> None:
        self._env = os.environ.copy()
        os.environ["YOUDO_LIST_VIEW_CLICK"] = "1"

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    def test_list_view_click_default_on(self) -> None:
        os.environ.pop("YOUDO_LIST_VIEW_CLICK", None)
        self.assertTrue(youdo_list_view_click_enabled())

    def test_click_list_view_when_map_only(self) -> None:
        page = MagicMock()
        card_loc = MagicMock()
        card_loc.count.return_value = 0
        list_loc = MagicMock()
        list_loc.is_visible.return_value = True
        list_loc.inner_text.return_value = "Показать списком"
        list_loc.get_attribute.return_value = ""
        page.locator.return_value = card_loc
        page.get_by_text.return_value.first = list_loc

        clicked = _youdo_click_list_view_if_needed(page)

        self.assertTrue(clicked.clicked)
        page.get_by_text.assert_called_with("Показать списком", exact=False)
        list_loc.click.assert_called_once_with(timeout=5000)
        page.wait_for_timeout.assert_called_once_with(1500)

    def test_skip_click_when_cards_already_present(self) -> None:
        page = MagicMock()
        card_loc = MagicMock()
        card_loc.count.return_value = 3
        page.locator.return_value = card_loc

        clicked = _youdo_click_list_view_if_needed(page)

        self.assertFalse(clicked.clicked)
        page.get_by_text.assert_not_called()

    def test_wait_listing_ready_calls_list_view_click(self) -> None:
        page = MagicMock()
        card_loc = MagicMock()
        card_loc.count.side_effect = [0, 1]
        page.locator.return_value = card_loc
        page.wait_for_selector.return_value = None

        with patch(
            "exchange_browser_fetch._youdo_list_view_attempt",
            return_value=_YoudoListViewResult(
                clicked=True,
                selector="text:Показать списком",
                data_id_count=0,
            ),
        ) as mock_attempt, patch(
            "exchange_browser_fetch._youdo_post_goto_list_view_wait",
        ), patch(
            "exchange_browser_fetch._youdo_maybe_list_view_pass2",
        ):
            _youdo_wait_listing_ready(page, 30_000)

        mock_attempt.assert_called_once_with(page, pass_n=1)

    def test_wait_listing_ready_async_calls_list_view_click(self) -> None:
        async def run() -> None:
            page = AsyncMock()
            page.locator.return_value.count = AsyncMock(return_value=1)
            page.wait_for_selector = AsyncMock(return_value=None)
            page.wait_for_timeout = AsyncMock(return_value=None)

            with patch(
                "exchange_browser_fetch._youdo_list_view_attempt_async",
                new_callable=AsyncMock,
                return_value=_YoudoListViewResult(
                    clicked=True,
                    selector="text:Показать списком",
                    data_id_count=0,
                ),
            ) as mock_attempt, patch(
                "exchange_browser_fetch._youdo_post_goto_list_view_wait_async",
                new_callable=AsyncMock,
            ), patch(
                "exchange_browser_fetch._youdo_maybe_list_view_pass2_async",
                new_callable=AsyncMock,
            ):
                await _youdo_wait_listing_ready_async(page, 30_000)

            mock_attempt.assert_awaited_once_with(page, pass_n=1)

        import asyncio

        asyncio.run(run())

    def test_async_click_list_view_when_map_only(self) -> None:
        async def run() -> bool:
            page = MagicMock()
            card_loc = MagicMock()
            card_loc.count = AsyncMock(return_value=0)
            list_loc = MagicMock()
            list_loc.is_visible = AsyncMock(return_value=True)
            list_loc.click = AsyncMock(return_value=None)
            list_loc.inner_text = AsyncMock(return_value="Показать списком")
            list_loc.get_attribute = AsyncMock(return_value="")
            page.locator.return_value = card_loc
            page.get_by_text.return_value.first = list_loc
            page.wait_for_timeout = AsyncMock(return_value=None)
            return await _youdo_click_list_view_if_needed_async(page)

        import asyncio

        clicked = asyncio.run(run())
        self.assertTrue(clicked.clicked)


if __name__ == "__main__":
    unittest.main()
