"""O50/O54: TG push + reply_draft strip tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import TestCase

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from match_push import (  # noqa: E402
    _DRAFT_CALLBACK_RE,
    _format_push_text,
    _push_keyboard,
)
from reply_draft_strip import (  # noqa: E402
    strip_reply_draft_price_deadline,
    strip_tg_draft_price_deadline,
)


class TestMatchPushO50(TestCase):
    def test_format_push_includes_source_budget_tags(self) -> None:
        text = _format_push_text(
            title="Плагин WooCommerce",
            source="fl",
            budget_text="15 000 ₽",
            task_summary="Нужен фикс корзины и оплаты.",
            match_pct=67,
            lead_tags=["wordpress_dev", "php"],
            tools_required=["git", "docker"],
        )
        self.assertIn("Match 67%", text)
        self.assertIn("FL.ru", text)
        self.assertIn("15 000", text)
        self.assertIn("Плагин WooCommerce", text)
        self.assertIn("Навыки:", text)
        self.assertIn("Инструменты:", text)

    def test_push_keyboard_paid_has_callback(self) -> None:
        raw = _push_keyboard(
            show_generate=True, lead_id=7019, order_url="https://fl.ru/projects/123/"
        )
        data = json.loads(raw)
        rows = data["inline_keyboard"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0]["text"], "Не моё")
        self.assertEqual(rows[0][0]["callback_data"], "nope:7019")
        self.assertEqual(rows[0][1]["text"], "Отклик")
        self.assertEqual(rows[0][1]["callback_data"], "draft:7019")
        self.assertEqual(rows[1][0]["text"], "Смотреть в ленте")
        self.assertEqual(rows[1][0]["url"], "https://rawlead.ru/lenta/?lead=7019")
        self.assertEqual(rows[1][1]["text"], "Смотреть на бирже")
        self.assertEqual(rows[1][1]["url"], "https://fl.ru/projects/123/")

    def test_push_keyboard_free_still_four_buttons(self) -> None:
        raw = _push_keyboard(show_generate=False, lead_id=42, order_url="https://kwork.ru/project/1")
        data = json.loads(raw)
        rows = data["inline_keyboard"]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][1]["callback_data"], "draft:42")
        self.assertEqual(rows[1][1]["url"], "https://kwork.ru/project/1")

    def test_format_push_uses_order_url(self) -> None:
        text = _format_push_text(
            title="Тест",
            source="fl",
            budget_text="10 000 ₽",
            task_summary="",
            match_pct=80,
            lead_tags=[],
            tools_required=[],
            order_url="https://fl.ru/projects/999/",
        )
        self.assertIn("https://fl.ru/projects/999/", text)

    def test_draft_callback_pattern(self) -> None:
        m = _DRAFT_CALLBACK_RE.match("draft:12345")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "12345")

    def test_strip_tg_draft_removes_price_deadline(self) -> None:
        raw = (
            "Здравствуйте. Заинтересовал проект.\n"
            "Сначала разберу API, потом добавлю тесты.\n"
            "Срок 5 дней, старт от 15 000 ₽."
        )
        out = strip_tg_draft_price_deadline(raw)
        self.assertIn("Здравствуйте", out)
        self.assertIn("API", out)
        self.assertNotIn("15 000", out)
        self.assertNotIn("5 дней", out)

    def test_strip_inline_price_deadline_tail(self) -> None:
        raw = (
            "Здравствуйте. Заинтересовал проект с Python и Neon. "
            "Ориентировочный срок — 2 недели, стоимость — от 45 000 руб."
        )
        out = strip_reply_draft_price_deadline(raw)
        self.assertIn("Python и Neon", out)
        self.assertNotIn("2 недели", out)
        self.assertNotIn("45 000", out)
        self.assertNotIn("стоимость", out.casefold())
