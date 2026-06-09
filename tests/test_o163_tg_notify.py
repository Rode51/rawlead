"""O163-TG-NOTIFY: gate, spam filter, no raw forward.

Покрывает DoD:
  1. Gate: владелец получает notify только при feed_visible AND public_feed_source.
  2. Нет raw forward (forward_listing_to_owner не вызывается).
  3. Pre-L1: promo-бот, CV «ищу проект/заказчиков», affiliate отсекаются.
  4. plan=None для tg-источника без public_feed (даже при feed_visible=True).
"""

from __future__ import annotations

import asyncio
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.tg_spam_filter import is_tg_spam, tg_spam_lite_analysis  # noqa: E402


# ── 1. Unit-тесты is_tg_spam ─────────────────────────────────────────────────


class TestTgSpamFilter(unittest.TestCase):

    # --- NOT spam: обычные заказы ---

    def test_freelance_order_not_spam(self):
        self.assertFalse(
            is_tg_spam(
                "Нужен разработчик Telegram-бота",
                "Сделать бота для сбора заявок, aiogram, PostgreSQL, бюджет 25 000 ₽.",
            )
        )

    def test_wp_order_not_spam(self):
        self.assertFalse(
            is_tg_spam(
                "WordPress: доработка темы",
                "Нужно поправить шапку и добавить блок на главной. Бюджет 8 000 ₽.",
            )
        )

    def test_parsing_order_not_spam(self):
        self.assertFalse(
            is_tg_spam(
                "Парсинг каталога",
                "Собрать 1000 товаров с сайта конкурента в таблицу Google Sheets.",
            )
        )

    def test_design_order_not_spam(self):
        self.assertFalse(
            is_tg_spam(
                "Дизайн лендинга",
                "Нужен дизайн одностраничника, срок 5 дней, оплата по факту.",
            )
        )

    def test_api_order_not_spam(self):
        self.assertFalse(
            is_tg_spam(
                "FastAPI backend для мобильного приложения",
                "Разработать REST API, авторизация JWT, Postgres, Redis, бюджет 40 000 ₽.",
            )
        )

    # --- Promo-бот реклама ---

    def test_bot_promo_subscribe(self):
        self.assertTrue(
            is_tg_spam(
                "Заработок онлайн",
                "Подписывайся на @earnbot и получай пассивный доход! 🔥",
            )
        )

    def test_bot_promo_try_free(self):
        self.assertTrue(
            is_tg_spam(
                "Попробуй наш сервис",
                "Попробуй бесплатно @newtoolbot — автоматизация заявок без кода.",
            )
        )

    def test_bot_promo_join(self):
        self.assertTrue(
            is_tg_spam(
                "",
                "Присоединяйся к нашему боту @promobot и зарабатывай прямо сейчас!",
            )
        )

    def test_bot_promo_register(self):
        self.assertTrue(
            is_tg_spam(
                "Регистрируйся",
                "Зарегистрируйся в @cashbot и получи бонус 500 рублей.",
            )
        )

    def test_bot_promo_partner(self):
        self.assertTrue(
            is_tg_spam(
                "Партнёрка",
                "Реферальная программа @affiliatebot — зарабатывай с каждого приглашённого.",
            )
        )

    # --- CV / «ищу проект» ---

    def test_cv_freelancer_seeking_project(self):
        self.assertTrue(
            is_tg_spam(
                "Ищу проект на разработку ботов",
                "Меня зовут Иван, Python-разработчик, ищу проект на фриланс.",
            )
        )

    def test_cv_seeking_client(self):
        self.assertTrue(
            is_tg_spam(
                "Фронтенд разработчик",
                "Ищу заказчиков, опыт 5 лет, React/Vue, портфолио в профиле.",
            )
        )

    def test_cv_in_search_of_orders(self):
        self.assertTrue(
            is_tg_spam(
                "В поиске заказов",
                "Дизайнер логотипов, в поиске клиентов, цены договорные.",
            )
        )

    def test_cv_offering_services(self):
        self.assertTrue(
            is_tg_spam(
                "Предлагаю услуги разработки",
                "Предлагаю свои услуги: сайты, боты, парсеры. Готов к сотрудничеству.",
            )
        )

    def test_cv_my_resume(self):
        self.assertTrue(
            is_tg_spam(
                "PHP разработчик",
                "Моё резюме: 8 лет опыта, WordPress, Laravel. Ищу удалённую работу.",
            )
        )

    def test_cv_anchor_in_title(self):
        self.assertTrue(
            is_tg_spam(
                "Ищу заказы на Python-разработку",
                "Доступен для новых проектов, опыт 4 года.",
            )
        )

    # --- Граничные случаи ---

    def test_empty_is_not_spam(self):
        self.assertFalse(is_tg_spam("", ""))

    def test_bot_mention_without_promo_not_spam(self):
        # Упоминание бота без промо-слов — не спам
        self.assertFalse(
            is_tg_spam(
                "Нужен бот Telegram",
                "Разработать @mycompanybot для CRM, aiogram, бюджет 20 000 ₽.",
            )
        )

    def test_promo_word_without_bot_not_spam(self):
        # Слово «бесплатно» без @*_bot упоминания — не прomo-spam (CV проверить отдельно)
        self.assertFalse(
            is_tg_spam(
                "Тестирование бесплатно",
                "Первые 3 часа работы бесплатно, далее 2500 ₽/час.",
            )
        )


