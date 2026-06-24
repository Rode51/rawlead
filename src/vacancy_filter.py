"""O114/O223: pre-L1 отсечение вакансий и физических услуг (не digital-фриланс).

Синхрон с docs/team/archive/FILTERS_DEEP_RESEARCH_2026.md §3 и CODER_PROMPT § O114/O223.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_analyze import AiLiteAnalysis

# Жёсткие маркеры штата (FILTERS §3 + CODER O114)
_STAFF_PHRASES: tuple[str, ...] = (
    "оформление по тк",
    "трудовой договор",
    "оклад от",
    "полная занятость",
    "полная занятость в компан",
    "пришлите резюме",
    "присылайте резюме",
    "hr-менеджер",
    "в офисе",
    "работа в офисе",
    "требования к кандидату",
    "требования к кандидат",
    "примерный уровень зп",
    "уровень зп",
    "ждем от тебя",
    "ждём от тебя",
    "предлагаем от себя",
    "карьерный рост",
    "начало рабочего дня",
    "рабочий день 10:",
    "заполни анкету",
    "анкета hr",
    "откликнуться на позицию",
    "откликаюсь на позицию",
    "digital marketing lead",
    "в штат",
    "сценарист в штат",
    "копирайтер вакансия",
)

# Якоря заголовка/тела (O114 L1 few-shot)
_VACANCY_ANCHOR_RE = re.compile(
    r"(?:"
    r"вакансия\s*[—\-–:]|"
    r"вакансия\s+удал|"
    r"ищем\s+(?:в\s+)?штат|"
    r"вакансия:\s*|"
    r"набор\s+в\s+команду|"
    r"подбор\s+персонала"
    r")",
    re.I,
)

_ZP_HIRE_RE = re.compile(
    r"(?:"
    r"з\s*/\s*п\s+от|"
    r"з/п\s+от|"
    r"зп\s+от|"
    r"зарплат[аы]\s+от|"
    r"з/п\s+\d|"
    r"з\s*п\s+\d"
    r")",
    re.I,
)

# «разовый проект» / фриланс без маркеров штата — не резать
_FREELANCE_PROJECT_HINTS: tuple[str, ...] = (
    "разовый проект",
    "разовая задача",
    "разовый заказ",
    "проект на фриланс",
    "фриланс-заказ",
    "бюджет проекта",
    "срок выполнения",
    "оплата по факту",
    "оплата по договор",
)


def _haystack(title: str, body: str = "") -> str:
    return f"{title}\n{body}".casefold()


def is_staff_vacancy(title: str, body: str = "") -> bool:
    """True — найм в штат / вакансия, не показывать в /lenta/."""
    hay = _haystack(title, body)
    if not hay.strip():
        return False

    for phrase in _STAFF_PHRASES:
        if phrase.casefold() in hay:
            return True

    freelance_hint = _has_freelance_project_hint(hay)
    if freelance_hint:
        return False

    if _VACANCY_ANCHOR_RE.search(hay):
        return True

    if "вакансия" in hay and _has_hire_context(hay):
        return True

    if _ZP_HIRE_RE.search(hay):
        return True

    return False


def _has_freelance_project_hint(hay: str) -> bool:
    return any(h.casefold() in hay for h in _FREELANCE_PROJECT_HINTS)


def _has_hire_context(hay: str) -> bool:
    hire = (
        "штат",
        "резюме",
        "кандидат",
        "собеседован",
        "трудов",
        "оклад",
        "зарплат",
        "з/п",
        "з п ",
        "hr",
        "откликнуться:",
        "откликнуться ",
        "анкета",
        "должность",
        "работодатель",
    )
    return any(m in hay for m in hire)


def vacancy_lite_analysis(*, title: str, body: str = "") -> AiLiteAnalysis | None:
    """Готовый L1-результат без OpenRouter, если это вакансия."""
    if not is_staff_vacancy(title, body):
        return None
    from ai_analyze import AiLiteAnalysis

    return AiLiteAnalysis(
        feed_visible=False,
        task_summary="вакансии, не фриланс-заказ",
        lead_tags=(),
        ai_reasons=(
            "Найм в штат / вакансия — не фриланс-заказ",
            "Маркеры HR, зарплаты или трудового договора",
        ),
        complexity=1,
        primary_category="",
    )


# O223/O245: физические / логистические / onsite-услуги YouDo (не digital-фриланс)
_PHYSICAL_SERVICE_MARKERS: tuple[str, ...] = (
    "гидроборт",
    "перевоз",
    "грузчик",
    "междугород",
    "эвакуатор",
    "погрузк",
    "паллет",
    "рохл",
    "курьер",
    "выезд",
    "на дому",
    "у клиента",
    "с указанием адреса",
    "по адресу",
    "установить виндоус",
    "установить windows",
    "установка виндоус",
    "установка windows",
    "на imac",
    "на macbook",
    "массаж",
    "уборк",
    "стеллаж",
    "собрать мебел",
    "сборка мебел",
    "клининг",
)

# «курьер» без digital-контекста — физуслуга; API/бот/CRM — dev
_DIGITAL_COURIER_HINTS: tuple[str, ...] = (
    "api",
    "интеграц",
    "telegram",
    "телеграм",
    "бот",
    "crm",
    "разработ",
    "программ",
    "сайт",
    "приложен",
    "wordpress",
    "бэкенд",
    "backend",
    "rest api",
)


def _has_digital_courier_hint(hay: str) -> bool:
    return any(h in hay for h in _DIGITAL_COURIER_HINTS)


def is_physical_service_job(title: str, body: str = "") -> bool:
    """True — логистика/физическая услуга, не показывать в /lenta/."""
    hay = _haystack(title, body)
    if not hay.strip():
        return False
    for marker in _PHYSICAL_SERVICE_MARKERS:
        if marker.casefold() not in hay:
            continue
        if marker == "курьер" and _has_digital_courier_hint(hay):
            continue
        return True
    return False


def physical_service_lite_analysis(*, title: str, body: str = "") -> AiLiteAnalysis | None:
    """Готовый L1-результат без OpenRouter, если физическая услуга."""
    if not is_physical_service_job(title, body):
        return None
    from ai_analyze import AiLiteAnalysis

    return AiLiteAnalysis(
        feed_visible=False,
        task_summary="физическая услуга, не digital-фриланс",
        lead_tags=(),
        ai_reasons=(
            "Физическая или onsite-услуга — не digital-фриланс",
            "Маркеры выезда, адреса клиента, перевозки или onsite-установки",
        ),
        complexity=1,
        primary_category="",
    )
