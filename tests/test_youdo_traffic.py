"""O157: YouDo traffic savings — detail skip, fetch_every_n, warm TTL."""

from __future__ import annotations

import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from exchange_browser_fetch import (  # noqa: E402
    _maybe_warm_youdo_home,
    _should_abort_youdo_request,
    _youdo_warm_recent,
    reset_youdo_warm_state_for_tests,
)
from lead_pipeline import _resolve_ingest_body  # noqa: E402
from listing import SOURCE_YOUDO, ListingProject  # noqa: E402
from youdo_parser import (  # noqa: E402
    YOUDO_FETCH_CYCLE_KEY,
    fetch_listing_projects,
)


class TestYoudoTraffic(unittest.TestCase):
    def setUp(self) -> None:
        self._env = os.environ.copy()
        reset_youdo_warm_state_for_tests()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)
        reset_youdo_warm_state_for_tests()

    @patch("lead_pipeline.fetch_project_detail")
    def test_detail_skip_when_snippet_long_enough(self, mock_detail: MagicMock) -> None:
        os.environ["YOUDO_DETAIL_MIN_CHARS"] = "300"
        project = ListingProject(
            project_id=1,
            title="Test",
            budget_text="1000",
            url="https://youdo.com/t1",
            published_at="",
            listing_snippet="x" * 350,
            source=SOURCE_YOUDO,
        )
        cfg = MagicMock()
        errors: list[str] = []
        body, meta = _resolve_ingest_body(project, cfg, errors)
        mock_detail.assert_not_called()
        self.assertEqual(len(body), 350)
        self.assertIsNone(meta)

    @patch("lead_pipeline.fetch_project_detail")
    def test_detail_fetch_when_snippet_short(self, mock_detail: MagicMock) -> None:
        os.environ["YOUDO_DETAIL_MIN_CHARS"] = "300"
        mock_detail.return_value = ("full body text", "<html></html>", True)
        project = ListingProject(
            project_id=2,
            title="Test",
            budget_text="1000",
            url="https://youdo.com/t2",
            published_at="",
            listing_snippet="short",
            source=SOURCE_YOUDO,
        )
        cfg = MagicMock()
        body, _ = _resolve_ingest_body(project, cfg, [])
        mock_detail.assert_called_once()
        self.assertEqual(body, "full body text")

    @patch("lead_pipeline.fetch_project_detail")
    def test_detail_never_when_fetch_disabled(self, mock_detail: MagicMock) -> None:
        os.environ["YOUDO_DETAIL_FETCH"] = "0"
        project = ListingProject(
            project_id=3,
            title="Test",
            budget_text="1000",
            url="https://youdo.com/t3",
            published_at="",
            listing_snippet="short",
            source=SOURCE_YOUDO,
        )
        cfg = MagicMock()
        body, meta = _resolve_ingest_body(project, cfg, [])
        mock_detail.assert_not_called()
        self.assertEqual(body, "short")
        self.assertIsNone(meta)

    @patch("youdo_parser._fetch_listing_html")
    def test_fetch_every_n_skips_listing(self, mock_fetch: MagicMock) -> None:
        os.environ["YOUDO_FETCH_EVERY_N_CYCLES"] = "4"
        storage = MagicMock()
        storage.get_setting.side_effect = lambda key, default="": (
            "1" if key == YOUDO_FETCH_CYCLE_KEY else default
        )
        cfg = MagicMock()
        cfg.radar_log_path = Path("/tmp/radar.log")
        out = fetch_listing_projects(cfg, storage=storage)
        self.assertEqual(out, [])
        mock_fetch.assert_not_called()

    def test_youdo_lean_abort_blocks_stylesheet(self) -> None:
        req = MagicMock(resource_type="stylesheet", url="https://youdo.com/app.css")
        self.assertTrue(_should_abort_youdo_request(req))

    def test_youdo_lean_abort_allows_document(self) -> None:
        req = MagicMock(resource_type="document", url="https://youdo.com/tasks")
        self.assertFalse(_should_abort_youdo_request(req))

    def test_youdo_lean_abort_allows_youdo_xhr(self) -> None:
        req = MagicMock(resource_type="xhr", url="https://youdo.com/api/gateway/tasks")
        self.assertFalse(_should_abort_youdo_request(req))

    def test_youdo_lean_abort_blocks_external_fetch(self) -> None:
        req = MagicMock(resource_type="fetch", url="https://mc.yandex.ru/watch/123")
        self.assertTrue(_should_abort_youdo_request(req))

    @patch("exchange_browser_fetch._warm_youdo_home")
    @patch("exchange_browser_fetch._youdo_warm_recent", return_value=True)
    def test_warm_home_skip_when_recent(
        self,
        _mock_recent: MagicMock,
        mock_warm: MagicMock,
    ) -> None:
        page = MagicMock()
        _maybe_warm_youdo_home(
            page,
            "http://u:p@1.2.3.4:8000",
            "youdo_1.2.3.4:8000",
            timeout_ms=5000,
        )
        mock_warm.assert_not_called()


if __name__ == "__main__":
    unittest.main()
