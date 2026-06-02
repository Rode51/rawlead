"""O34: filter→Neon→parallel L1."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from lead_pipeline import ingest_with_l1  # noqa: E402
from listing import ListingProject  # noqa: E402


def _site_cfg() -> MagicMock:
    cfg = MagicMock()
    cfg.radar_profile = "site"
    cfg.neon_ingest_wide = True
    cfg.filter_wide = True
    cfg.ai_active = True
    cfg.ai_uses_l1_l2 = True
    cfg.min_budget_rub = 0
    cfg.radar_log_path = Path(_ROOT / "data" / "test_pipeline.log")
    cfg.l1_max_workers = 2
    cfg.match_push_enabled = False
    return cfg


def _project(**kw) -> ListingProject:
    defaults = dict(
        project_id=123,
        title="Разработка бота Telegram",
        budget_text="50000 руб",
        url="https://kwork.ru/projects/123",
        published_at="",
        listing_snippet="Нужен бот на Python",
        source="kwork",
    )
    defaults.update(kw)
    return ListingProject(**defaults)


class FilterBeforeNeonTest(TestCase):
    def test_filter_rejects_before_neon_insert(self) -> None:
        cfg = _site_cfg()
        storage = MagicMock()
        storage.try_record_new.return_value = True
        storage.try_record_content_fingerprint.return_value = True
        word_filter = MagicMock()
        word_filter.accepts_listing.return_value = False
        pg = MagicMock()
        pg.lead_exists.return_value = False
        errors: list[str] = []

        was_new, plan = ingest_with_l1(
            _project(),
            storage,
            word_filter,
            cfg,
            errors=errors,
            pg=pg,
        )

        self.assertIsNone(plan)
        pg.record_new_lead.assert_not_called()
        self.assertTrue(any("pipeline:skip filter" in e for e in errors))


class L1PoolTest(TestCase):
    @patch("l1_pool.analyze_lite")
    def test_pool_runs_multiple_workers(self, mock_lite) -> None:
        from ai_analyze import AiLiteAnalysis
        from l1_pool import L1Pool
        from pg_storage import NeonLeadStorage

        delays: list[float] = []

        def _slow_lite(*args, **kwargs):
            delays.append(time.monotonic())
            time.sleep(0.05)
            return AiLiteAnalysis(
                feed_visible=True,
                task_summary="test",
                lead_tags=("python",),
                ai_reasons=(),
                pending_tags=(),
            )

        mock_lite.side_effect = _slow_lite

        cfg = _site_cfg()
        cfg.l1_max_workers = 2
        pg = MagicMock(spec=NeonLeadStorage)
        pg.enabled = True
        pg.update_after_lite = MagicMock()
        pg.fetch_lead_id = MagicMock(return_value=1)
        errors: list[str] = []

        pool = L1Pool(cfg, pg, errors=errors)
        for i in range(3):
            pool.submit(
                _project(project_id=100 + i),
                ingest_snippet="snippet",
            )
        t0 = time.monotonic()
        done = pool.drain()
        elapsed = time.monotonic() - t0

        self.assertEqual(done, 3)
        self.assertEqual(mock_lite.call_count, 3)
        self.assertLess(elapsed, 0.14)
        self.assertGreaterEqual(elapsed, 0.04)


class L1FailedTest(TestCase):
    @patch("l1_pool.analyze_lite", return_value=None)
    def test_ai_fail_marks_l1_failed(self, _mock_lite) -> None:
        from l1_pool import L1Pool

        cfg = _site_cfg()
        pg = MagicMock()
        pg.enabled = True
        pg.mark_l1_failed = MagicMock()
        pg.update_after_lite = MagicMock()
        errors: list[str] = []

        pool = L1Pool(cfg, pg, errors=errors)
        pool.submit(_project(), ingest_snippet="body")
        pool.drain()

        pg.mark_l1_failed.assert_called_once()
        pg.update_after_lite.assert_not_called()
        self.assertTrue(any("l1_failed" in e for e in errors))


if __name__ == "__main__":
    import unittest

    unittest.main()
