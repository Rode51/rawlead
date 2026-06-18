"""O213: Kwork multi-page listing fetch."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from kwork_parser import (  # noqa: E402
    _kwork_listing_page_url,
    fetch_listing_projects,
)


def _wants_html(*ids: int, name: str = "Test") -> str:
    wants = [
        {
            "id": pid,
            "name": f"{name} {pid}",
            "description": "desc",
            "priceLimit": 1000,
            "isHigherPrice": False,
            "date_create": "2026-06-14",
        }
        for pid in ids
    ]
    import json

    return f'<html><script>var x = {{"wants":{json.dumps(wants)}}};</script></html>'


class TestKworkListingPageUrl(unittest.TestCase):
    def test_page_one_is_base(self) -> None:
        base = "https://kwork.ru/projects?c=all"
        self.assertEqual(_kwork_listing_page_url(base, 1), base)

    def test_page_two_adds_query(self) -> None:
        base = "https://kwork.ru/projects?c=all"
        self.assertEqual(
            _kwork_listing_page_url(base, 2),
            "https://kwork.ru/projects?c=all&page=2",
        )


class TestKworkMultiPageFetch(unittest.TestCase):
    @patch("kwork_parser.listing_browser_enabled", return_value=False)
    @patch("kwork_parser.exchange_get")
    @patch.dict("os.environ", {"KWORK_MAX_PAGES": "2"})
    def test_multi_page_merge_dedup_and_log(
        self, mock_get: MagicMock, _browser_off: MagicMock
    ) -> None:
        page1 = MagicMock(status_code=200, encoding="utf-8")
        page1.content = _wants_html(101, 102).encode("utf-8")
        page2 = MagicMock(status_code=200, encoding="utf-8")
        page2.content = _wants_html(102, 103).encode("utf-8")
        mock_get.side_effect = [page1, page2]

        cfg = MagicMock(
            kwork_projects_url="https://kwork.ru/projects?c=all",
            http_user_agent="FLRadar/test",
            radar_log_path=None,
        )
        with patch("kwork_parser.log_pipeline_line") as mock_log:
            projects = fetch_listing_projects(cfg, timeout_sec=30.0)
            log_lines = [c.args[1] for c in mock_log.call_args_list if len(c.args) > 1]

        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(len(projects), 3)
        self.assertEqual({p.project_id for p in projects}, {101, 102, 103})
        listing_line = next(l for l in log_lines if l.startswith("listing:kwork"))
        self.assertIn("parsed=3", listing_line)
        self.assertIn("pages=2", listing_line)


if __name__ == "__main__":
    unittest.main()
