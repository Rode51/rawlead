"""O56/O59a: async draft job helpers."""

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
    _poll_error_from_stored,
    _run_generation,
    _user_facing_error,
    draft_response_body,
    _run_generation,
    sanitize_draft_error_detail,
    submit_draft,
)
from match_push import DraftError  # noqa: E402  (same module as draft_async)


class TestDraftAsyncHelpers(unittest.TestCase):
    def test_user_facing_ai_fail_timeout(self) -> None:
        msg = _user_facing_error(DraftError("ai_fail", "openrouter: request timed out"))
        self.assertIn("не успел", msg)

    def test_sanitize_strips_generic(self) -> None:
        self.assertEqual(
            sanitize_draft_error_detail("draft generation failed"),
            "ИИ временно недоступен — повторите",
        )

    def test_poll_error_from_stored(self) -> None:
        msg = _poll_error_from_stored("openrouter: HTTP 429 rate limit")
        self.assertIn("перегружен", msg)

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

    def test_draft_response_failed_has_error(self) -> None:
        resp = DraftPollResponse(
            status="failed",
            lead_id=7,
            error="ИИ не успел ответить — повторите",
        )
        body = draft_response_body(resp)
        self.assertEqual(body["status"], "failed")
        self.assertEqual(body["error"], resp.error)
        self.assertEqual(body["detail"], resp.error)

    def test_draft_response_pending(self) -> None:
        body = draft_response_body(DraftPollResponse(status="pending", lead_id=1))
        self.assertEqual(body["status"], "pending")
        self.assertNotIn("reply_draft", body)


class TestAnalyzeSharedOndemand(unittest.TestCase):
    def test_backoff_calls_four_times(self) -> None:
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
                description="desc",
                lite=lite,
                tools_required=["python"],
                ai_errors=[],
                log_prefix="test:",
                max_retries=4,
            )
        self.assertIsNone(result)
        self.assertEqual(mocked.call_count, 4)


class TestRunGenerationFail(unittest.TestCase):
    def test_ai_fail_stores_detail_and_sanitized_poll(self) -> None:
        cfg = MagicMock()
        cfg.database_url = "postgresql://test"
        fail_exc = DraftError("ai_fail", "openrouter: timeout after 90s")

        with patch(
            "src.draft_async.generate_and_store_lead_draft",
            side_effect=fail_exc,
        ):
            from src import draft_async as da
            da._job_errors.clear()
            da._active_futures.clear()
            _run_generation(cfg, "uid", 12, "test:")

        stored = da._job_errors.get(("uid", 12))
        self.assertEqual(stored, "openrouter: timeout after 90s")
        poll_err = _poll_error_from_stored(stored or "")
        self.assertIn("не успел", poll_err)


class TestSubmitPerUserKey(unittest.TestCase):
    def test_submit_starts_worker_per_user(self) -> None:
        cfg = MagicMock()
        cfg.ai_active = True
        cfg.database_url = "postgresql://test"

        with (
            patch("src.draft_async._start_worker") as start_worker,
            patch(
                "src.draft_async.poll_draft",
                return_value=DraftPollResponse(status="pending", lead_id=5),
            ),
            patch("src.draft_async.psycopg.connect") as mock_connect,
        ):
            mock_cur = MagicMock()
            mock_cur.fetchone.return_value = None
            mock_conn = MagicMock()
            mock_conn.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur
            mock_connect.return_value = mock_conn

            resp_a = submit_draft(cfg, user_id="u1", lead_id=5, quick_wait_sec=0)
            resp_b = submit_draft(cfg, user_id="u2", lead_id=5, quick_wait_sec=0)

        self.assertEqual(start_worker.call_count, 2)
        self.assertEqual(resp_a.status, "pending")
        self.assertEqual(resp_b.status, "pending")


if __name__ == "__main__":
    unittest.main()
