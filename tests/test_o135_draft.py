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

from src.ai_analyze import (  # noqa: E402
    _build_shared_reply_user,
    _reply_draft_false_truncation_reason,
    _shared_reply_system,
    _shared_snippet_for_l2,
    validate_stored_l2_draft,
)
from src.ai_analyze import AiLiteAnalysis  # noqa: E402
from src.draft_async import (  # noqa: E402
    DraftPollResponse,
    draft_response_body,
    poll_draft,
    submit_draft,
)
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


class TestO168L2Gates(unittest.TestCase):
    def test_shared_reply_prompt_requires_all_tools(self) -> None:
        sys_prompt = _shared_reply_system(cabinet=False)
        self.assertIn("все", sys_prompt.casefold())
        self.assertIn("photoshop + illustrator", sys_prompt.casefold())

    def test_shared_reply_user_lists_tools_for_enumeration(self) -> None:
        lite = AiLiteAnalysis(
            task_summary="Нарисовать спрайты по референсам",
            feed_visible=True,
            lead_tags=("design",),
            ai_reasons=(),
            complexity=2,
            primary_category="design",
        )
        user = _build_shared_reply_user(
            title="Спрайты",
            budget_text="5000",
            lite=lite,
            tools_required=["photoshop", "illustrator"],
        )
        self.assertIn("photoshop", user.casefold())
        self.assertIn("illustrator", user.casefold())
        self.assertIn("каждый", user.casefold())

    def test_forbidden_word_fails_auto_audit(self) -> None:
        fails = validate_stored_l2_draft(
            verdict="брать",
            reply_draft="Здравствуйте! Сделаю через ChatGPT за 2 дня.",
            tools_required=["python", "javascript"],
            title="API",
            description="Нужен REST API",
        )
        self.assertTrue(any(f.startswith("L2:") for f in fails))

    def test_tools_min_2_required(self) -> None:
        draft = (
            "Здравствуйте! Настрою лендинг на Tilda по ТЗ. "
            "Подскажите, есть ли готовый контент?"
        )
        fails = validate_stored_l2_draft(
            verdict="брать",
            reply_draft=draft,
            tools_required=["figma"],
            title="Tilda",
            description="лендинг Tilda",
        )
        self.assertIn("tools:min_2_required", fails)

    def test_valid_draft_passes(self) -> None:
        draft = (
            "Здравствуйте! Сверстаю лендинг на Tilda по макету Figma. "
            "Подскажите, макет в Figma или PDF?"
        )
        fails = validate_stored_l2_draft(
            verdict="брать",
            reply_draft=draft,
            tools_required=["figma", "javascript"],
            title="Tilda",
            description="лендинг Tilda + Figma",
        )
        self.assertEqual(fails, [])

    def test_shared_reply_user_adds_trunc_note_when_snippet_cut(self) -> None:
        long_desc = "А" * 2500
        lite = AiLiteAnalysis(task_summary="Парсинг базы", feed_visible=True)
        user = _build_shared_reply_user(
            title="Парсинг",
            budget_text="10000",
            lite=lite,
            tools_required=["python"],
            description=long_desc,
        )
        self.assertIn("[Описание обрезано", user)
        snippet, truncated = _shared_snippet_for_l2(long_desc)
        self.assertTrue(truncated)
        self.assertTrue(snippet.endswith("…"))

    def test_fl5508904_false_truncation_fails_audit(self) -> None:
        """O168 g1c: FL #5508904 — полное предложение, ложный «обрывается»."""
        description = (
            "Нужно выкачать базу рецептов из игры. "
            "Рецепты хранятся на сервере игры. "
            "Формат выгрузки — JSON или CSV."
        )
        bad_draft = (
            "Здравствуйте! Вижу задачу по выгрузке рецептов. "
            "Фраза «Рецепты хранятся на…» обрывается — подскажите, где именно лежит база?"
        )
        self.assertIsNotNone(
            _reply_draft_false_truncation_reason(bad_draft, description)
        )
        fails = validate_stored_l2_draft(
            verdict="брать",
            reply_draft=bad_draft,
            tools_required=["python", "postgresql"],
            title="Выкачать базу рецептов из игры",
            description=description,
        )
        self.assertTrue(any("false_truncation_claim" in f for f in fails))

    def test_fl5508904_good_draft_passes(self) -> None:
        description = (
            "Нужно выкачать базу рецептов из игры. "
            "Рецепты хранятся на сервере игры. "
            "Формат выгрузки — JSON или CSV."
        )
        good_draft = (
            "Здравствуйте! Выгружу базу рецептов с сервера игры в JSON или CSV. "
            "Уточните, нужен ли доступ к API или дамп из клиента?"
        )
        fails = validate_stored_l2_draft(
            verdict="брать",
            reply_draft=good_draft,
            tools_required=["python", "postgresql"],
            title="Выкачать базу рецептов из игры",
            description=description,
        )
        self.assertEqual(fails, [])


class TestO159DraftOrConcurrency(unittest.TestCase):
    def test_draft_or_concurrency_single_proxy(self) -> None:
        import config as config_mod
        from src.ai_analyze import draft_or_concurrency

        config_mod._openrouter_proxy_cache = None
        with patch.dict(
            os.environ,
            {"OPENROUTER_HTTP_PROXY": "http://38.154.16.60:8000:user:pass"},
            clear=False,
        ):
            config_mod._openrouter_proxy_cache = None
            self.assertEqual(draft_or_concurrency(), 1)

    def test_draft_or_concurrency_two_proxies(self) -> None:
        import config as config_mod
        from src.ai_analyze import draft_or_concurrency

        config_mod._openrouter_proxy_cache = None
        with patch.dict(
            os.environ,
            {
                "OPENROUTER_PROXY_URLS": (
                    "http://p1:8000:u:p,http://p2:8000:u:p"
                )
            },
            clear=False,
        ):
            config_mod._openrouter_proxy_cache = None
            self.assertEqual(draft_or_concurrency(), 2)

    def test_poll_pending_includes_queue_ahead(self) -> None:
        cfg = MagicMock()
        cfg.database_url = "postgresql://test"

        with (
            patch("src.draft_async._ensure_draft_tables"),
            patch("src.draft_async._fetch_saved_draft", return_value=None),
            patch("src.draft_async._clear_stale_lead_pending"),
            patch("src.draft_async._read_lead_job", return_value=("pending", "")),
            patch("src.draft_async._worker_running", return_value=True),
            patch("src.draft_async._draft_queue_ahead", return_value=2),
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
            )

        self.assertEqual(resp.status, "pending")
        self.assertEqual(resp.queue_ahead, 2)
        body = draft_response_body(resp)
        self.assertTrue(body.get("queued"))
        self.assertEqual(body.get("queue_ahead"), 2)


if __name__ == "__main__":
    unittest.main()
