"""O134: ingest published_at, fresh-only listing, pipeline skip resync."""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from ingest_published_at import (  # noqa: E402
    parse_fl_published_at,
    parse_kwork_date_create,
    parse_ru_relative_published_at,
    parse_source_published_at,
)
from lead_pipeline import ingest_with_l1  # noqa: E402
from listing import ListingProject  # noqa: E402
from listing_dedup import listing_content_hash  # noqa: E402
from listing_fresh import trim_listing_at_known  # noqa: E402
from storage import ProjectStorage  # noqa: E402


class TestO134PublishedAt(TestCase):
    def test_fl_ru_relative_minutes(self) -> None:
        now = datetime(2026, 6, 8, 12, 0, 0, tzinfo=timezone.utc)
        dt = parse_ru_relative_published_at("5 минут назад", now=now)
        self.assertIsNotNone(dt)
        assert dt is not None
        self.assertEqual(int((now - dt).total_seconds()), 300)

    def test_fl_ru_relative_hours(self) -> None:
        now = datetime(2026, 6, 8, 12, 0, 0, tzinfo=timezone.utc)
        dt = parse_ru_relative_published_at("2 часа назад", now=now)
        self.assertIsNotNone(dt)
        assert dt is not None
        self.assertEqual(int((now - dt).total_seconds()), 7200)

    def test_fl_iso_passthrough(self) -> None:
        iso = parse_fl_published_at("2026-06-03T09:15:00+00:00")
        self.assertEqual(iso, "2026-06-03T09:15:00+00:00")

    def test_kwork_date_only_msk_to_utc(self) -> None:
        iso = parse_kwork_date_create("2026-06-03")
        self.assertTrue(iso.startswith("2026-06-02T21:00:00"))

    def test_kwork_unix_timestamp(self) -> None:
        ts = 1748870400
        iso = parse_kwork_date_create(ts)
        self.assertIn("2025", iso)

    def test_pg_parse_fl_source(self) -> None:
        now = datetime(2026, 6, 8, 12, 0, 0, tzinfo=timezone.utc)
        dt = parse_source_published_at("10 минут назад", source="fl", now=now)
        self.assertIsNotNone(dt)
        assert dt is not None
        self.assertAlmostEqual((now - dt).total_seconds(), 600, delta=1)


class TestO134FreshListing(TestCase):
    def test_trim_stops_at_known_id(self) -> None:
        tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        storage = ProjectStorage(Path(tmp.name) / "t.db")
        storage.try_record_new("fl", 100)
        projects = [
            ListingProject(
                project_id=102,
                title="new",
                budget_text="",
                url="https://fl.ru/projects/102/",
                published_at="",
                listing_snippet="",
                source="fl",
            ),
            ListingProject(
                project_id=100,
                title="old",
                budget_text="",
                url="https://fl.ru/projects/100/",
                published_at="",
                listing_snippet="",
                source="fl",
            ),
        ]
        kept = trim_listing_at_known(projects, storage, "fl")
        self.assertEqual([p.project_id for p in kept], [102])
        storage = None  # type: ignore[assignment]
        tmp.cleanup()

    def test_trim_pinned_known_new_below(self) -> None:
        """O139: закреплённые known сверху не блокируют fresh ниже."""
        tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        storage = ProjectStorage(Path(tmp.name) / "t.db")
        storage.try_record_new("fl", 100)
        storage.try_record_new("fl", 101)
        projects = [
            ListingProject(
                project_id=100,
                title="pinned old",
                budget_text="",
                url="https://fl.ru/projects/100/",
                published_at="",
                listing_snippet="",
                source="fl",
            ),
            ListingProject(
                project_id=101,
                title="pinned old 2",
                budget_text="",
                url="https://fl.ru/projects/101/",
                published_at="",
                listing_snippet="",
                source="fl",
            ),
            ListingProject(
                project_id=200,
                title="new below",
                budget_text="",
                url="https://fl.ru/projects/200/",
                published_at="",
                listing_snippet="",
                source="fl",
            ),
            ListingProject(
                project_id=201,
                title="new below 2",
                budget_text="",
                url="https://fl.ru/projects/201/",
                published_at="",
                listing_snippet="",
                source="fl",
            ),
        ]
        kept = trim_listing_at_known(projects, storage, "fl")
        self.assertEqual([p.project_id for p in kept], [200, 201])
        storage = None  # type: ignore[assignment]
        tmp.cleanup()


class TestO134PipelineSkipResync(TestCase):
    def test_sqlite_dup_filter_reject_skips_neon(self) -> None:
        tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        storage = ProjectStorage(Path(tmp.name) / "t.db")
        project = ListingProject(
            project_id=555,
            title="spam vacancy",
            budget_text="1000",
            url="https://kwork.ru/projects/555/view",
            published_at="2026-06-08T10:00:00+00:00",
            listing_snippet="ищем сотрудника в штат",
            source="kwork",
        )
        storage.try_record_new(project.source, project.project_id)

        cfg = MagicMock()
        cfg.radar_profile = "site"
        cfg.neon_ingest_wide = True
        cfg.filter_wide = True
        cfg.ai_active = True
        cfg.ai_uses_l1_l2 = True
        cfg.min_budget_rub = 0
        cfg.radar_log_path = Path(tmp.name) / "radar.log"
        cfg.match_push_enabled = False

        word_filter = MagicMock()
        word_filter.accepts_listing.return_value = False
        pg = MagicMock()
        pg.lead_exists.side_effect = AssertionError("lead_exists must not run")

        errors: list[str] = []
        with patch("lead_pipeline.is_public_feed_source", return_value=True):
            was_new, plan = ingest_with_l1(
                project,
                storage,
                word_filter,
                cfg,
                errors=errors,
                pg=pg,
            )
        self.assertFalse(was_new)
        self.assertIsNone(plan)
        pg.lead_exists.assert_not_called()
        self.assertTrue(any("pipeline:skip filter" in e for e in errors))
        self.assertFalse(any("neon_resync_check" in e for e in errors))
        storage = None  # type: ignore[assignment]
        tmp.cleanup()

    def test_fl_parse_listing_sets_published_at(self) -> None:
        from fl_parser import parse_listing_html

        html = """
        <div class="b-page__lenta_item">
          <div class="b-post__title"><a href="/projects/900001/t/">T</a></div>
          <span class="text-gray-opacity-4">3 минуты назад</span>
          <div class="b-post__body"><div class="b-post__txt">Body</div></div>
        </div>
        """
        items = parse_listing_html(html, "https://www.fl.ru/projects/")
        self.assertTrue(items[0].published_at.endswith("+00:00"))
        self.assertIn("T", items[0].published_at)


if __name__ == "__main__":
    import unittest

    unittest.main()
