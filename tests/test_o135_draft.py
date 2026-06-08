"""O135-DRAFT: L2-only first user · draft_async restart · OpenRouter proxy."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.draft_async import DraftPollResponse, poll_draft, submit_draft  # noqa: E402
from src.match_push import generate_and_store_lead_draft  # noqa: E402

_USER = "00000000-0000-0000-0000-000000000201"
_LEAD_ID = 15146

_LEAD_ROW = (
    _LEAD_ID,
    "kwork",
    "Test lead",
    "body",
    "https://kwork.ru/1",
    "5000",
    80,
    "Брать",
    '["python"]',
    "[]",
    None,
    "dev",
    "Need Python API",
    '["python"]',
    "",
)


class TestO135FirstUserL2Only(unittest.TestCase):
    @patch("src.match_push.psycopg.connect")
    @patch("src.match_push._analyze_shared_ondemand", return_value="L2 shared text.")
    @patch("src.match_push.rephrase_reply_draft_per_user")
    @patch("src.match_push.keyword_match", return_value=80)
    @patch("src.match_push._canonical_lead_tags", return_value=["python"])
    @patch("src.match_push._parse_ai_reasons", return_value=[])
    @patch("src.match_push._parse_tools_required", return_value=["python"])
    @patch("src.match_push._user_effective_access", return_value=True)
    @patch("src.match_push._fetch_lead_row", return_value=_LEAD_ROW)
    @patch("src.match_push._fetch_saved_draft", return_value=None)
    @patch("src.match_push._load_user_tags", return_value={"python": 1.0})
    @patch("src.match_push.draft_rate_limit_retry_after", return_value=None)
    @patch("src.match_push.note_draft_request")
    @patch("src.match_push.strip_reply_draft_price_deadline", side_effect=lambda x: x)
    def test_first_user_skips_l3(
        self,
        _strip: MagicMock,
        _note: MagicMock,
        _rate: MagicMock,
        _tags: MagicMock,
        _saved: MagicMock,
        _row: MagicMock,
        _access: MagicMock,
        _tools: MagicMock,
        _reasons: MagicMock,
        _canonical: MagicMock,
        _km: MagicMock,
        rephrase: MagicMock,
        _analyze: MagicMock,
        _connect: MagicMock,
    ) -> None:
        cfg = MagicMock()
        cfg.ai_active = True
        cfg.database_url = "postgresql://test"
        conn = MagicMock()
        cur = MagicMock()
        _connect.return_value.__enter__.return_value = conn
        conn.cursor.return_value.__enter__.return_value = cur

        with patch("src.match_push._insert_user_draft") as insert:
            result = generate_and_store_lead_draft(
                cfg,
                user_id=_USER,
                lead_id=_LEAD_ID,
                log_prefix=f"lenta:draft:{_LEAD_ID}:",
                enforce_rate_limit=False,
            )

        rephrase.assert_not_called()
        insert.assert_called_once()
        self.assertEqual(insert.call_args[0][3], "L2 shared text.")
        self.assertEqual(result.reply_draft, "L2 shared text.")


class TestO135PollRestart(unittest.TestCase):
    def test_poll_restarts_dead_worker_instead_of_not_started(self) -> None:
        cfg = MagicMock()
        cfg.database_url = "postgresql://test"

        with (
            patch("src.draft_async._ensure_draft_tables"),
            patch("src.draft_async._fetch_saved_draft", return_value=None),
            patch("src.draft_async._clear_stale_lead_pending"),
            patch("src.draft_async._read_lead_job", return_value=("pending", "")),
            patch("src.draft_async._worker_running", return_value=False),
            patch("src.draft_async._restart_worker") as restart,
            patch("src.draft_async.psycopg.connect") as mock_connect,
        ):
            mock_cur = MagicMock()
            mock_conn = MagicMock()
            mock_conn.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur
            mock_connect.return_value = mock_conn

            resp = poll_draft(
                cfg,
                user_id=_USER,
                lead_id=_LEAD_ID,
                log_prefix=f"lenta:draft:{_LEAD_ID}:",
            )

        self.assertEqual(resp.status, "pending")
        restart.assert_called_once()

    def test_submit_restarts_pending_dead_worker(self) -> None:
        cfg = MagicMock()
        cfg.ai_active = True
        cfg.database_url = "postgresql://test"

        with (
            patch("src.draft_async._ensure_draft_tables"),
            patch("src.draft_async._fetch_saved_draft", return_value=None),
            patch("src.draft_async._clear_stale_lead_pending"),
            patch("src.draft_async._read_lead_job", return_value=("pending", "")),
            patch("src.draft_async._insert_lead_pending"),
            patch("src.draft_async._worker_running", return_value=False),
            patch("src.draft_async._restart_worker") as restart,
            patch(
                "src.draft_async.poll_draft",
                return_value=DraftPollResponse(status="pending", lead_id=_LEAD_ID),
            ),
            patch("src.draft_async.psycopg.connect") as mock_connect,
        ):
            mock_cur = MagicMock()
            mock_conn = MagicMock()
            mock_conn.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.__enter__.return_value = mock_cur
            mock_connect.return_value = mock_conn

            resp = submit_draft(
                cfg,
                user_id=_USER,
                lead_id=_LEAD_ID,
                quick_wait_sec=0,
            )

        self.assertEqual(resp.status, "pending")
        restart.assert_called_once()


class TestO135OpenRouterProxy(unittest.TestCase):
    def test_openrouter_proxy_from_env(self) -> None:
        import config as config_mod

        config_mod._openrouter_proxy_cache = None
        with patch.dict(
            os.environ,
            {"OPENROUTER_HTTP_PROXY": "http://proxy.example:8080:user:pass"},
            clear=False,
        ):
            config_mod._openrouter_proxy_cache = None
            urls = config_mod.openrouter_proxy_urls()
            hint = config_mod.openrouter_proxy_hint()
            proxies = config_mod.openrouter_requests_proxies()

        self.assertEqual(len(urls), 1)
        self.assertIn("proxy.example:8080", urls[0])
        self.assertEqual(hint, "proxy.example:8080")
        self.assertEqual(proxies["http"], urls[0])

    @patch("src.ai_analyze.requests.post")
    def test_openrouter_chat_uses_draft_proxy(self, mock_post: MagicMock) -> None:
        import config as config_mod
        from src.ai_analyze import _openrouter_chat

        config_mod._openrouter_proxy_cache = None
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": '{"reply_draft":"hi"}'}}]
        }
        cfg = MagicMock()
        cfg.ai_api_key = "sk-test"

        with patch.dict(
            os.environ,
            {"OPENROUTER_HTTP_PROXY": "http://127.0.0.1:3128"},
            clear=False,
        ):
            config_mod._openrouter_proxy_cache = None
            _openrouter_chat(
                cfg,
                model="google/gemini-2.5-pro",
                system="sys",
                user="usr",
                timeout_sec=10.0,
                json_mode=True,
                use_draft_proxy=True,
            )

        kwargs = mock_post.call_args.kwargs
        self.assertIn("127.0.0.1:3128", kwargs["proxies"]["http"] or "")

    @patch("src.ai_analyze._openrouter_chat")
    def test_shared_reply_draft_uses_proxy_when_env(
        self, mock_chat: MagicMock
    ) -> None:
        import config as config_mod
        from src.ai_analyze import AiLiteAnalysis, analyze_shared_reply_draft

        config_mod._openrouter_proxy_cache = None
        mock_chat.return_value = '{"reply_draft":"Привет, готов взяться."}'
        cfg = MagicMock()
        cfg.ai_active = True
        cfg.ai_provider = "openrouter"
        cfg.ai_model_shared_draft = "google/gemini-2.5-pro"
        lite = AiLiteAnalysis(feed_visible=True, task_summary="Нужен лендинг")

        with patch.dict(
            os.environ,
            {"OPENROUTER_HTTP_PROXY": "http://38.154.16.60:8000:user:pass"},
            clear=False,
        ):
            config_mod._openrouter_proxy_cache = None
            analyze_shared_reply_draft(
                cfg,
                title="Лендинг",
                budget_text="50000",
                lite=lite,
                lead_id=1,
            )

        kwargs = mock_chat.call_args.kwargs
        self.assertTrue(kwargs.get("use_draft_proxy"))


if __name__ == "__main__":
    unittest.main()
