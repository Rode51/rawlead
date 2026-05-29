"""O39: dup fast path — без Neon RTT на повторных SQLite-dup."""

from __future__ import annotations

import sys
import tempfile
import time
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from lead_pipeline import ingest_with_l1  # noqa: E402
from listing import ListingProject  # noqa: E402
from listing_dedup import listing_content_hash  # noqa: E402
from pg_storage import NeonLeadLiteState  # noqa: E402
from radar_cycle_log import neon_cycle_counts, reset_neon_cycle_counters  # noqa: E402
from storage import ProjectStorage  # noqa: E402


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


class DupFastPathTest(TestCase):
    def setUp(self) -> None:
        reset_neon_cycle_counters()
        self._tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.storage = ProjectStorage(Path(self._tmpdir.name) / "test.db")

    def tearDown(self) -> None:
        self.storage = None  # type: ignore[assignment]
        self._tmpdir.cleanup()

    def test_fast_path_skips_lead_exists_when_synced(self) -> None:
        cfg = _site_cfg()
        project = _project()
        fingerprint = listing_content_hash(
            project.title, project.listing_snippet or project.title
        )
        self.storage.try_record_new(project.source, project.project_id)
        self.storage.mark_neon_dup_synced(
            project.source, project.project_id, fingerprint
        )

        word_filter = MagicMock()
        word_filter.accepts_listing.return_value = True
        pg = MagicMock()
        pg.lead_exists.return_value = True
        errors: list[str] = []

        was_new, plan = ingest_with_l1(
            project,
            self.storage,
            word_filter,
            cfg,
            errors=errors,
            pg=pg,
        )

        self.assertIsNone(plan)
        self.assertFalse(was_new)
        pg.lead_exists.assert_not_called()
        self.assertTrue(any("skip:dup_fast_skip" in e for e in errors))
        _ins, _rep, _sk, _resync, fast = neon_cycle_counts()
        self.assertEqual(fast, 1)

    def test_first_dup_still_calls_lead_exists_then_marks_synced(self) -> None:
        cfg = _site_cfg()
        project = _project()
        fingerprint = listing_content_hash(
            project.title, project.listing_snippet or project.title
        )
        self.storage.try_record_new(project.source, project.project_id)

        word_filter = MagicMock()
        word_filter.accepts_listing.return_value = True
        pg = MagicMock()
        pg.lead_exists.return_value = True
        pg.fetch_lead_lite_state.return_value = NeonLeadLiteState(
            ai_verdict="Брать",
            ai_score=85,
        )
        errors: list[str] = []

        ingest_with_l1(
            project,
            self.storage,
            word_filter,
            cfg,
            errors=errors,
            pg=pg,
        )

        pg.lead_exists.assert_called_once()
        self.assertTrue(
            self.storage.is_neon_dup_fast_path(
                project.source, project.project_id, fingerprint
            )
        )

    def test_hash_change_clears_fast_path_and_triggers_replay(self) -> None:
        cfg = _site_cfg()
        project = _project()
        old_hash = listing_content_hash(
            project.title, project.listing_snippet or project.title
        )
        self.storage.try_record_new(project.source, project.project_id)
        self.storage.mark_neon_dup_synced(
            project.source, project.project_id, old_hash
        )

        changed = _project(listing_snippet="Обновлённое описание задачи")
        new_hash = listing_content_hash(changed.title, changed.listing_snippet)

        word_filter = MagicMock()
        word_filter.accepts_listing.return_value = True
        pg = MagicMock()
        pg.lead_exists.return_value = True
        pg.fetch_lead_lite_state.return_value = None
        errors: list[str] = []

        with patch("lead_pipeline._run_l1_inline_site") as mock_l1:
            was_new, plan = ingest_with_l1(
                changed,
                self.storage,
                word_filter,
                cfg,
                errors=errors,
                pg=pg,
            )

        pg.lead_exists.assert_called()
        mock_l1.assert_called_once()
        self.assertTrue(was_new)
        self.assertIsNone(plan)
        self.assertFalse(
            self.storage.is_neon_dup_fast_path(
                changed.source, changed.project_id, new_hash
            )
        )

    def test_ninety_dupes_under_90_seconds_without_lead_exists(self) -> None:
        cfg = _site_cfg()
        word_filter = MagicMock()
        word_filter.accepts_listing.return_value = True
        pg = MagicMock()
        pg.lead_exists.side_effect = AssertionError("lead_exists must not run")

        projects: list[ListingProject] = []
        for i in range(90):
            project = _project(project_id=1000 + i, listing_snippet=f"Snippet {i}")
            fingerprint = listing_content_hash(
                project.title, project.listing_snippet or project.title
            )
            self.storage.try_record_new(project.source, project.project_id)
            self.storage.mark_neon_dup_synced(
                project.source, project.project_id, fingerprint
            )
            projects.append(project)

        reset_neon_cycle_counters()
        t0 = time.monotonic()
        for project in projects:
            errors: list[str] = []
            ingest_with_l1(
                project,
                self.storage,
                word_filter,
                cfg,
                errors=errors,
                pg=pg,
            )
        elapsed = time.monotonic() - t0

        self.assertLess(elapsed, 90.0)
        _ins, _rep, _sk, _resync, fast = neon_cycle_counts()
        self.assertEqual(fast, 90)
        pg.lead_exists.assert_not_called()


if __name__ == "__main__":
    import unittest

    unittest.main()
