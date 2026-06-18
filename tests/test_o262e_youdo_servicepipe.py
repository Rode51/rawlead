"""O262e: ServicePipe challenge detect + wait before list-view (Mechanic)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from exchange_browser_fetch import (  # noqa: E402
    _validate_youdo_html,
    _youdo_html_is_servicepipe,
    _youdo_post_goto_list_view_wait,
    _youdo_wait_servicepipe_clear,
)
from html_fetch import HtmlFetchError  # noqa: E402

_SERVICEPIPE_HTML = """<!DOCTYPE html><html><head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<noscript><meta http-equiv="refresh" content="0; url=/exhkqyad"></noscript>
<style>.spinner{background:url('//servicepipe.ru/loaders/default.gif');}</style>
</head><body><div class="spinner"></div></body></html>"""


class TestO262eServicepipe(unittest.TestCase):
    def test_detects_prod_shell(self) -> None:
        self.assertTrue(_youdo_html_is_servicepipe(_SERVICEPIPE_HTML))
        self.assertFalse(_youdo_html_is_servicepipe("<html>" + "x" * 5000 + "</html>"))

    def test_validate_raises_servicepipe(self) -> None:
        with self.assertRaises(HtmlFetchError) as ctx:
            _validate_youdo_html(_SERVICEPIPE_HTML, "http://1.2.3.4:8000")
        self.assertIn("ServicePipe", str(ctx.exception))

    def test_wait_clears_when_html_grows(self) -> None:
        page = MagicMock()
        page.content.side_effect = [
            _SERVICEPIPE_HTML,
            '<html><a data-id="1" href="/t123">task</a></html>',
        ]

        with patch("exchange_browser_fetch._youdo_servicepipe_wait_sec", return_value=10.0):
            self.assertTrue(_youdo_wait_servicepipe_clear(page, timeout_ms=5000))
        self.assertEqual(page.wait_for_timeout.call_count, 1)

    def test_wait_short_shell_polls(self) -> None:
        page = MagicMock()
        short = "<html>" + "x" * 1700 + "</html>"
        page.content.side_effect = [short, short, short]

        with patch("exchange_browser_fetch._youdo_servicepipe_wait_sec", return_value=4.0):
            self.assertFalse(_youdo_wait_servicepipe_clear(page, timeout_ms=4000))
        self.assertGreaterEqual(page.wait_for_timeout.call_count, 1)

        page = MagicMock()
        page.content.return_value = _SERVICEPIPE_HTML

        with patch(
            "exchange_browser_fetch._youdo_wait_servicepipe_clear",
            return_value=False,
        ):
            with self.assertRaises(HtmlFetchError) as ctx:
                _youdo_post_goto_list_view_wait(page)
        self.assertIn("ServicePipe", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
