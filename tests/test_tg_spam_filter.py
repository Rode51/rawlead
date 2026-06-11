"""O170-TG-L1-FILTER: тесты seller-voice/infobiz фильтра и post-L1 guard.

Покрывает:
  1. is_tg_spam: seller-voice, infobiz, scarcity → True (spam).
  2. is_tg_spam: реальные заказы → False (не spam).
  3. is_tg_order_post: заказ с маркерами → True; реклама без → False.
  4. Кейс #20170-class: «книга под ключ / автографы» → is_tg_spam=True.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import unittest

from src.tg_spam_filter import is_tg_order_post, is_tg_spam


# ── 1. Seller-voice → SPAM ─────────────────────────────────────────────────


class TestSellerVoiceSpam(unittest.TestCase):

    def test_nasha_komanda(self):
        self.assertTrue(
            is_tg_spam(
                "Разработка сайтов",
                "Наша команда делает лендинги под ключ. Портфолио: @studio_tg",
            )
        )

    def test_my_predlagaem(self):
        self.assertTrue(
            is_tg_spam(
                "Продвижение в TG",
                "Мы предлагаем услуги по продвижению Telegram-каналов. Пишите в личку.",
            )
        )

    def test_pod_kluch_s_seller(self):
        """#20170-class: книга под ключ — самый типичный кейс."""
        self.assertTrue(
            is_tg_spam(
                "Книга под ключ",
                "Написание, вёрстка, автографы — делаем под ключ. Примеры работ в профиле.",
            )
        )

    def test_pod_kluch_explicit(self):
        self.assertTrue(
            is_tg_spam(
                "SMM под ключ",
                "Создаём контент и ведём соцсети под ключ. Стоимость от 15 000 ₽/мес.",
            )
        )

    def test_prinimaem_zayavki(self):
        self.assertTrue(
            is_tg_spam(
                "Разработка Telegram-ботов",
                "Принимаем заявки на разработку ботов. Наш сайт: rawlead.ru",
            )
        )

    def test_pishhite_v_lku(self):
        self.assertTrue(
            is_tg_spam(
                "Дизайн логотипов",
                "Создаю фирменный стиль и логотипы. Примеры работ:, пишите в личку.",
            )
        )

    def test_besplatnaya_konsultaciya(self):
        self.assertTrue(
            is_tg_spam(
                "SEO для вашего сайта",
                "Бесплатная консультация по продвижению. Мы предлагаем аудит сайта.",
            )
        )

    def test_stoimost_ot(self):
        self.assertTrue(
            is_tg_spam(
                "Верстка сайтов",
                "Верстаем сайты любой сложности. Стоимость от 5000 ₽. Пишите нам.",
            )
        )

    def test_my_delaem(self):
        self.assertTrue(
            is_tg_spam(
                "Парсинг данных",
                "Мы делаем парсеры для любых сайтов. Обращайтесь к нам.",
            )
        )

    def test_nashe_agentstvo(self):
        self.assertTrue(
            is_tg_spam(
                "Реклама в TG",
                "Наше агентство ведет рекламные кампании в Telegram. Наш телеграм: @agency",
            )
        )


# ── 2. Инфобиз / воронка → SPAM ───────────────────────────────────────────


class TestInfobizSpam(unittest.TestCase):

    def test_nastavnichestvo(self):
        self.assertTrue(
            is_tg_spam(
                "Наставничество по фрилансу",
                "Наставничество для фрилансеров — выйди на 100к за 3 месяца.",
            )
        )

    def test_voronka_prodazh(self):
        self.assertTrue(
            is_tg_spam(
                "Воронка продаж для вашего бизнеса",
                "Создаю воронку продаж в TG. Лид-магнит + серия прогрева + продажа.",
            )
        )

    def test_lyd_magnit(self):
        self.assertTrue(
            is_tg_spam(
                "Продвижение онлайн-школы",
                "Напишу лид-магнит и запускаю курс для вашей аудитории.",
            )
        )

    def test_marafon(self):
        self.assertTrue(
            is_tg_spam(
                "Марафон по SMM",
                "Запускаю марафон по SMM-продвижению. Осталось 5 мест.",
            )
        )

    def test_scarcity_mesta(self):
        self.assertTrue(
            is_tg_spam(
                "Группа по Python",
                "Осталось 3 из 10 мест в моей группе. Записывайтесь сейчас.",
            )
        )


