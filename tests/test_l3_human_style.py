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
    reply_retry_user_suffix,
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
        """O72e-L2-r3/r4: #9843 TG+Google — GAS branch + Python when in TZ."""
        body = build_shared_l2_system()
        self.assertIn("Google Apps Script", body)
        self.assertIn("People API", body)
        self.assertIn("anti-flood", body)

    def test_shared_l2_r4_fail_ids(self) -> None:
        """O72e-L2-r4/r5: pilot fixes — GAS, SEO no perf, FontLab mandatory."""
        body = build_shared_l2_system()
        self.assertIn("GOOD (#9843 GAS)", body)
        self.assertIn("SEO-урок WP (#10362)", body)
        self.assertIn("FontLab", body)
        self.assertIn("wireframe", body)

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
        """O72e-L2-r7: #8752 ed platform — Telegram только из текста ТЗ, не из tools_required."""
        body = build_shared_l2_system()
        self.assertIn("экзамены, видео-плеер, адаптив", body)
        self.assertIn("Telegram/API — **не добавляй**", body)

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


    def test_shared_l2_r6_fixes(self) -> None:
        """O72e-L2-r6: #8772 литература, #10442 Figma/HTML вилка."""
        body = build_shared_l2_system()
        # #8772: литература явно в creative/text категории
        self.assertIn("литература", body)
        # #10442: обязательный вопрос Figma vs HTML когда оба в ТЗ
        self.assertIn("Figma-макет или готовая", body)
        self.assertIn("вопрос-вилку", body)
        self.assertIn("tools_required", body)


    def test_shared_l2_r7_fixes(self) -> None:
        """O72e-L2-r7: #8772 creative — вопрос объём/формат; #8752 — нет TG из tools_required."""
        body = build_shared_l2_system()
        # #8772: вопрос для creative только про объём/формат, не про сюжет
        self.assertIn("объём (знаки или слова)", body)
        self.assertIn("никогда", body)
        # #8752: Telegram/API не добавляй если нет в Описании
        self.assertIn("Telegram/API — **не добавляй**", body)
        self.assertNotIn("упомяни Telegram/API если они в", body)

    def test_shared_l2_r8_creative_tags(self) -> None:
        """O72e-L2-r8: #8772 — фраза «творческая» + «теги карточки»; #8752 — reconcile TG rule."""
        body = build_shared_l2_system()
        # #8772: GOOD-пример содержит «творческая» и «теги карточки»
        self.assertIn("творческая", body)
        self.assertIn("теги карточки", body)
        # #8772: правило creative/text с пояснением tech-тегов
        self.assertIn("creative/text (#8772", body)
        # #8752: TG только если и в Описании и в tools_required
        self.assertIn("и** в Описании **и** в tools_required", body)
        # #8752: три GOOD/BAD примера присутствуют
        self.assertIn("GOOD (#8752 нет TG", body)
        self.assertIn("GOOD (#8752 TG есть", body)

    def test_shared_l2_r9_w1_send_gate(self) -> None:
        """O72e-L2-r9: judge w1 send 50% → блоки send-ready, tools_required, якоря w1."""
        body = build_shared_l2_system()

        # A1: блок «Структура send-ready» присутствует
        self.assertIn("Структура send-ready", body)
        self.assertIn("≥4 предложени", body)
        # A1: FAIL-условие send
        self.assertIn("FAIL send", body)
        self.assertIn("готов присоединиться", body)

        # A2: блок «tools_required — сверка перед ответом»
        self.assertIn("tools_required — сверка перед ответом", body)
        self.assertIn("не из** tools_required", body)

        # A3: якорь #11332 WP каталог — PHP + этапы
        self.assertIn("#11332", body)
        self.assertIn("PHP", body)
        # A3: якорь #9875 книга — Excel
        self.assertIn("#9875", body)
        self.assertIn("Excel", body)
        # A3: якорь #10442 — HTML/CSS вилка
        self.assertIn("HTML/CSS", body)

        # BAD w1: «готов начать» без этапов и инструментов
        self.assertIn("готов начать", body)
        # GOOD #11332: PHP + фильтры + навигация
        self.assertIn("GOOD (#11332)", body)
        # GOOD #9875: Excel + структура книги
        self.assertIn("GOOD (#9875)", body)

    def test_shared_l2_r10_12148_stack_conflict(self) -> None:
        """O72e-L2-r10: #12148 — NestJS/Nuxt из ТЗ, PHP из tools не упоминать."""
        body = build_shared_l2_system()
        self.assertIn("#12148", body)
        self.assertIn("Конфликт tools_required vs Описание", body)
        self.assertIn("GOOD (#12148)", body)
        self.assertIn("webhook handlers", body)

    def test_shared_l2_r11_customer_stack_from_tz(self) -> None:
        """O72e-L2-r11: стек из ТЗ — основной + вспомогательный, не дефолты модели."""
        body = build_shared_l2_system()
        self.assertIn("Стек заказчика", body)
        self.assertIn("вспомогательный", body)
        self.assertIn("не сужай", body)
        self.assertIn("Приоритет", body)

    def test_shared_l2_r12_freeze_depth_tos(self) -> None:
        """O72e-L2-r12: freeze FAIL — ToS-safe #9843, depth CRM/API/SMM."""
        body = build_shared_l2_system()
        self.assertIn("ToS-safe", body)
        self.assertIn("группы-посредники", body)
        self.assertIn("GOOD (#9843 GAS)", body)
        self.assertIn("GOOD (#8915)", body)
        self.assertIn("GOOD (#8774)", body)
        self.assertIn("GOOD (#9316)", body)
        self.assertIn("GOOD (#9861)", body)
        self.assertNotIn("групп-посредников. Опыт с TG-инвайтингом", body)

    # --- O128-L2-VOICE ---

    def test_o128_smell_imeyu_opyt(self) -> None:
        """O128: «имею опыт» → smell/retry."""
        self.assertIsNotNone(l3_ai_smell_reason("Имею опыт разработки Telegram-ботов."))

    def test_o128_smell_ya_ekspert(self) -> None:
        """O128: «я эксперт» → smell/retry."""
        self.assertIsNotNone(l3_ai_smell_reason("Я эксперт в сфере автоматизации."))

    def test_o128_smell_delal_pokhozhee(self) -> None:
        """O128: «делал похожее» → smell/retry."""
        self.assertIsNotNone(l3_ai_smell_reason("Делал похожее для другого интернет-магазина."))

    def test_o128_smell_stack_pref_question(self) -> None:
        """O128: «предпочтение по стеку» → smell/retry."""
        self.assertIsNotNone(
            l3_ai_smell_reason("Подскажите, предпочтение по стеку?")
        )

    def test_o128_smell_stack_choice_question(self) -> None:
        """O128: «какой стек предпочитаете» → smell/retry."""
        self.assertIsNotNone(
            l3_ai_smell_reason("Подскажите, какой стек предпочитаете использовать?")
        )

    def test_o128_good_plan_from_tz_no_smell(self) -> None:
        """O128: план по ТЗ без portfolio-claims → no smell."""
        self.assertIsNone(
            l3_ai_smell_reason(
                "Здравствуйте! По ТЗ — webhook AmoCRM: заявка с формы → сделка, "
                "тест на тестовом аккаунте. REST API Amo, как в описании. "
                "Подскажите, одна воронка или разные по источнику?"
            )
        )

    def test_o128_shared_l2_no_delal_pokhozhee(self) -> None:
        """O128: «Делал похожее» убран из allowed-patterns."""
        body = build_shared_l2_system()
        self.assertNotIn("«Делал похожее", body)

    def test_o128_shared_l2_poziciya_ispolnitelya(self) -> None:
        """O128: блок «Позиция исполнителя» присутствует в shared-промпте."""
        body = build_shared_l2_system()
        self.assertIn("Позиция исполнителя", body)

    def test_o128_shared_l2_plan_vocabulary(self) -> None:
        """O128: словарь O128-B — запрет portfolio-claims, разрешение плана."""
        body = build_shared_l2_system()
        self.assertIn("план по ТЗ", body)
        self.assertIn("делал похожее", body.casefold())

    def test_o128_uniquify_a_plan_not_experience(self) -> None:
        """O128: каркас (A) uniquify — план→шаги→вопрос, без «личного опыта»."""
        body = build_uniquify_system(voice_hint="тест")
        self.assertIn("план→шаги→вопрос", body)
        self.assertNotIn("личного опыта или кейса", body)

    def test_o128_retry_suffix_no_experience_hint(self) -> None:
        """O128: retry suffix «similar» не предлагает «начни с опыта»."""
        suffix = reply_retry_user_suffix(reason="similar", attempt=1, layer="L3")
        self.assertNotIn("начни с опыта", suffix)
        self.assertIn("план→шаги→вопрос", suffix)

    def test_o128_8752_good_no_stack_pref(self) -> None:
        """O128: GOOD #8752 (нет TG) — без «предпочтение по стеку»."""
        body = build_shared_l2_system()
        idx = body.find("GOOD (#8752 нет TG")
        self.assertGreater(idx, 0)
        good_section = body[idx : idx + 300]
        self.assertNotIn("предпочтение по стеку", good_section)

    # --- O164-L2-PROMPT ---

    def test_o164_attachment_offtopic_ignore_rule_present(self) -> None:
        """O164: правило — off-topic вложение (юр. шаблон/портфолио) → игнорировать."""
        body = build_shared_l2_system()
        self.assertIn("Вложение off-topic", body)
        self.assertIn("игнорируй вложение", body)
        self.assertIn("юридический шаблон", body)

    def test_o164_attachment_offtopic_examples_present(self) -> None:
        """O164: примеры off-topic (оферта, приложение №, регламент) указаны в правиле."""
        body = build_shared_l2_system()
        self.assertIn("оферта", body)
        self.assertIn("регламент", body)
        self.assertIn("Приложение №", body)

    def test_o164_attachment_extracted_rule_still_present(self) -> None:
        """O164: правило о файлах/вложениях (базовое) не сломано."""
        body = build_shared_l2_system()
        self.assertIn("[TZ attachment — извлечено", body)
        self.assertIn("Файлы и вложения", body)

    # --- O200-L2-CATEGORY-WAVE ---

    def test_o200_category_playbooks_all_four(self) -> None:
        """O200: Category playbooks block exists for all 4 categories."""
        body = build_shared_l2_system()
        self.assertIn("Category playbooks", body)
        # dev: stack by name, steps, no fake PageSpeed
        self.assertIn("### dev", body)
        self.assertIn("PageSpeed", body)  # anti-hallucination rule referenced
        # design: Figma/Illustrator/Reels, deliverables, no PHP
        self.assertIn("### design", body)
        self.assertIn("deliverables", body)
        # marketing: channel + KPI
        self.assertIn("### marketing", body)
        self.assertIn("KPI", body)
        # text: volume (знаки/слова), tone, format
        self.assertIn("### text", body)
        self.assertIn("знаки", body)

    def test_o200_category_playbooks_bad_good_each(self) -> None:
        """O200: BAD+GOOD pair present for each category playbook."""
        body = build_shared_l2_system()
        # find playbooks block and check BAD/GOOD exist after it
        idx = body.find("Category playbooks")
        self.assertGreater(idx, 0)
        block = body[idx: idx + 6000]
        self.assertIn("BAD:", block)
        self.assertIn("GOOD:", block)
        # at least 4 BAD lines (one per category)
        self.assertGreaterEqual(block.count("BAD:"), 4)
        self.assertGreaterEqual(block.count("GOOD:"), 4)

    def test_o200_category_playbooks_no_dev_tools_in_design(self) -> None:
        """O200: design playbook BAD example must not suggest PHP/WP tools."""
        body = build_shared_l2_system()
        idx = body.find("### design")
        self.assertGreater(idx, 0)
        design_block = body[idx: idx + 1200]
        # playbook says not to add dev tools in design reply
        self.assertIn("PHP", design_block)  # mentioned as forbidden
        # BAD example in design does NOT call for PHP usage
        bad_idx = design_block.find("BAD:")
        if bad_idx >= 0:
            bad_line = design_block[bad_idx: bad_idx + 200]
            self.assertNotIn("PHP", bad_line)

    def test_o200_anti_hallucination_still_intact(self) -> None:
        """O200: anti-hallucination rules not removed (O164 guard)."""
        body = build_shared_l2_system()
        self.assertIn("Anti-hallucination", body)
        self.assertIn("Файлы и вложения", body)
        self.assertIn("[TZ attachment — извлечено", body)


    # --- O200-L2-CAT-80 (r2 playbook micro-fixes) ---

    def test_o200_l2_cat80_marketing_no_invented_budget(self) -> None:
        """O200-L2-CAT-80: marketing — no invented budget/price rule; KPI from TZ only."""
        body = build_shared_l2_system()
        idx = body.find("### marketing")
        self.assertGreater(idx, 0)
        block = body[idx: idx + 1400]
        # tightened KPI rule
        self.assertIn("явно", block)
        self.assertNotIn("логичны из ТЗ", block)
        # no invented budget
        self.assertIn("бюджет", block.casefold())
        self.assertIn("изобретай", block.casefold())
        # price-when-requested guidance
        self.assertIn("цену/стоимость", block)
        # BAD with invented budget
        self.assertIn("BAD (#19933", block)
        # GOOD example with concrete channel
        self.assertIn("GOOD (#19231", block)

    def test_o200_l2_cat80_dev_pipeline_coverage(self) -> None:
        """O200-L2-CAT-80: dev — multi-component pipeline coverage rule present."""
        body = build_shared_l2_system()
        idx = body.find("### dev")
        self.assertGreater(idx, 0)
        block = body[idx: idx + 1050]
        # multi-component pipeline rule
        self.assertIn("Многокомпонентный", block)
        self.assertIn("все слои пайплайна", block)
        # pure AI/ML guard
        self.assertIn("web_scraping", block)
        self.assertIn("pure AI/ML/RAG", block)
        # BAD/GOOD for #19954
        self.assertIn("#19954", block)

    def test_o200_l2_cat80_design_no_ready_when_tz(self) -> None:
        """O200-L2-CAT-80: design — reject «готов когда пришлёте ТЗ»; tool from TZ rule."""
        body = build_shared_l2_system()
        idx = body.find("### design")
        self.assertGreater(idx, 0)
        block = body[idx: idx + 1800]
        # specific tool from TZ rule
        self.assertIn("конкретную программу", block)
        self.assertIn("Видеомонтаж", block)
        # BAD: «Готов начать, когда пришлёте ТЗ»
        self.assertIn("Готов начать, когда пришлёте ТЗ", block)
        # price/portfolio when requested
        self.assertIn("цену/сроки/примеры работ", block)
        # BAD/GOOD for #21614 and #19234
        self.assertIn("#21614", block)
        self.assertIn("#19234", block)


if __name__ == "__main__":
    unittest.main()
