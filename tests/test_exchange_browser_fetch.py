"""Shared Playwright instance: FL persistent + YouDo ephemeral in one radar cycle."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

import exchange_browser_fetch as ebf  # noqa: E402
from exchange_browser_fetch import (  # noqa: E402
    _DEFAULT_UA,
    _abort_heavy_route,
    _fetch_youdo_ephemeral,
    _should_abort_playwright_request,
    fetch_listing_html_browser,
    reset_browser_contexts_for_tests,
)


def _html_ok() -> str:
    return "<html><body>" + "x" * 600 + "</body></html>"


class TestExchangeBrowserFetch(unittest.TestCase):
    def tearDown(self) -> None:
        reset_browser_contexts_for_tests()
        if ebf._PLAYWRIGHT is not None:
            try:
                ebf._PLAYWRIGHT.stop()
            except Exception:
                pass
        ebf._PLAYWRIGHT = None

    @patch("exchange_browser_fetch._jitter_sleep")
    @patch("exchange_browser_fetch._playwright_proxy", return_value={"server": "http://1.2.3.4:8000"})
    def test_youdo_ephemeral_uses_shared_playwright_launch(
        self, _mock_px: MagicMock, _mock_jitter: MagicMock
    ) -> None:
        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.content.return_value = _html_ok()
        mock_ctx = MagicMock()
        mock_ctx.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_ctx
        mock_pw.chromium.launch.return_value = mock_browser

        with patch("exchange_browser_fetch._get_playwright", return_value=mock_pw) as get_pw:
            with patch("playwright.sync_api.sync_playwright") as sync_pw:
                html = _fetch_youdo_ephemeral(
                    "https://youdo.com/tasks-all-opened-all",
                    user_agent="FLRadar/bot",
                    timeout_sec=45.0,
                    proxy_url="http://u:p@1.2.3.4:8000",
                )

        get_pw.assert_called_once()
        sync_pw.assert_not_called()
        mock_pw.chromium.launch.assert_called_once_with(
            headless=True, proxy={"server": "http://1.2.3.4:8000"}
        )
        mock_browser.new_context.assert_called_once_with(user_agent=_DEFAULT_UA, locale="ru-RU")
        mock_ctx.route.assert_called_once_with("**/*", _abort_heavy_route)
        mock_browser.close.assert_called_once()
        self.assertGreater(len(html), 500)

    def test_should_abort_heavy_and_tracker(self) -> None:
        req_img = MagicMock(resource_type="image", url="https://youdo.com/x.png")
        req_doc = MagicMock(resource_type="document", url="https://youdo.com/tasks")
        req_tag = MagicMock(resource_type="script", url="https://mc.yandex.ru/metrika/tag.js")
        req_tracker = MagicMock(resource_type="xhr", url="https://youdo.com/tracker/event")
        self.assertTrue(_should_abort_playwright_request(req_img))
        self.assertFalse(_should_abort_playwright_request(req_doc))
        self.assertTrue(_should_abort_playwright_request(req_tag))
        self.assertTrue(_should_abort_playwright_request(req_tracker))

    @patch("exchange_browser_fetch._jitter_sleep")
    @patch("exchange_browser_fetch._playwright_proxy", return_value=None)
    @patch(
        "exchange_browser_fetch.exchange_primary_proxy_url",
        return_value="http://u:p@5.6.7.8:8000",
    )
    def test_fl_browser_then_youdo_one_playwright_instance(
        self,
        _mock_primary: MagicMock,
        _mock_px: MagicMock,
        _mock_jitter: MagicMock,
    ) -> None:
        mock_pw = MagicMock()
        mock_persistent = MagicMock()
        mock_page_fl = MagicMock()
        mock_page_fl.content.return_value = _html_ok()
        mock_persistent.new_page.return_value = mock_page_fl
        mock_pw.chromium.launch_persistent_context.return_value = mock_persistent

        mock_browser = MagicMock()
        mock_page_yd = MagicMock()
        mock_page_yd.content.return_value = _html_ok()
        mock_ctx = MagicMock()
        mock_ctx.new_page.return_value = mock_page_yd
        mock_browser.new_context.return_value = mock_ctx
        mock_pw.chromium.launch.return_value = mock_browser

        sync_starts: list[str] = []

        def fake_get_playwright():
            if ebf._PLAYWRIGHT is None:
                sync_starts.append("start")
                ebf._PLAYWRIGHT = mock_pw
            return ebf._PLAYWRIGHT

        profile_root = Path(tempfile.mkdtemp())
        with patch("exchange_browser_fetch._data_root", return_value=profile_root):
            with patch("exchange_browser_fetch._profile_key", return_value="fl_slot0"):
                with patch(
                    "exchange_browser_fetch._get_playwright",
                    side_effect=fake_get_playwright,
                ):
                    with patch("playwright.sync_api.sync_playwright") as sync_pw:
                        fetch_listing_html_browser(
                            "fl",
                            "https://www.fl.ru/projects/",
                            user_agent=_DEFAULT_UA,
                            timeout_sec=30.0,
                        )
                        _fetch_youdo_ephemeral(
                            "https://youdo.com/tasks-all-opened-all",
                            user_agent="FLRadar/bot",
                            timeout_sec=45.0,
                            proxy_url="http://u:p@1.2.3.4:8000",
                        )
                        sync_pw.assert_not_called()
                        self.assertEqual(sync_starts, ["start"])
                        mock_pw.chromium.launch_persistent_context.assert_called_once()
                        mock_pw.chromium.launch.assert_called_once()


if __name__ == "__main__":
    unittest.main()
