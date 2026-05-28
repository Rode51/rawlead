"""Фикстуры лидов для § PRE-PROD-STRESS (4 category × ≥3)."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class PreprodLeadFixture:
    id: str
    category: str
    title: str
    budget_text: str
    snippet: str
    url: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


PREPROD_LEAD_FIXTURES: tuple[PreprodLeadFixture, ...] = (
    # dev
    PreprodLeadFixture(
        id="dev-1",
        category="dev",
        title="Telegram-бот на Python: парсинг заказов и уведомления",
        budget_text="25 000 ₽",
        snippet=(
            "Нужен бот на aiogram 3: подписка на каналы, фильтр по ключевым словам, "
            "отправка карточек в личку. БД PostgreSQL, деплой на VPS."
        ),
        url="https://www.fl.ru/projects/5507001/",
    ),
    PreprodLeadFixture(
        id="dev-2",
        category="dev",
        title="REST API на FastAPI + интеграция с CRM",
        budget_text="40 000 ₽",
        snippet=(
            "Разработать API для приёма лидов с сайта, валидация, webhook в Bitrix24. "
            "Документация OpenAPI, pytest, Docker-compose."
        ),
        url="https://kwork.ru/projects/123456",
    ),
    PreprodLeadFixture(
        id="dev-3",
        category="dev",
        title="Автоматизация Excel → Google Sheets скрипт",
        budget_text="8 000 ₽",
        snippet=(
            "Ежедневная выгрузка отчёта из Excel, расчёт KPI, запись в Google Sheets "
            "через Apps Script или Python. Без ручного копирования."
        ),
        url="https://freelancehunt.com/project/avtomatizaciya-otcheta/123",
    ),
    # design
    PreprodLeadFixture(
        id="design-1",
        category="design",
        title="UI/UX дизайн мобильного приложения в Figma",
        budget_text="35 000 ₽",
        snippet=(
            "5 экранов onboarding + главная + профиль. Design system, компоненты, "
            "прототип кликабельный. Стиль минимализм, iOS guidelines."
        ),
        url="https://www.fl.ru/projects/5507102/",
    ),
    PreprodLeadFixture(
        id="design-2",
        category="design",
        title="Логотип и фирменный стиль для IT-стартапа",
        budget_text="12 000 ₽",
        snippet=(
            "Логотип (3 концепта), палитра, шрифты, варианты для соцсетей. "
            "Исходники в векторе, гайд на 2 страницы."
        ),
        url="https://kwork.ru/projects/234567",
    ),
    PreprodLeadFixture(
        id="design-3",
        category="design",
        title="Монтаж Reels 60 сек: продуктовый ролик",
        budget_text="6 000 ₽",
        snippet=(
            "Исходники 4K, нужен динамичный монтаж под музыку, субтитры, "
            "цветокор. Формат 9:16 для Instagram."
        ),
        url="https://www.fl.ru/projects/5507203/",
    ),
    # marketing
    PreprodLeadFixture(
        id="marketing-1",
        category="marketing",
        title="Настройка Яндекс.Директ: лидогенерация B2B",
        budget_text="20 000 ₽",
        snippet=(
            "Семантика, РСЯ + поиск, UTM, цели в Метрике. Бюджет теста 30k. "
            "Отчёт по CPA через 2 недели."
        ),
        url="https://www.fl.ru/projects/5507304/",
    ),
    PreprodLeadFixture(
        id="marketing-2",
        category="marketing",
        title="Ведение Instagram: контент-план + stories",
        budget_text="15 000 ₽/мес",
        snippet=(
            "Ниша косметика, 12 постов + 20 stories в месяц. "
            "Таргет на подписчиков, аналитика охватов."
        ),
        url="https://kwork.ru/projects/345678",
    ),
    PreprodLeadFixture(
        id="marketing-3",
        category="marketing",
        title="SEO-аудит сайта на WordPress + ТЗ исправлений",
        budget_text="10 000 ₽",
        snippet=(
            "Технический аудит, Core Web Vitals, семантика 50 запросов, "
            "рекомендации по контенту и перелинковке."
        ),
        url="https://freelancehunt.com/project/seo-audit-wp/456",
    ),
    # text
    PreprodLeadFixture(
        id="text-1",
        category="text",
        title="Тексты для лендинга SaaS: 5 блоков",
        budget_text="7 000 ₽",
        snippet=(
            "Hero, преимущества, тарифы, FAQ, CTA. Тон деловой, без воды. "
            "УТП — автоматизация фриланса. Нужен docx + правки 1 раунд."
        ),
        url="https://www.fl.ru/projects/5507405/",
    ),
    PreprodLeadFixture(
        id="text-2",
        category="text",
        title="Перевод технической документации EN → RU",
        budget_text="5 000 ₽",
        snippet=(
            "API-документация ~8000 слов, терминология IT сохраняется. "
            "Гlossарий согласовать до старта."
        ),
        url="https://kwork.ru/projects/456789",
    ),
    PreprodLeadFixture(
        id="text-3",
        category="text",
        title="Редактура и вычитка статей для блога (10 шт)",
        budget_text="4 000 ₽",
        snippet=(
            "Статьи по маркетингу, 3000–5000 знаков каждая. "
            "Орфография, стиль, единообразие заголовков."
        ),
        url="https://freelancehunt.com/project/redaktura-blog/789",
    ),
)

CATEGORIES: tuple[str, ...] = ("dev", "design", "marketing", "text")
