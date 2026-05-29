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
        raw = _push_keyboard(show_generate=True, lead_id=7019)
        data = json.loads(raw)
        row = data["inline_keyboard"][0]
        self.assertEqual(row[0]["callback_data"], "draft:7019")
        self.assertEqual(row[1]["text"], "Открыть ленту")

    def test_push_keyboard_free_no_generate(self) -> None:
        raw = _push_keyboard(show_generate=False, lead_id=42)
        data = json.loads(raw)
        row = data["inline_keyboard"][0]
        self.assertEqual(len(row), 1)
        self.assertIn("url", row[0])

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
