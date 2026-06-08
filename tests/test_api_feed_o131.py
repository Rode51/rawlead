"""O131-PERF: feed scan limit + today_count inline + db mode helper."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.api_server import (  # noqa: E402
    _ME_FEED_SCAN_LIMIT,
    _db_connection_mode,
    _feed_page_time,
    _feed_scan_limit,
    _feed_today_subquery_sql,
)


class TestFeedScanLimit(unittest.TestCase):
    def test_time_sort_no_filters_uses_small_buffer(self) -> None:
        n = _feed_scan_limit(
            limit=20,
            offset=0,
            categories=[],
            skills=[],
            sort="time",
        )
        self.assertEqual(n, 40)

    def test_categories_use_wide_scan(self) -> None:
        n = _feed_scan_limit(
            limit=20,
            offset=0,
            categories=["dev"],
            skills=[],
            sort="time",
        )
        self.assertEqual(n, _ME_FEED_SCAN_LIMIT)

    def test_match_with_skills_uses_wide_scan(self) -> None:
        n = _feed_scan_limit(
            limit=20,
            offset=0,
            categories=[],
            skills=["python"],
            sort="match",
        )
        self.assertEqual(n, _ME_FEED_SCAN_LIMIT)


class TestFeedTodaySubquery(unittest.TestCase):
    def test_subquery_embeds_msk_day(self) -> None:
        sql, _params = _feed_today_subquery_sql(skills=[], apply_delay=True)
        self.assertIn("COUNT(*)", sql)
        self.assertIn("Europe/Moscow", sql)


class TestFeedPageTimeInlineToday(unittest.TestCase):
    def test_single_execute_includes_today_count(self) -> None:
        cur = MagicMock()
        row = tuple(range(15)) + (7,)
        cur.fetchall.return_value = [row]

        page, count, today = _feed_page_time(
            cur,
            limit=20,
            offset=0,
            min_score=0,
            skills=[],
            categories=[],
            tag_weights={},
            apply_delay=True,
        )

        self.assertEqual(today, 7)
        self.assertEqual(count, len(page))
        self.assertEqual(cur.execute.call_count, 1)
        query = cur.execute.call_args[0][0]
        self.assertIn("_today_count", query)


class TestDbConnectionMode(unittest.TestCase):
    def test_pooler_host(self) -> None:
        self.assertEqual(
            _db_connection_mode(),
            "direct",
        )

    def test_pooler_detection(self) -> None:
        import os

        old = os.environ.get("DATABASE_URL")
        try:
            os.environ["DATABASE_URL"] = "postgresql://u:p@ep-foo-pooler.eu-west.aws.neon.tech/db"
            self.assertEqual(_db_connection_mode(), "pooler")
            os.environ["DATABASE_URL"] = "postgresql://u:p@host:6543/db"
            self.assertEqual(_db_connection_mode(), "pooler")
        finally:
            if old is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = old


if __name__ == "__main__":
    unittest.main()