# ── 3. Реальные заказы → НЕ спам ─────────────────────────────────────────


class TestRealOrderNotSpam(unittest.TestCase):

    def test_tg_bot_order(self):
        self.assertFalse(
            is_tg_spam(
                "Нужен разработчик Telegram-бота",
                "Нужен разработчик TG-бота для сбора заявок. Бюджет 25 000 ₽, aiogram.",
            )
        )

    def test_tilda_order(self):
        self.assertFalse(
            is_tg_spam(
                "Требуется верстальщик Tilda",
                "Требуется специалист по Tilda для сборки лендинга. ТЗ есть. Бюджет 8к.",
            )
        )

    def test_parser_order(self):
        self.assertFalse(
            is_tg_spam(
                "Парсинг каталога товаров",
                "Нужно собрать 5000 товаров в Google Sheets. Срок — неделя. Бюджет 3000 ₽.",
            )
        )

    def test_wp_order(self):
        self.assertFalse(
            is_tg_spam(
                "WordPress: правки темы",
                "Нужно поправить шапку и подвал. Бюджет 5000 ₽, срок 3 дня.",
            )
        )

    def test_designer_order(self):
        self.assertFalse(
            is_tg_spam(
                "Ищем дизайнера для Tilda",
                "Ищем дизайнера для оформления лендинга. ТЗ есть, бюджет обсуждается.",
            )
        )

    def test_pod_kluch_buyer_voice(self):
        """«Под ключ» в устах заказчика — не спам."""
        self.assertFalse(
            is_tg_spam(
                "Нужен сайт под ключ",
                "Нужен сайт под ключ на WordPress. Бюджет до 40к, срок — месяц.",
            )
        )


# ── 4. is_tg_order_post (post-L1 guard) ──────────────────────────────────


class TestIsTgOrderPost(unittest.TestCase):

    def test_nuzhen_razrabotchik(self):
        self.assertTrue(
            is_tg_order_post(
                "Нужен разработчик бота",
                "Нужен разработчик aiogram для Telegram-бота. Бюджет 20к.",
            )
        )

    def test_trebuetsya(self):
        self.assertTrue(
            is_tg_order_post(
                "Требуется верстальщик",
                "Требуется верстальщик Tilda. Срок — неделя, оплата 8000 ₽.",
            )
        )

    def test_tz_est(self):
        self.assertTrue(
            is_tg_order_post(
                "Разработка парсера",
                "ТЗ есть, нужен Python-разработчик для парсинга сайта.",
            )
        )

    def test_budzhet_marker(self):
        self.assertTrue(
            is_tg_order_post(
                "Сайт на Tilda",
                "Собрать лендинг на Tilda. Бюджет: 10 000 ₽.",
            )
        )

    # --- False: реклама без маркеров заказа ---

    def test_seller_no_order_marker(self):
        self.assertFalse(
            is_tg_order_post(
                "Книга под ключ",
                "Написание, вёрстка, автографы. Примеры работ в профиле. Стоимость от 50к.",
            )
        )

    def test_smm_promo(self):
        self.assertFalse(
            is_tg_order_post(
                "SMM-продвижение",
                "Наша команда ведёт соцсети. Пишите в лс для консультации.",
            )
        )

    def test_infobiz_no_order(self):
        self.assertFalse(
            is_tg_order_post(
                "Наставничество",
                "Наставничество для фрилансеров. Осталось 3 места. Записывайтесь.",
            )
        )

    def test_empty(self):
        self.assertFalse(is_tg_order_post("", ""))


# ── 5. Проверка #20170-class напрямую ────────────────────────────────────


class TestLead20170Class(unittest.TestCase):
    """Прямой кейс из CODER_PROMPT: «книга под ключ / автографы» → SPAM."""

    _TITLE = "Книга под ключ"
    _BODY = (
        "Привет! Пишу книги под ключ — от идеи до публикации. "
        "Включает: написание текста, редактура, вёрстка, обложка, "
        "организация подписи/автографов от автора. "
        "Примеры работ: /channel/bookstudio. Стоимость от 80 000 ₽. "
        "Пишите в личку для консультации."
    )

    def test_is_spam(self):
        self.assertTrue(is_tg_spam(self._TITLE, self._BODY))

    def test_no_order_markers(self):
        self.assertFalse(is_tg_order_post(self._TITLE, self._BODY))


if __name__ == "__main__":
    unittest.main()
