"""O94-w3: /v1/feed today_count uses MSK calendar day."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.api_server import _feed_today_count  # noqa: E402


class _CountCursor:
    def __init__(self, count: int) -> None:
        self.last_query = ""
        self._count = count

    def execute(self, query: str, params: tuple) -> None:
        self.last_query = query
        self._params = params

    def fetchone(self) -> tuple[int]:
        return (self._count,)


class TestFeedTodayCount(unittest.TestCase):
    def test_msk_day_in_sql(self) -> None:
        cur = _CountCursor(3)
        n = _feed_today_count(cur, skills=["python"], categories=[], apply_delay=True)
        self.assertEqual(n, 3)
        self.assertIn("Europe/Moscow", cur.last_query)
        self.assertIn("COUNT(*)", cur.last_query)
        self.assertIn("make_interval(mins => %s)", cur.last_query)

    def test_category_filter_resolved_in_python(self) -> None:
        class _RowsCursor:
            last_query = ""

            def execute(self, query: str, params: tuple) -> None:
                self.last_query = query
                self._params = params

            def fetchall(self) -> list[tuple[str, str, list, str]]:
                return [
                    ("Python bot", "FastAPI", [], "dev"),
                    ("Тексты", "Копирайтинг", [], "dev"),
                ]

        cur = _RowsCursor()
        n = _feed_today_count(cur, skills=[], categories=["dev"], apply_delay=False)
        self.assertEqual(n, 1)
        self.assertNotIn("COUNT(*)", cur.last_query)
        self.assertIn("title, body, lead_tags, category", cur.last_query)


if __name__ == "__main__":
    unittest.main()
