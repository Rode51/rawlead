"""O48: on-demand draft reliability helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.ai_analyze import (  # noqa: E402
    AiAnalyzeError,
    AiLiteAnalysis,
    analyze_premium,
    draft_stats_24h,
    note_draft_request,
)
from src.draft_limits import draft_hourly_limit  # noqa: E402
from src.match_push import (  # noqa: E402
    draft_quota_for_user,
    draft_rate_limit_retry_after,
    reset_draft_quota_for_user,
)


class TestDraftStats(unittest.TestCase):
    def test_draft_stats_24h(self) -> None:
        while draft_stats_24h()["draft_ok"] or draft_stats_24h()["draft_fail"]:
            note_draft_request(False)
        note_draft_request(True)
        note_draft_request(False)
        stats = draft_stats_24h()
        self.assertEqual(stats["draft_ok"], 1)
        self.assertEqual(stats["draft_fail"], 1)


class TestDraftRateLimit(unittest.TestCase):
    def test_default_limit_ten(self) -> None:
        import os

        old = os.environ.pop("DRAFT_HOURLY_LIMIT", None)
        try:
            from importlib import reload

            import src.draft_limits as dl

            reload(dl)
            self.assertEqual(dl.draft_hourly_limit(), 10)
            self.assertIn("10", dl.draft_rate_limit_detail())
        finally:
            if old is not None:
                os.environ["DRAFT_HOURLY_LIMIT"] = old

    def test_zero_disables_limit(self) -> None:
        import os

        os.environ["DRAFT_HOURLY_LIMIT"] = "0"
        from importlib import reload

        import src.draft_limits as dl

        reload(dl)
        self.assertEqual(dl.draft_hourly_limit(), 0)
        self.assertEqual(dl.draft_rate_limit_detail(), "")
        uid = "00000000-0000-0000-0000-000000000010"
        for _ in range(20):
            self.assertIsNone(draft_rate_limit_retry_after(uid))
        os.environ.pop("DRAFT_HOURLY_LIMIT", None)
        reload(dl)

    def test_rate_limit_blocks_when_configured(self) -> None:
        import os

        os.environ["DRAFT_HOURLY_LIMIT"] = "10"
        from importlib import reload

        import src.draft_limits as dl

        reload(dl)
        self.assertEqual(draft_hourly_limit(), 10)
        uid = "00000000-0000-0000-0000-000000000099"
        for _ in range(10):
            self.assertIsNone(draft_rate_limit_retry_after(uid))
        retry = draft_rate_limit_retry_after(uid)
        self.assertIsNotNone(retry)
        self.assertGreater(retry, 0)
        os.environ.pop("DRAFT_HOURLY_LIMIT", None)
        reload(dl)


class TestDraftQuota(unittest.TestCase):
    def test_quota_tracks_used_and_remaining(self) -> None:
        import os
        from importlib import reload

        import src.draft_limits as dl
        import src.match_push as mp

        os.environ["DRAFT_HOURLY_LIMIT"] = "10"
        reload(dl)
        reload(mp)
        uid = "00000000-0000-0000-0000-000000000088"
        mp._draft_attempts.pop(uid, None)
        self.assertEqual(draft_quota_for_user(uid)["draft_remaining"], 10)
        for _ in range(9):
            self.assertIsNone(draft_rate_limit_retry_after(uid))
        quota = draft_quota_for_user(uid)
        self.assertEqual(quota["draft_used"], 9)
        self.assertEqual(quota["draft_remaining"], 1)
        self.assertIsNone(draft_rate_limit_retry_after(uid))
        quota = draft_quota_for_user(uid)
        self.assertEqual(quota["draft_used"], 10)
        self.assertEqual(quota["draft_remaining"], 0)
        self.assertGreater(quota["draft_retry_after_sec"], 0)
        self.assertIsNotNone(draft_rate_limit_retry_after(uid))
        os.environ.pop("DRAFT_HOURLY_LIMIT", None)
        reload(dl)
        reload(mp)

    def test_reset_clears_quota(self) -> None:
        import os
        from importlib import reload

        import src.draft_limits as dl
        import src.match_push as mp

        os.environ["DRAFT_HOURLY_LIMIT"] = "10"
        reload(dl)
        reload(mp)
        uid = "00000000-0000-0000-0000-000000000077"
        mp._draft_attempts.pop(uid, None)
        for _ in range(10):
            self.assertIsNone(draft_rate_limit_retry_after(uid))
        self.assertEqual(draft_quota_for_user(uid)["draft_remaining"], 0)
        reset = reset_draft_quota_for_user(uid)
        self.assertEqual(reset["draft_used"], 0)
        self.assertEqual(reset["draft_remaining"], 10)
        os.environ.pop("DRAFT_HOURLY_LIMIT", None)
        reload(dl)
        reload(mp)


class TestAnalyzePremiumRetries(unittest.TestCase):
    def test_on_demand_three_attempts(self) -> None:
        cfg = MagicMock()
        cfg.ai_active = True
        cfg.ai_provider = "openrouter"
        cfg.ai_model_premium = "test-model"
        lite = AiLiteAnalysis(
            feed_visible=True,
            task_summary="test task",
            lead_tags=("php",),
        )
        with patch("src.ai_analyze._call_once", side_effect=AiAnalyzeError("fail")) as mocked:
            result = analyze_premium(
                cfg,
                title="t",
                budget_text="1000",
                description="desc",
                url="https://fl.ru/1",
                lite=lite,
                errors=[],
                log_prefix="test:",
                max_retries=3,
            )
        self.assertIsNone(result)
        self.assertEqual(mocked.call_count, 3)


if __name__ == "__main__":
    unittest.main()
