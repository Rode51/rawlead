"""O56: async draft job helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.draft_async import (  # noqa: E402
    DraftPollResponse,
    _user_facing_error,
    draft_response_body,
)
from src.match_push import DraftError  # noqa: E402


class TestDraftAsyncHelpers(unittest.TestCase):
    def test_user_facing_ai_fail(self) -> None:
        msg = _user_facing_error(DraftError("ai_fail", "draft generation failed"))
        self.assertIn("ИИ временно недоступен", msg)

    def test_draft_response_ready(self) -> None:
        resp = DraftPollResponse(
            status="ready",
            lead_id=42,
            reply_draft="Привет",
            tools_required=["Figma"],
            keyword_match=80,
        )
        body = draft_response_body(resp)
        self.assertEqual(body["status"], "ready")
        self.assertEqual(body["reply_draft"], "Привет")
        self.assertEqual(body["keyword_match"], 80)

    def test_draft_response_pending(self) -> None:
        body = draft_response_body(DraftPollResponse(status="pending", lead_id=1))
        self.assertEqual(body["status"], "pending")
        self.assertNotIn("reply_draft", body)


class TestAnalyzeSharedOndemand(unittest.TestCase):
    def test_backoff_calls_multiple_times(self) -> None:
        from src.match_push import _analyze_shared_ondemand

        cfg = MagicMock()
        cfg.ai_active = True
        cfg.ai_provider = "openrouter"
        lite = MagicMock()
        with patch("src.match_push.analyze_shared_reply_draft", return_value=None) as mocked:
            result = _analyze_shared_ondemand(
                cfg,
                title="t",
                budget_text="1",
                lite=lite,
                tools_required=["python"],
                ai_errors=[],
                log_prefix="test:",
                max_retries=3,
            )
        self.assertIsNone(result)
        self.assertEqual(mocked.call_count, 3)


if __name__ == "__main__":
    unittest.main()
