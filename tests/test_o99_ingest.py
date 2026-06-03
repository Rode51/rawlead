"""O99: cycle order, 403 strikes, listing parse mocks."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from exchange_proxy import _record_failure, reset_cascade_state_for_tests
from fl_parser import parse_listing_html
from kwork_parser import parse_listing_html as parse_kwork_html


_FL_CARD = """
<div class="b-page__lenta_item">
  <div class="b-post__title"><a href="/projects/900001/test/">Title A</a></div>
  <div class="b-post__price">10 000 ₽</div>
  <div class="b-post__body"><div class="b-post__txt">Snippet text</div></div>
</div>
"""

_KWORK_WANTS = (
    '<script>window.__data = {"wants":[{"id":42,"name":"K job",'
    '"description":"desc","priceLimit":5000,"isHigherPrice":false,'
    '"date_create":"2026-06-03"}]};</script>'
)


class TestO99Ingest(unittest.TestCase):
    def setUp(self) -> None:
        reset_cascade_state_for_tests()
        self._env = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)
        reset_cascade_state_for_tests()

    def test_fl_parse_mock_html(self) -> None:
        items = parse_listing_html(_FL_CARD, "https://www.fl.ru/projects/")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].project_id, 900001)

    def test_kwork_parse_mock_html(self) -> None:
        html = f"<html><body>{_KWORK_WANTS}</body></html>"
        items = parse_kwork_html(html, "https://kwork.ru/projects")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].project_id, 42)

    def test_secondary_skip_every_n(self) -> None:
        from main import _should_fetch_secondary

        storage = MagicMock()
        storage.get_setting.return_value = "0"
        os.environ["SECONDARY_FETCH_EVERY_N_CYCLES"] = "2"
        self.assertTrue(_should_fetch_secondary(storage))
        storage.get_setting.return_value = "1"
        self.assertFalse(_should_fetch_secondary(storage))

    @patch("main._tg_poll_if_due")
    @patch("main.record_cycle_summary")
    @patch("main.commit_site_rollup_cycle")
    @patch("main.begin_site_rollup_cycle")
    @patch("main.drain_tools_backlog", return_value=0)
    @patch("main.drain_l1_backlog", return_value=0)
    @patch("main._maybe_run_feed_retention_batch")
    @patch("main._maybe_run_delist_batch")
    @patch("main.public_feed_sources", return_value=["fl"])
    @patch("main.fetch_listing_projects")
    @patch("main.L1Pool")
    def test_hot_l1_drain_before_secondary(
        self,
        mock_pool_cls: MagicMock,
        mock_fetch_fl: MagicMock,
        *_mocks: MagicMock,
    ) -> None:
        from listing import SOURCE_FL, ListingProject
        from main import run_cycle

        cfg = MagicMock()
        cfg.radar_profile = "site"
        cfg.ai_active = True
        cfg.ai_uses_l1_l2 = True
        cfg.kwork_projects_url = ""
        cfg.l1_backlog_drain = False
        cfg.l1_max_workers = 4
        cfg.l1_batch_per_cycle = 8
        cfg.radar_log_path = Path(os.devnull)

        mock_fetch_fl.return_value = [
            ListingProject(
                project_id=1,
                title="t",
                budget_text="",
                url="https://fl.ru/projects/1/",
                published_at="",
                listing_snippet="s",
                source=SOURCE_FL,
            )
        ]

        pool = MagicMock()
        pool.drain.side_effect = [3, 0]
        mock_pool_cls.return_value = pool

        pg = MagicMock()
        pg.enabled = True

        storage = MagicMock()
        storage.get_setting.return_value = "0"
        os.environ["SECONDARY_FETCH_EVERY_N_CYCLES"] = "1"

        with patch("main.process_new_listing", return_value=(1, 0)):
            with patch("main._P1_WEB_SOURCES", (("youdo", MagicMock()),)):
                with patch("main._fetch_source") as mock_sec_fetch:
                    run_cycle(cfg, storage, MagicMock(), pg)

        self.assertGreaterEqual(pool.drain.call_count, 1)
        first_shutdown = pool.drain.call_args_list[0].kwargs.get("shutdown")
        self.assertIs(first_shutdown, False)
        mock_sec_fetch.assert_called()


if __name__ == "__main__":
    unittest.main()
