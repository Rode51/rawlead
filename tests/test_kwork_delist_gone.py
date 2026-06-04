"""O109/O65: Kwork delist — «404» в HTML не должен считать заказ снятым."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from kwork_parser import check_project_page_gone  # noqa: E402


class TestKworkDelistGone(TestCase):
    def test_html_with_404_substring_not_gone(self) -> None:
        html = (
            '<html><body class="wants-page">'
            '<div want-description>Ошибка 404 в макете — поправить</div>'
            '"want": {"id": 3190279}'
            "</body></html>"
        )
        resp = MagicMock(status_code=200, encoding="utf-8", content=html.encode())
        cfg = MagicMock(http_user_agent="test")
        with patch("kwork_parser.exchange_get", return_value=resp):
            self.assertFalse(check_project_page_gone("https://kwork.ru/projects/3190279/view", cfg))

    def test_real_gone_marker(self) -> None:
        html = "<html><body>заказ закрыт</body></html>"
        resp = MagicMock(status_code=200, encoding="utf-8", content=html.encode())
        cfg = MagicMock(http_user_agent="test")
        with patch("kwork_parser.exchange_get", return_value=resp):
            self.assertTrue(check_project_page_gone("https://kwork.ru/projects/1/view", cfg))