# ── 2. tg_spam_lite_analysis возвращает feed_visible=False ───────────────────


class TestTgSpamLiteAnalysis(unittest.TestCase):

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key", "AI_ACTIVE": "1"})
    def test_spam_returns_feed_visible_false(self):
        result = tg_spam_lite_analysis(
            "Ищу проект Python",
            "Ищу проект на фриланс, опыт 5 лет, готов к сотрудничеству.",
        )
        self.assertIsNotNone(result)
        self.assertFalse(result.feed_visible)  # type: ignore[union-attr]

    def test_non_spam_returns_none(self):
        result = tg_spam_lite_analysis(
            "Нужен Python-разработчик",
            "Разработать скрипт парсинга, бюджет 15 000 ₽.",
        )
        self.assertIsNone(result)


# ── 3. process_new_listing_from_tg: gate + no raw forward ────────────────────


def _make_cfg(*, site_notify_owner: bool = True, ai_active: bool = False):
    cfg = MagicMock()
    cfg.ai_active = ai_active
    cfg.ai_uses_l1_l2 = False
    cfg.radar_profile = "site"
    cfg.site_notify_owner = site_notify_owner
    cfg.ai_notify_skip = False
    cfg.site_notify_on_ai_unavailable = False
    cfg.neon_ingest_wide = False
    cfg.filter_wide = False
    cfg.radar_log_path = ""
    cfg.match_push_enabled = False
    cfg.min_budget_rub = 0
    cfg.telegram_chat_id = "12345"
    return cfg


