"""Парсинг бюджета из текста карточки (уровень 3, до ИИ)."""

from __future__ import annotations

import re

BUDGET_AGREED = "по договоренности"

_DIGITS = re.compile(r"\d+")
_BUDGET_PREFIX = re.compile(
    r"(?:бюджет|цен[аы]|стоимость|оплат[аы])\s*[:\-]?\s*"
    r"([\d][\d\s.,]*(?:\s*[-–—]\s*[\d][\d\s.,]*)?\s*(?:руб\.?|₽|р\.?|rub)?)",
    re.IGNORECASE,
)
_RUB_AMOUNT = re.compile(
    r"([\d][\d\s.,]*(?:\s*[-–—]\s*[\d][\d\s.,]*)?\s*(?:руб\.?|₽|р\.?\b|rub\b))",
    re.IGNORECASE,
)


def parse_budget_rub(budget_text: str) -> int | None:
    """
    Извлекает нижнюю оценку бюджета в рублях из строки листинга.
    «до 15 000 ₽» → 15000; «7 000 - 10 000» → 7000; не распознано → None.
    """
    raw = (budget_text or "").strip()
    if not raw:
        return None
    low = raw.casefold()
    if any(x in low for x in ("договор", "по договорен", "не указан", "бесплат")):
        return None

    chunks = re.split(r"[-–—]", raw)
    numbers: list[int] = []
    for chunk in chunks:
        digits = "".join(_DIGITS.findall(chunk))
        if not digits:
            continue
        try:
            numbers.append(int(digits))
        except ValueError:
            continue
    if not numbers:
        return None
    return min(numbers)


def meets_min_budget(budget_text: str, min_rub: int) -> bool:
    """True, если бюджет не распознан или ≥ порога (не отсекаем «договорную»)."""
    parsed = parse_budget_rub(budget_text)
    if parsed is None:
        return True
    return parsed >= min_rub


def _budget_fragment_from_line(line: str) -> str | None:
    for pattern in (_BUDGET_PREFIX, _RUB_AMOUNT):
        for match in pattern.finditer(line):
            fragment = match.group(1).strip()
            if parse_budget_rub(fragment) is not None:
                return fragment
    return None


def extract_budget_text_from_post(text: str) -> str:
    """Сумма из текста TG-поста; иначе BUDGET_AGREED (не пустая строка)."""
    raw = (text or "").strip()
    if not raw:
        return BUDGET_AGREED

    budget_keys = ("бюджет", "руб", "₽", "оплат", "цен", "стоим")
    for line in raw.splitlines():
        low = line.casefold()
        if any(key in low for key in budget_keys):
            fragment = _budget_fragment_from_line(line)
            if fragment:
                return fragment

    fragment = _budget_fragment_from_line(raw)
    if fragment:
        return fragment

    return BUDGET_AGREED


def display_budget_text(budget_text: str, *, is_telegram: bool) -> str:
    """Подпись бюджета в карточке и промпте ИИ."""
    value = (budget_text or "").strip()
    if value:
        return value
    return BUDGET_AGREED if is_telegram else "не указан"
