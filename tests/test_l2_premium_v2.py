"""O49: L2 premium reply_draft validation."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from ai_analyze import AiAnalyzeError, _validate_reply_draft_take  # noqa: E402


class TestL2PremiumV2(TestCase):
    def test_rejects_gotov_start(self) -> None:
        with self.assertRaises(AiAnalyzeError):
            _validate_reply_draft_take("Готов заменить текущий модуль на новый.")

    def test_rejects_gotov_lowercase(self) -> None:
        with self.assertRaises(AiAnalyzeError):
            _validate_reply_draft_take("готов взяться за проект.")

    def test_accepts_zainteresoval(self) -> None:
        draft = _validate_reply_draft_take(
            "Заинтересовал проект. Сначала разберу форму, потом поправлю валидацию "
            "и выкачу на staging. Срок 3 дня, старт от 12 000 ₽."
        )
        self.assertTrue(draft.startswith("Заинтересовал"))

    def test_accepts_sdelaju(self) -> None:
        draft = _validate_reply_draft_take(
            "Сделаю интеграцию API: подключу webhook, проверю idempotency, "
            "добавлю логи. От 8 000 ₽, 2 дня."
        )
        self.assertIn("Сделаю", draft)

    def test_accepts_zdravstvuyte_greeting(self) -> None:
        draft = _validate_reply_draft_take(
            "Здравствуйте. Заинтересовал проект. Сначала разберу форму, "
            "потом поправлю валидацию. Срок 3 дня, от 12 000 ₽."
        )
        self.assertTrue(draft.startswith("Здравствуйте"))

    def test_rejects_zdravstvuyte_gotov(self) -> None:
        with self.assertRaises(AiAnalyzeError):
            _validate_reply_draft_take(
                "Здравствуйте. Готов реализовать модуль за 3 дня."
            )