def _make_project(source: str = "tg:99999"):
    from src.listing import ListingProject

    return ListingProject(
        project_id=42,
        title="Разработка бота",
        budget_text="15000",
        url="https://t.me/c/99999/100",
        published_at="",
        listing_snippet="Нужен Telegram-бот, aiogram, PostgreSQL.",
        source=source,
    )


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestProcessTgGate(unittest.TestCase):
    """Gate DoD1: notify только при feed_visible AND public_feed_source."""

    def _run_tg(self, source: str, *, feed_visible: bool, public_sources: str = "fl,kwork"):
        from src.ai_analyze import AiLiteAnalysis
        from src.lead_pipeline import ListingNotifyPlan, process_new_listing_from_tg

        lite = AiLiteAnalysis(
            feed_visible=feed_visible,
            task_summary="test",
            lead_tags=(),
            ai_reasons=(),
            complexity=2,
            primary_category="dev",
        )
        plan = ListingNotifyPlan(
            project=_make_project(source),
            lite_analysis=lite,
            analysis=None,
            ai_unavailable=False,
            task_fallback_text="test",
        )

        storage = MagicMock()
        storage.try_record_new.return_value = True
        storage.is_neon_dup_fast_path.return_value = False
        storage.get_neon_synced_hash.return_value = None
        storage.try_record_content_fingerprint.return_value = True

        word_filter = MagicMock()
        word_filter.accepts_listing.return_value = True

        msg = MagicMock()
        client = MagicMock()
        cfg = _make_cfg()

        with patch.dict(os.environ, {"PUBLIC_FEED_SOURCES": public_sources}):
            # Clear lru_cache so env var change takes effect
            from src import public_feed
            public_feed.public_feed_sources.cache_clear()

            with patch(
                "src.lead_pipeline.ingest_with_l1", return_value=(True, plan)
            ) as mock_ingest, patch(
                "src.lead_pipeline.send_listing_notification", return_value=True
            ) as mock_send, patch(
                "src.tg_forward.forward_listing_to_owner", new_callable=AsyncMock
            ) as mock_fwd:
                was_new, notified = _run(
                    process_new_listing_from_tg(
                        msg, client, _make_project(source), storage, word_filter, cfg,
                        errors=[], pg=None, account="acc2", chat_title="TestChat",
                    )
                )
            return was_new, notified, mock_send.called, mock_fwd.called

    def test_tg_source_not_in_public_feed_no_notify(self):
        """TG ∉ PUBLIC_FEED_SOURCES → no notify, even if feed_visible=True (DoD1)."""
        was_new, notified, send_called, fwd_called = self._run_tg(
            "tg:99999", feed_visible=True, public_sources="fl,kwork"
        )
        self.assertTrue(was_new)
        self.assertFalse(notified)
        self.assertFalse(send_called, "send_listing_notification must NOT be called")
        self.assertFalse(fwd_called, "forward_listing_to_owner must NOT be called (DoD2)")

    def test_tg_source_feed_visible_false_no_notify(self):
        """feed_visible=False → no notify regardless of source."""
        _, notified, send_called, _ = self._run_tg(
            "tg:99999", feed_visible=False, public_sources="fl,kwork,tg:99999"
        )
        self.assertFalse(notified)
        self.assertFalse(send_called)

    def test_public_source_feed_visible_true_notifies(self):
        """Source in PUBLIC_FEED_SOURCES + feed_visible=True → notify sent."""
        _, notified, send_called, fwd_called = self._run_tg(
            "fl", feed_visible=True, public_sources="fl,kwork"
        )
        self.assertTrue(notified)
        self.assertTrue(send_called)
        # Raw forward must never be called (DoD2)
        self.assertFalse(fwd_called, "forward_listing_to_owner must NOT be called (DoD2)")

    def test_no_raw_forward_even_when_notify(self):
        """Форматированная карточка — без raw Telethon forward (DoD2)."""
        _, _, _, fwd_called = self._run_tg(
            "fl", feed_visible=True, public_sources="fl,kwork"
        )
        self.assertFalse(fwd_called)

    def tearDown(self):
        # Always clear cache after each test
        from src import public_feed
        public_feed.public_feed_sources.cache_clear()


# ── 4. process_new_listing_from_tg: spam skip before ingest ──────────────────


class TestProcessTgSpamSkip(unittest.TestCase):
    """Spam filter (DoD3): ingest_with_l1 не вызывается для promo/CV."""

    def _run_spam_check(self, title: str, body: str) -> tuple[bool, bool, bool]:
        from src.lead_pipeline import process_new_listing_from_tg
        from src.listing import ListingProject

        project = ListingProject(
            project_id=7,
            title=title,
            budget_text="",
            url="https://t.me/c/1/7",
            published_at="",
            listing_snippet=body,
            source="tg:1",
        )
        storage = MagicMock()
        word_filter = MagicMock()
        msg = MagicMock()
        client = MagicMock()
        cfg = _make_cfg()

        with patch(
            "src.lead_pipeline.ingest_with_l1", return_value=(True, None)
        ) as mock_ingest:
            was_new, notified = _run(
                process_new_listing_from_tg(
                    msg, client, project, storage, word_filter, cfg,
                    errors=[], pg=None,
                )
            )
        return was_new, notified, mock_ingest.called

    def test_promo_bot_skipped_no_ingest(self):
        was_new, notified, ingest_called = self._run_spam_check(
            "Подписывайся на нашего бота!",
            "Зарабатывай онлайн! Подписывайся на @earnbot и получай доход.",
        )
        self.assertFalse(was_new)
        self.assertFalse(notified)
        self.assertFalse(ingest_called, "ingest_with_l1 must not be called for spam")

    def test_cv_seeking_project_skipped(self):
        was_new, notified, ingest_called = self._run_spam_check(
            "Ищу проект по разработке",
            "Python-разработчик, ищу проект на фриланс, готов к сотрудничеству.",
        )
        self.assertFalse(was_new)
        self.assertFalse(notified)
        self.assertFalse(ingest_called, "ingest_with_l1 must not be called for CV")

    def test_valid_order_proceeds_to_ingest(self):
        _, _, ingest_called = self._run_spam_check(
            "Нужен разработчик API",
            "Создать FastAPI сервис, авторизация JWT, бюджет 30 000 ₽.",
        )
        self.assertTrue(ingest_called, "ingest_with_l1 MUST be called for valid orders")


if __name__ == "__main__":
    unittest.main()
