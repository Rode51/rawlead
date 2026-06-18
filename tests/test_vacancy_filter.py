"""O114/O245: pre-L1 vacancy filter — freelance vs staff + physical/onsite services."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from vacancy_filter import is_physical_service_job, is_staff_vacancy, vacancy_lite_analysis  # noqa: E402

_FREELANCE_OK = (
    (
        "Разовый проект: вёрстка лендинга на Tilda",
        "Нужна вёрстка одной страницы по макету Figma, бюджет 12 000 ₽, срок 5 дней.",
    ),
    (
        "Доработка WordPress: формы и Метрика",
        "Удалённо: поправить Contact Form 7, цели Яндекс.Метрики, оплата по факту.",
    ),
    (
        "Парсинг каталога в Google Sheets",
        "Собрать 500 SKU конкурента в таблицу, API есть, бюджет проекта 18 000.",
    ),
    (
        "Telegram-бот для заявок",
        "Разовая задача: бот принимает заявки, Neon, срок выполнения 10 дней.",
    ),
    (
        "Копирайт 5 статей для блога",
        "Разовый проект — 5 статей, 800 ₽/знак, срок 7 дней, оплата по факту, без штата.",
    ),
)

_VACANCY_BAD = (
    (
        "🖥 Вакансия — Удалённо",
        "Digital Marketing Lead. Требования к кандидату. Примерный уровень ЗП: от 200 000 ₽.",
    ),
    (
        "**Копирайтер**",
        "З/П от 70 000 рублей. Начало рабочего дня 10:00-19:00. Карьерный рост.",
    ),
    (
        "Сценарист для сторис",
        "З/п 80 000 на старте. Ждём от тебя опыт. Заполни анкету: forms.yandex.ru",
    ),
    (
        "Менеджер по продажам",
        "Полная занятость в компании, оклад от 90 000, трудовой договор, пришлите резюме HR.",
    ),
    (
        "UI-дизайнер",
        "Оформление по ТК РФ, работа в офисе Москва, полная занятость.",
    ),
)


def test_freelance_not_vacancy() -> None:
    for title, body in _FREELANCE_OK:
        assert not is_staff_vacancy(title, body), (title, body)


def test_staff_vacancy_detected() -> None:
    for title, body in _VACANCY_BAD:
        assert is_staff_vacancy(title, body), (title, body)


def test_vacancy_lite_hidden() -> None:
    lite = vacancy_lite_analysis(
        title="Вакансия копирайтер",
        body="оклад от 80 000, трудовой договор",
    )
    assert lite is not None
    assert lite.feed_visible is False
    assert lite.is_skip_verdict()
    assert "вакансии" in lite.task_summary.casefold()


_T14858651_TITLE = "Установить виндоус на iMac"
_T14858651_BODY = (
    "Нужна помощь с установкой Windows на iMac, с указанием адреса для выезда мастера."
)


def test_physical_repro_t14858651() -> None:
    assert is_physical_service_job(_T14858651_TITLE, _T14858651_BODY)


def test_physical_vyezd_marker() -> None:
    assert is_physical_service_job("Мастер на выезд", "Ремонт техники у клиента")


def test_physical_na_domu_marker() -> None:
    assert is_physical_service_job("Уборка на дому", "Квартира в центре")


def test_remote_dev_not_physical() -> None:
    title = "Разработка REST API на Python"
    body = "Удалённо: FastAPI, Neon, оплата по факту."
    assert not is_physical_service_job(title, body)
