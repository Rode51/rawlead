"""O72e-regen-tail: allowlist «ИИ»/«ИИ-бот» из ТЗ заказчика в reply_draft."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from ai_analyze import (  # noqa: E402
    AiAnalyzeError,
    _check_forbidden_reply_words,
    _validate_reply_draft_take,
)

_TITLE_9909 = "Привлечь клиентов в ИИ-Бота в телеграмм"
_DESC_9909 = (
    "Нужно привлечь пользователей в нейробота в Телеграмм для генерации текстов/фото/видео"
)


class TestForbiddenReplyAllowlist(TestCase):
    def test_9909_customer_ii_bot_passes(self) -> None:
        draft = (
            "Здравствуйте! Помогу привлечь пользователей в ваш ИИ-бот в Telegram: "
            "настрою каналы, посевы и аналитику пополнений. "
            "Подскажите, какие площадки уже пробовали?"
        )
        out = _validate_reply_draft_take(
            draft,
            title=_TITLE_9909,
            description=_DESC_9909,
        )
        self.assertIn("ИИ-бот", out)

    def test_chatgpt_always_fails(self) -> None:
        draft = "Здравствуйте! Сделаю через ChatGPT за 2 дня."
        with self.assertRaises(AiAnalyzeError):
            _validate_reply_draft_take(
                draft,
                title=_TITLE_9909,
                description=_DESC_9909,
            )

    def test_ii_without_lead_context_fails(self) -> None:
        draft = "Здравствуйте! Помогу с вашим ИИ-ботом."
        with self.assertRaises(AiAnalyzeError):
            _validate_reply_draft_take(draft)

    def test_ai_method_phrase_fails_even_with_lead_context(self) -> None:
        draft = "Здравствуйте! Реализую задачу через ИИ за 3 дня."
        with self.assertRaises(AiAnalyzeError):
            _check_forbidden_reply_words(
                draft,
                title=_TITLE_9909,
                description=_DESC_9909,
            )

    def test_ventilyatsiya_no_false_positive(self) -> None:
        _check_forbidden_reply_words(
            "Здравствуйте! Настрою автоматику ИТП и вентиляции.",
            title="ИТП",
            description="автоматика ИТП и вентиляции",
        )
