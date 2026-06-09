"""O163: pre-L1 фильтр TG-спама (promo-бот реклама, CV фрилансера, партнёрки).

Вызывается в lead_pipeline.process_new_listing_from_tg до ingest_with_l1.
Возвращает is_tg_spam() → bool или tg_spam_lite_analysis() → AiLiteAnalysis|None.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_analyze import AiLiteAnalysis

# ── Bot-promo: @username_bot упоминание в тексте ──────────────────────────────

_BOT_USERNAME_RE = re.compile(r"@\w*bot\b", re.I)

_PROMO_PHRASES: tuple[str, ...] = (
    "подписывайся",
    "подпишись",
    "переходи по ссылке",
    "переходи в бот",
    "переходи в чат",
    "жми по ссылке",
    "жми на ссылку",
    "перейди в бот",
    "попробуй бесплатно",
    "попробовать бесплатно",
    "бесплатно по ссылке",
    "присоединяйся",
    "реферальн",
    "партнёрка",
    "партнерка",
    "заработай на",
    "зарабатывай",
    "пассивный доход",
    "приглашаю в",
    "регистрируйся",
    "зарегистрируйся",
    "наш бот",
    "мой бот",
    "наш сервис",
    "реклама:",
    "#реклама",
)

# ── CV / «ищу проект» ────────────────────────────────────────────────────────

_CV_ANCHOR_RE = re.compile(
    r"(?:"
    r"ищу\s+(?:проект|заказ[ы]?|заказчик|клиент|работу|фриланс)|"
    r"в\s+поиске\s+(?:проект[аов]?|заказ[аов]?|клиент[аов]?)|"
    r"доступен\s+для\s+(?:новых\s+)?проектов|"
    r"ищу\s+удал[её]нн|"
    r"открыт\s+(?:для\s+)?(?:новых\s+)?проектов|"
    r"помогу\s+с\s+проект"
    r")",
    re.I,
)

_CV_PHRASES: tuple[str, ...] = (
    "ищу проект",
    "ищу заказ",
    "ищу заказчик",
    "ищу клиент",
    "ищу работу на фриланс",
    "ищу проекты на фриланс",
    "в поиске проекта",
    "в поиске заказов",
    "в поиске клиент",
    "предлагаю свои услуги",
    "предлагаю услуги разработ",
    "мои услуги:",
    "моё резюме",
    "мое резюме",
    "портфолио в профиле",
    "нанять меня",
    "нанимайте меня",
    "готов к сотрудничеству",
    "опыт работы:",
)

# ── helpers ───────────────────────────────────────────────────────────────────


def _haystack(title: str, body: str) -> str:
    return f"{title}\n{body}".casefold()


def _is_bot_promo(hay: str) -> bool:
    """True если: @*_bot упоминание + промо-слово."""
    if not _BOT_USERNAME_RE.search(hay):
        return False
    return any(p.casefold() in hay for p in _PROMO_PHRASES)


def _is_cv_post(hay: str) -> bool:
    """True если: текст — CV / «ищу заказчиков» (не заказ, а резюме-фрилансера)."""
    if _CV_ANCHOR_RE.search(hay):
        return True
    return any(p.casefold() in hay for p in _CV_PHRASES)


# ── public API ────────────────────────────────────────────────────────────────


def is_tg_spam(title: str, body: str = "") -> bool:
    """True — прomo-бот реклама, CV фрилансера или партнёрка; не показывать в ленте."""
    if not title and not body:
        return False
    hay = _haystack(title, body)
    return _is_bot_promo(hay) or _is_cv_post(hay)


def tg_spam_lite_analysis(title: str, body: str = "") -> "AiLiteAnalysis | None":
    """Готовый L1-результат без OpenRouter, если TG-пост — спам/CV."""
    if not is_tg_spam(title, body):
        return None
    from ai_analyze import AiLiteAnalysis

    return AiLiteAnalysis(
        feed_visible=False,
        task_summary="TG-спам / CV фрилансера — не фриланс-заказ",
        lead_tags=(),
        ai_reasons=(
            "Promo-бот реклама, CV «ищу проект/заказчиков» или партнёрка",
            "Не является заказом фрилансера",
        ),
        complexity=1,
        primary_category="",
    )
