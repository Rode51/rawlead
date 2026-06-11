"""Personal feed: sort=time shows all leads (no min_match gate)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.api_server import (  # noqa: E402
    _ME_FEED_SCAN_LIMIT,
    _feed_page_match,
    _feed_where_with_sources,
    _feed_today_subquery_sql,
    _personal_feed_page,
)

_ROW = tuple(range(15))


def _feed_row(lead_id: int) -> tuple:
    return tuple([lead_id] + list(range(1, 15)))


class TestPersonalFeedTimeSort(unittest.TestCase):
    @patch("src.api_server._row_to_item", side_effect=lambda row, **kw: {"id": row[0]})
    @patch("src.api_server.keyword_match", return_value=0)
    @patch("src.api_server._canonical_lead_tags", return_value=[])
    @patch("src.api_server._finalize_feed_items")
    @patch("src.api_server._load_user_tags", return_value={"python": 1.0})
    def test_time_sort_uses_sql_offset_not_min_match(
        self, _tags: MagicMock, _fin: MagicMock, *_rest: MagicMock
    ) -> None:
        cur = MagicMock()
        cur.fetchall.return_value = [_ROW]

        page, count, _today = _personal_feed_page(
            cur,
            "00000000-0000-0000-0000-000000000001",
            limit=20,
            offset=40,
            min_score=0,
            min_match=80,
            skills=[],
            categories=[],
            sort="time",
        )

        query = cur.execute.call_args[0][0]
        params = cur.execute.call_args[0][1]
        self.assertIn("OFFSET", query)
        self.assertEqual(params[-2:], (20, 40))
        self.assertEqual(count, len(page))

    @patch("src.api_server._passes_category_filter")
    @patch("src.api_server._row_to_item", side_effect=lambda row, **kw: {"id": row[0]})
    @patch("src.api_server.keyword_match", return_value=0)
    @patch("src.api_server._canonical_lead_tags", return_value=[])
    @patch("src.api_server._finalize_feed_items")
    @patch("src.api_server._load_user_tags", return_value={"python": 1.0})
    def test_time_sort_category_wide_scan(
        self,
        _tags: MagicMock,
        _fin: MagicMock,
        _canon: MagicMock,
        _km: MagicMock,
        _row_item: MagicMock,
        passes_cat: MagicMock,
    ) -> None:
        rows = [_feed_row(i) for i in range(35)]
        cur = MagicMock()
        cur.fetchall.return_value = rows

        def _passes(row: tuple, categories: list[str]) -> bool:
            return row[0] >= 30 and "marketing" in categories

        passes_cat.side_effect = _passes

        page, count, today = _personal_feed_page(
            cur,
            "00000000-0000-0000-0000-000000000001",
            limit=20,
            offset=0,
            min_score=0,
            min_match=80,
            skills=[],
            categories=["marketing"],
            sort="time",
        )

        query = cur.execute.call_args[0][0]
        params = cur.execute.call_args[0][1]
        self.assertNotIn("OFFSET", query)
        self.assertEqual(params[-1], _ME_FEED_SCAN_LIMIT)
        self.assertIsNone(today)
        self.assertEqual(len(page), 5)
        self.assertEqual(count, 5)
        self.assertEqual([item["id"] for item in page], [30, 31, 32, 33, 34])

    @patch("src.api_server._row_to_item", side_effect=lambda row, **kw: {"id": row[0]})
    @patch("src.api_server.keyword_match", return_value=0)
    @patch("src.api_server._canonical_lead_tags", return_value=[])
    @patch("src.api_server._finalize_feed_items")
    @patch("src.api_server._load_user_tags", return_value={"python": 1.0})
    def test_time_sort_source_filter_binds_today_params_first(
        self, _tags: MagicMock, _fin: MagicMock, *_rest: MagicMock
    ) -> None:
        cur = MagicMock()
        cur.fetchall.return_value = [_ROW]
        source_keys = ["fl", "youdo"]

        _personal_feed_page(
            cur,
            "00000000-0000-0000-0000-000000000001",
            limit=20,
            offset=0,
            min_score=0,
            min_match=0,
            skills=[],
            categories=[],
            sort="time",
            source_keys=source_keys,
        )

        params = cur.execute.call_args[0][1]
        _fw, feed_params = _feed_where_with_sources(source_keys=source_keys)
        _ts, today_params = _feed_today_subquery_sql(skills=[], apply_delay=False)
        self.assertEqual(params[: len(today_params)], tuple(today_params))
        self.assertEqual(
            params[len(today_params) : len(today_params) + len(feed_params)],
            tuple(feed_params),
        )

    @patch("src.api_server._feed_today_count_standalone_cached", return_value=0)
    @patch("src.api_server._finalize_feed_items")
    @patch("src.api_server._rank_feed_rows", return_value=[])
    @patch("src.api_server._load_user_tags", return_value={"python": 1.0})
    def test_match_sort_source_filter_binds_today_params_first(
        self, _tags: MagicMock, _rank: MagicMock, _fin: MagicMock, _today: MagicMock
    ) -> None:
        cur = MagicMock()
        cur.fetchall.return_value = []
        source_keys = ["fl"]

        _personal_feed_page(
            cur,
            "00000000-0000-0000-0000-000000000001",
            limit=20,
            offset=0,
            min_score=0,
            min_match=80,
            skills=[],
            categories=[],
            sort="match",
            source_keys=source_keys,
        )

        params = cur.execute.call_args_list[0][0][1]
        _fw, feed_params = _feed_where_with_sources(source_keys=source_keys)
        _ts, today_params = _feed_today_subquery_sql(skills=[], apply_delay=False)
        self.assertEqual(params[: len(today_params)], tuple(today_params))
        self.assertEqual(
            params[len(today_params) : len(today_params) + len(feed_params)],
            tuple(feed_params),
        )


class TestFeedPageMatchSourceFilter(unittest.TestCase):
    @patch("src.api_server._feed_today_count_standalone_cached", return_value=0)
    @patch("src.api_server._finalize_feed_items")
    @patch("src.api_server._rank_feed_rows", return_value=[])
    def test_match_page_source_filter_binds_today_params_first(
        self, _rank: MagicMock, _fin: MagicMock, _today: MagicMock
    ) -> None:
        cur = MagicMock()
        cur.fetchall.return_value = []
        source_keys = ["fl", "tg", "youdo"]

        _feed_page_match(
            cur,
            limit=20,
            offset=0,
            min_score=0,
            skills=[],
            categories=[],
            tag_weights={},
            source_keys=source_keys,
        )

        params = cur.execute.call_args_list[0][0][1]
        _fw, feed_params = _feed_where_with_sources(source_keys=source_keys)
        _ts, today_params = _feed_today_subquery_sql(skills=[], apply_delay=False)
        self.assertEqual(params[: len(today_params)], tuple(today_params))
        self.assertEqual(
            params[len(today_params) : len(today_params) + len(feed_params)],
            tuple(feed_params),
        )


if __name__ == "__main__":
    unittest.main()
