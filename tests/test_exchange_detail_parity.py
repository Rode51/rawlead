"""O141: detail TZ parity for all web exchanges."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from exchange_detail import fetch_project_detail, is_web_detail_source  # noqa: E402
from lead_pipeline import _resolve_ingest_body  # noqa: E402
from listing import ListingProject  # noqa: E402
from ai_analyze import _shared_draft_too_vague  # noqa: E402
from match_push import _format_push_text, push_match_for_lead  # noqa: E402
from telegram_notify import _source_labels  # noqa: E402
from youdo_parser import _parse_youdo_detail_html  # noqa: E402


class TestExchangeDetailParity(TestCase):
    def test_youdo_detail_longer_than_listing_snippet(self) -> None:
        snippet = "Короткий сниппет с листинга."
        html = (_ROOT / "tests" / "fixtures" / "o141_youdo_detail.html").read_text(
            encoding="utf-8"
        )
        body = _parse_youdo_detail_html(html, fallback_snippet=snippet)
        self.assertGreater(len(body), len(snippet))
        self.assertIn("aiogram 3", body)
        self.assertIn("PostgreSQL", body)

    def test_is_web_detail_source_includes_youdo(self) -> None:
        self.assertTrue(is_web_detail_source("youdo"))
        self.assertFalse(is_web_detail_source("tg:-100123"))

    def test_resolve_ingest_body_dispatches_youdo(self) -> None:
        project = ListingProject(
            project_id=99001,
            title="AI companion бот",
            budget_text="до 50 000 ₽",
            url="https://youdo.com/t99001",
            published_at="",
            listing_snippet="Короткий сниппет.",
            source="youdo",
        )
        cfg = MagicMock()
        errors: list[str] = []
        long_body = "X" * 600
        with patch(
            "lead_pipeline.fetch_project_detail",
            return_value=(long_body, "<html></html>", True),
        ) as mock_fetch:
            body, tz, _ = _resolve_ingest_body(project, cfg, errors)
        mock_fetch.assert_called_once()
        self.assertEqual(body, long_body)
        self.assertIsNone(tz)
        self.assertGreater(len(body), len(project.listing_snippet))

    def test_fetch_project_detail_fallback_on_error(self) -> None:
        cfg = MagicMock()
        with patch(
            "youdo_parser.fetch_project_detail",
            return_value=("snippet", "", False),
        ):
            text, html, ok = fetch_project_detail(
                "youdo",
                "https://youdo.com/t1",
                cfg,
                fallback_snippet="snippet",
            )
        self.assertFalse(ok)
        self.assertEqual(text, "snippet")
        self.assertEqual(html, "")

    def test_telegram_notify_youdo_label(self) -> None:
        site, button = _source_labels("youdo")
        self.assertEqual(site, "YouDo")
        self.assertIn("YouDo", button)
        self.assertNotEqual(site, "FL")

    def test_push_text_youdo_source_label(self) -> None:
        text = _format_push_text(
            title="AI companion бот",
            source="youdo",
            budget_text="50 000 ₽",
            task_summary="aiogram 3 + Postgres + Redis + RAG",
            match_pct=72,
            lead_tags=["telegram_bot_dev", "python"],
            tools_required=["postgresql", "redis"],
            order_url="https://youdo.com/t99001",
        )
        self.assertIn("YouDo", text)
        self.assertNotIn("FL.ru", text)

    def test_vague_bot_question_rejected_for_bot_lead(self) -> None:
        reason = _shared_draft_too_vague(
            "Здравствуйте! Что должен делать бот? Расскажите задачу.",
            title="AI companion бот в Telegram",
            tools_required=["telegram_bot_dev", "python"],
        )
        self.assertEqual(reason, "vague:bot_what_should_do")

    def test_push_match_for_lead_youdo_visible(self) -> None:
        cfg = MagicMock()
        cfg.match_push_enabled = True
        cfg.database_url = "postgresql://test"
        cfg.telegram_bot_token = "123:ABC"

        lead_row = (
            42,
            "youdo",
            "AI companion бот",
            "body",
            "https://youdo.com/t99001",
            "50 000 ₽",
            80,
            "Брать",
            ["telegram_bot_dev", "python"],
            (),
            None,
            "dev",
            "aiogram 3 Postgres Redis",
            ["postgresql"],
            None,
        )
        user_row = (
            "00000000-0000-0000-0000-000000000001",
            111222333,
            "beta",
            True,
            None,
            None,
            50,
            True,
        )

        mock_cur = MagicMock()
        mock_cur.fetchone.side_effect = [
            lead_row,
            (None,),
            None,
            None,
            ("beta", True, None, None),
        ]
        mock_cur.fetchall.return_value = [user_row]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        errors: list[str] = []
        with (
            patch("match_push.psycopg.connect", return_value=mock_conn),
            patch(
                "match_push._load_user_tags",
                return_value={"telegram_bot_dev": 4.0, "python": 4.0},
            ),
            patch("match_push._send_push_message", return_value=(True, "")) as mock_send,
        ):
            sent = push_match_for_lead(
                cfg,
                42,
                title="AI companion бот",
                task_summary="aiogram 3",
                lead_tags=["telegram_bot_dev", "python"],
                errors=errors,
            )
        self.assertEqual(sent, 1)
        mock_send.assert_called_once()
        push_text = mock_send.call_args[0][2]
        self.assertIn("YouDo", push_text)


if __name__ == "__main__":
    import unittest

    unittest.main()
