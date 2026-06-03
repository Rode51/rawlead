"""O99: L3 human style — similarity, AI smell, prompt builder."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from l3_human_style import (  # noqa: E402
    build_shared_l2_system,
    build_uniquify_system,
    l3_ai_smell_reason,
    l3_too_similar,
    l3_voice_hint,
)


class TestL3HumanStyle(unittest.TestCase):
    def test_too_similar_cosmetic_synonyms(self) -> None:
        shared = (
            "Здравствуйте! Выполню дизайн презентации из 17 слайдов. "
            "Сначала создам мастер-слайд, затем подберу изображения. "
            "Уточните, есть ли брендбук?"
        )
        personal = (
            "Здравствуйте! Разработаю дизайн презентации на 17 слайдов. "
            "Для начала создам мастер-слайд, далее подберу изображения. "
            "Подскажите, есть ли брендбук?"
        )
        self.assertTrue(l3_too_similar(shared, personal))

    def test_not_similar_when_restructured(self) -> None:
        shared = (
            "Здравствуйте! Разработаю backend для Telegram mini app. "
            "Сначала спроектирую архитектуру TON. Затем API для NFT. "
            "Какой стек на бэкенде?"
        )
        personal = (
            "Здравствуйте! По ТЗ — mini app и NFT на TON. "
            "Подключу API под ваши подарки, схему согласуем до кода. "
            "Подскажите, бэкенд уже на Python или с нуля?"
        )
        self.assertFalse(l3_too_similar(shared, personal))

    def test_ai_smell_detects_hard_phrases(self) -> None:
        self.assertIsNotNone(
            l3_ai_smell_reason("Здравствуйте! Обеспечу качественную реализацию модуля.")
        )
        self.assertIsNotNone(l3_ai_smell_reason("Заинтересовала задача по монтажу видео."))
        self.assertIsNone(
            l3_ai_smell_reason(
                "Здравствуйте! Подготовлю креативы, демонстрирующие возможности сервиса."
            )
        )

    def test_shared_l2_includes_ideal_example(self) -> None:
        body = build_shared_l2_system()
        self.assertIn("Telethon", body)
        self.assertIn("Пример идеального отклика", body)

    def test_shared_l2_specificity_domain_patterns(self) -> None:
        """O72e-L2-r2: новые specificity-якоря и BAD/GOOD по паттернам judge."""
        body = build_shared_l2_system()
        # #8925 GAS/Rhino migration
        self.assertIn("Browser.msgBox", body)
        self.assertIn("console.log", body)
        # #10442 Midjourney + Figma / HTML
        self.assertIn("HTML/CSS", body)
        # #9581 SVG Illustrator
        self.assertIn("Illustrator", body)
        # #9326 3D Cinema 4D + STL
        self.assertIn("Cinema 4D", body)
        self.assertIn("STL", body)
        # #9374 B2B — этапы + UI-kit
        self.assertIn("UI-kit", body)
        # specificity domain block
        self.assertIn("Specificity-якоря по домену", body)

    def test_build_system_includes_voice(self) -> None:
        hint = l3_voice_hint(42)
        body = build_uniquify_system(voice_hint=hint)
        self.assertIn(hint, body)
        self.assertIn("FL.ru/Kwork", body)
        self.assertIn("анти-копипаста", body.casefold())

    def test_build_uniquify_system_has_three_patterns(self) -> None:
        body = build_uniquify_system(voice_hint="тест")
        self.assertIn("(A)", body)
        self.assertIn("(B)", body)
        self.assertIn("(C)", body)

    def test_too_similar_ratio_070(self) -> None:
        shared = (
            "Здравствуйте! Выполню дизайн презентации из 17 слайдов. "
            "Сначала создам мастер-слайд, затем подберу изображения. "
            "Уточните, есть ли брендбук?"
        )
        personal = (
            "Здравствуйте! Разработаю дизайн презентации на 17 слайдов. "
            "Для начала создам мастер-слайд, далее подберу изображения. "
            "Подскажите, есть ли брендбук?"
        )
        self.assertTrue(l3_too_similar(shared, personal, min_ratio=0.70))

    def test_not_similar_restructured_ton_070(self) -> None:
        shared = (
            "Здравствуйте! Разработаю backend для Telegram mini app. "
            "Сначала спроектирую архитектуру TON. Затем API для NFT. "
            "Какой стек на бэкенде?"
        )
        personal = (
            "Здравствуйте! По ТЗ — mini app и NFT на TON. "
            "Подключу API под ваши подарки, схему согласуем до кода. "
            "Подскажите, бэкенд уже на Python или с нуля?"
        )
        self.assertFalse(l3_too_similar(shared, personal, min_ratio=0.70))

    def test_shared_l2_r3_streaming_domain(self) -> None:
        """O72e-L2-r3: #9831 стриминг — domain-insight блок и BAD/GOOD."""
        body = build_shared_l2_system()
        self.assertIn("Глубина без простыни", body)
        self.assertIn("монетизация", body)
        self.assertIn("подписки рядом с подписчиками", body)
        self.assertIn("UI-kit или редизайн с нуля", body)

    def test_shared_l2_r3_tg_limits(self) -> None:
        """O72e-L2-r3: #9843 TG+Google — Python/Telethon + лимиты Telegram."""
        body = build_shared_l2_system()
        self.assertIn("Python/Telethon", body)
        self.assertIn("anti-flood", body)
        self.assertIn("import→validate→groups grid", body)

    def test_shared_l2_r3_fontlab(self) -> None:
        """O72e-L2-r3: #9581 SVG — FontLab при тексте в логотипе."""
        body = build_shared_l2_system()
        self.assertIn("FontLab", body)

    def test_shared_l2_r3_tools_required_rule(self) -> None:
        """O72e-L2-r3: tools_required vs Описание — правило в Anti-hallucination."""
        body = build_shared_l2_system()
        self.assertIn("tools_required vs Описание", body)
        self.assertIn("text/design/творческий", body)

    def test_shared_l2_r3_ed_platform_no_telegram(self) -> None:
        """O72e-L2-r3: #8752 ed platform — без telegram если не в Описании."""
        body = build_shared_l2_system()
        self.assertIn("экзамены, видео-плеер, адаптив", body)
        self.assertIn("telegram/api если не в Описании", body)

    def test_shared_l2_r3_ai_design_rounds(self) -> None:
        """O72e-L2-r3: #10442 AI-дизайн — раунды генерации → Figma, ограничения AI."""
        body = build_shared_l2_system()
        self.assertIn("2–3 раунда генерации", body)
        self.assertIn("AI не заменит", body)

    def test_shared_l2_r3_bad_good_new_ids(self) -> None:
        """O72e-L2-r3: #9831 и #8752 добавлены в BAD/GOOD."""
        body = build_shared_l2_system()
        self.assertIn("#9831", body)
        self.assertIn("#8752", body)


if __name__ == "__main__":
    unittest.main()
