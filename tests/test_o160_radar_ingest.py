"""O160: FL hang must not block cycle — per-source lock + source wall-clock."""

from __future__ import annotations

import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

import exchange_browser_fetch as ebf  # noqa: E402
from exchange_browser_fetch import (  # noqa: E402
    _fetch_lock,
    fetch_listing_html_browser_wall_clock,
    reset_browser_contexts_for_tests,
)
from html_fetch import HtmlFetchError  # noqa: E402
from main import _fetch_source, run_cycle  # noqa: E402


class TestO160PerSourceLocks(unittest.TestCase):
    def tearDown(self) -> None:
        reset_browser_contexts_for_tests()
        if ebf._PLAYWRIGHT is not None:
            try:
                ebf._PLAYWRIGHT.stop()
            except Exception:
                pass
        ebf._PLAYWRIGHT = None

    def test_fl_and_kwork_use_different_locks(self) -> None:
        self.assertIsNot(_fetch_lock("fl"), _fetch_lock("kwork"))

    @patch("exchange_browser_fetch.fetch_listing_html_browser")
    def test_wall_clock_raises_before_hang_completes(self, mock_fetch: MagicMock) -> None:
        def slow(*_args: object, **_kwargs: object) -> str:
            time.sleep(3.0)
            return "x" * 600

        mock_fetch.side_effect = slow
        started = time.monotonic()
        with self.assertRaises(HtmlFetchError):
            fetch_listing_html_browser_wall_clock(
                "fl",
                "https://www.fl.ru/projects/",
                user_agent="test",
                wall_clock_sec=0.5,
            )
        self.assertLess(time.monotonic() - started, 2.5)


class TestO160SourceFetchWallClock(unittest.TestCase):
    def setUp(self) -> None:
        self._env = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    @patch("exchange_browser_fetch.close_all_browser_contexts")
    def test_slow_fl_times_out_kwork_still_runs(self, _mock_close: MagicMock) -> None:
        os.environ["RADAR_SOURCE_FETCH_WALL_SEC"] = "2"
        os.environ["SECONDARY_FETCH_EVERY_N_CYCLES"] = "99"

        def slow_fl(_cfg: object, **_kw: object) -> list:
            time.sleep(30.0)
            return []

        def fast_kwork(_cfg: object, **_kw: object) -> list:
            return []

        cfg = MagicMock(radar_log_path=Path("/tmp/radar_test.log"))
        errors: list[str] = []
        stats_fl = MagicMock(fetch_error="")
        stats_kwork = MagicMock(fetch_error="")

        started = time.monotonic()
        fl_result = _fetch_source("fl", slow_fl, cfg, errors, stats_fl)
        elapsed_fl = time.monotonic() - started
        kwork_result = _fetch_source("kwork", fast_kwork, cfg, errors, stats_kwork)
        total = time.monotonic() - started

        self.assertIsNone(fl_result)
        self.assertEqual(kwork_result, [])
        self.assertLess(elapsed_fl, 5.0)
        self.assertLess(total, 8.0)
        self.assertTrue(any("fl:fetch:" in e for e in errors))


class TestO160CycleHangKworkRuns(unittest.TestCase):
    def setUp(self) -> None:
        self._env = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

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
    @patch("main._tg_poll_if_due")
    @patch("main.public_feed_sources", return_value=["fl", "kwork"])
    @patch("main.fetch_kwork_listing_projects")
    @patch("main.fetch_listing_projects")
    @patch("main.L1Pool")
    def test_fl_hang_cycle_completes_with_kwork(
        self,
        _pool: MagicMock,
        mock_fetch_fl: MagicMock,
        mock_fetch_kwork: MagicMock,
        *_mocks: MagicMock,
    ) -> None:
        os.environ["RADAR_SOURCE_FETCH_WALL_SEC"] = "2"
        os.environ["SECONDARY_FETCH_EVERY_N_CYCLES"] = "99"

        def slow_fl(*_a: object, **_k: object) -> list:
            time.sleep(60.0)
            return []

        mock_fetch_fl.side_effect = slow_fl
        mock_fetch_kwork.return_value = []

        cfg = MagicMock(
            radar_profile="site",
            radar_log_path=Path("/tmp/radar_o160.log"),
            kwork_projects_url="https://kwork.ru/projects",
            ai_active=False,
            ai_uses_l1_l2=False,
            l1_backlog_drain=False,
        )
        storage = MagicMock()
        storage.is_radar_paused.return_value = False

        started = time.monotonic()
        run_cycle(cfg, storage, MagicMock(), pg=None)
        elapsed = time.monotonic() - started

        mock_fetch_kwork.assert_called_once()
        self.assertLess(elapsed, 180.0)


if __name__ == "__main__":
    unittest.main()
