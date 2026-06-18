"""O262i: YouDo DC_SLOTS=0, cycle wall ≥900, ingest after parse."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from exchange_proxy import (  # noqa: E402
    _youdo_dc_pool,
    _youdo_dc_slot_count,
    reset_cascade_state_for_tests,
    youdo_dc_pool_size,
)
from listing import ListingProject  # noqa: E402
from main import _radar_cycle_wall_sec, run_cycle  # noqa: E402
from public_feed import public_feed_sources  # noqa: E402


def _fake_youdo_projects(n: int = 50) -> list[ListingProject]:
    return [
        ListingProject(
            project_id=900_000 + i,
            title=f"YouDo task {i}",
            budget_text="1000 ₽",
            url=f"https://youdo.com/t{i}",
            published_at="2026-06-17",
            source="youdo",
        )
        for i in range(n)
    ]


class TestO262iDcSlotsZero(unittest.TestCase):
    def setUp(self) -> None:
        self._env = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)
        reset_cascade_state_for_tests()

    def test_dc_slot_count_allows_zero(self) -> None:
        os.environ["YOUDO_O191_DC_SLOTS"] = "0"
        self.assertEqual(_youdo_dc_slot_count(), 0)

    def test_dc_pool_empty_when_slots_zero(self) -> None:
        os.environ["YOUDO_O191_DC_SLOTS"] = "0"
        os.environ["YOUDO_PROXY_URLS"] = (
            "http://185.147.131.15:8000:u1:p1,"
            "http://gate.node-proxy.com:10000:ru1:rp1"
        )
        reset_cascade_state_for_tests()
        self.assertEqual(_youdo_dc_pool(), [])
        self.assertEqual(youdo_dc_pool_size(), 0)


class TestO262iCycleWall(unittest.TestCase):
    def setUp(self) -> None:
        self._env = os.environ.copy()
        public_feed_sources.cache_clear()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)
        public_feed_sources.cache_clear()

    def test_cycle_wall_at_least_900_when_youdo_enabled(self) -> None:
        os.environ["RADAR_CYCLE_WALL_SEC"] = "600"
        os.environ["PUBLIC_FEED_SOURCES"] = "fl,kwork,youdo"
        public_feed_sources.cache_clear()
        self.assertGreaterEqual(_radar_cycle_wall_sec(), 900.0)

    def test_cycle_wall_respects_higher_env_when_youdo_enabled(self) -> None:
        os.environ["RADAR_CYCLE_WALL_SEC"] = "1200"
        os.environ["PUBLIC_FEED_SOURCES"] = "fl,youdo"
        public_feed_sources.cache_clear()
        self.assertEqual(_radar_cycle_wall_sec(), 1200.0)

    def test_cycle_wall_default_when_youdo_disabled(self) -> None:
        os.environ["RADAR_CYCLE_WALL_SEC"] = "600"
        os.environ["PUBLIC_FEED_SOURCES"] = "fl,kwork"
        public_feed_sources.cache_clear()
        self.assertEqual(_radar_cycle_wall_sec(), 600.0)


class TestO262iIngestAfterParse(unittest.TestCase):
    def setUp(self) -> None:
        self._env = os.environ.copy()
        public_feed_sources.cache_clear()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)
        public_feed_sources.cache_clear()

    @patch("exchange_browser_fetch.close_all_browser_contexts")
    @patch("exchange_browser_fetch.cleanup_stale_browser_processes")
    @patch("main._maybe_log_site_rollup")
    @patch("main._log_cycle_health_lines")
    @patch("healthchecks.ping_after_site_cycle")
    @patch("main.record_cycle_summary")
    @patch("main.commit_site_rollup_cycle")
    @patch("main.begin_site_rollup_cycle")
    @patch("main.drain_tools_backlog", return_value=0)
    @patch("main.drain_l1_backlog", return_value=0)
    @patch("main._maybe_run_feed_retention_batch")
    @patch("main._maybe_run_delist_batch")
    @patch("main._maybe_run_trial_maintenance")
    @patch("main._record_source_health")
    @patch("main._commit_youdo_fetch_gate")
    @patch("main._tg_poll_if_due")
    @patch("main.fetch_listing_projects", return_value=[])
    @patch("main.public_feed_sources", return_value=frozenset({"fl", "youdo"}))
    @patch("main._process_listings", return_value=(3, 0))
    @patch("main._fetch_source")
    @patch("main.L1Pool")
    def test_youdo_parse_runs_ingest_and_logs_done(
        self,
        _pool: MagicMock,
        mock_fetch_source: MagicMock,
        mock_process: MagicMock,
        _feed_sources: MagicMock,
        *_mocks: MagicMock,
    ) -> None:
        os.environ["SECONDARY_FETCH_EVERY_N_CYCLES"] = "1"
        os.environ["PUBLIC_FEED_SOURCES"] = "fl,youdo"
        os.environ["RADAR_CYCLE_WALL_SEC"] = "600"
        projects = _fake_youdo_projects(50)

        def _fetch_side_effect(
            label: str,
            _fetch_fn: object,
            _cfg: object,
            _errors: list[str],
            stats: MagicMock,
            storage: object | None = None,
        ) -> list[ListingProject] | None:
            if label == "fl":
                return []
            if label == "youdo":
                stats.fetch_error = ""
                return projects
            return None

        mock_fetch_source.side_effect = _fetch_side_effect

        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "radar_site.log"
            cfg = MagicMock(
                radar_profile="site",
                radar_log_path=log_path,
                kwork_projects_url="",
                ai_active=False,
                ai_uses_l1_l2=False,
                l1_backlog_drain=False,
            )
            storage = MagicMock()
            storage.is_radar_paused.return_value = False
            storage.get_setting.side_effect = lambda k, d="": d

            run_cycle(cfg, storage, MagicMock(), pg=None)

            mock_process.assert_called()
            youdo_call = mock_process.call_args_list[-1]
            self.assertEqual(youdo_call[0][0], projects)
            log_text = log_path.read_text(encoding="utf-8")
            self.assertIn("youdo:ingest done=50 new=3", log_text)


if __name__ == "__main__":
    unittest.main()
