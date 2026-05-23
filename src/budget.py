"""Парсинг бюджета из текста карточки (уровень 3, до ИИ)."""

from __future__ import annotations

import re

_DIGITS = re.compile(r"\d+")


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
