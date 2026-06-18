"""O252: TG same text, new message.id — one Neon row, dup_abort."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from lead_pipeline import _insert_neon_after_gates, ingest_with_l1  # noqa: E402
from listing import ListingProject, telegram_source  # noqa: E402
from listing_dedup import listing_content_hash  # noqa: E402
from pg_storage import NeonLeadLiteState  # noqa: E402
from radar_cycle_log import reset_neon_cycle_counters  # noqa: E402
from storage import ProjectStorage  # noqa: E402


def _tg_project(msg_id: int, *, text: str = "Тест push 228228 руб") -> ListingProject:
    return ListingProject(
        project_id=msg_id,
        title=text.split("\n", 1)[0],
        budget_text="228228 руб",
        url=f"https://t.me/c/5177575757/{msg_id}",
        published_at="",
        listing_snippet=text,
        source=telegram_source(-5177575757),
    )


class TgContentDedupO252Test(TestCase):
    def setUp(self) -> None:
        reset_neon_cycle_counters()

    def test_insert_neon_after_gates_hash_dup_aborts_without_empty_hash(self) -> None:
        first = _tg_project(101)
        second = _tg_project(102)
        fp = listing_content_hash(first.title, first.listing_snippet)
        pg = MagicMock()
        pg.lead_exists.side_effect = lambda src, eid, err: eid == "101"
        pg.record_new_lead.return_value = False
        pg.fetch_lead_lite_state.return_value = NeonLeadLiteState(
            ai_verdict="Брать",
            ai_score=80,
        )

        errors: list[str] = []
        in_neon, replay, resync, dup_abort = _insert_neon_after_gates(
            second,
            pg,
            fingerprint=fp,
            ingest_body=second.listing_snippet,
            inserted=True,
            exchange_neon=True,
            errors=errors,
            stats=None,
        )

        self.assertFalse(in_neon)
        self.assertFalse(replay)
        self.assertFalse(resync)
        self.assertTrue(dup_abort)
        pg.record_new_lead.assert_called_once()
        call_kw = pg.record_new_lead.call_args.kwargs
        self.assertEqual(call_kw.get("content_hash"), fp)
        self.assertNotEqual(call_kw.get("content_hash"), "")

    def test_ingest_second_message_same_text_one_neon_insert(self) -> None:
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

        first = _tg_project(201)
        second = _tg_project(202)
        fp = listing_content_hash(first.title, first.listing_snippet)

        tmpdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        storage = ProjectStorage(Path(tmpdir.name) / "test.db")
        word_filter = MagicMock()
        word_filter.accepts_listing.return_value = True

        pg = MagicMock()
        pg.enabled = True
        pg.lead_exists.side_effect = lambda src, eid, err: eid == "201"
        pg.record_new_lead.side_effect = lambda *a, **kw: kw.get("content_hash") == fp and str(
            a[0].project_id
        ) == "201"
        pg.fetch_lead_lite_state.return_value = NeonLeadLiteState(
            ai_verdict="Брать",
            ai_score=85,
        )

        errors: list[str] = []
        was_new, plan = ingest_with_l1(
            second,
            storage,
            word_filter,
            cfg,
            errors=errors,
            pg=pg,
        )

        self.assertIsNone(plan)
        self.assertTrue(any("skip:neon_dup_skip" in e for e in errors))
        self.assertEqual(pg.record_new_lead.call_count, 1)
        tmpdir.cleanup()


if __name__ == "__main__":
    import unittest

    unittest.main()
