"""O144-RFP-COMPLY: guard _rfp_defer_instead_of_ideas + промпт RFP в build_shared_l2_system."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from ai_analyze import _rfp_defer_instead_of_ideas, _shared_draft_too_vague
from l3_human_style import build_shared_l2_system


# ── Guard: _rfp_defer_instead_of_ideas ──────────────────────────────────────

_RFP_HORECA_DESC = (
    "Сеть ресторанов Уфа. Нужен SMM-специалист. "
    "Что приложить к отклику: 2-3 коротких идеи по домену HoReCa, кейсы с цифрами."
)

_BAD_DRAFT_DEFER = (
    "Здравствуйте! Чтобы подготовить 2–3 идеи, пришлите ссылки на ваши проекты "
    "и примеры текущего SMM."
)

_GOOD_DRAFT_IDEAS = (
    "Здравствуйте! Идея 1: гео-реклама и акции в Яндекс.Картах вокруг точек. "
    "Идея 2: реактивация спящей базы (SMS/push «вернись»). "
    "Идея 3: отзывы 4.8+ → блок «почему мы» на сайте брони. "
    "Кейсы HoReCa с цифрами — в диалоге. Подскажите, есть ли программа лояльности?"
)


def test_rfp_bad_defer_caught() -> None:
    """BAD: ТЗ требует идеи, draft отфутболивает «пришлите ссылки» → rfp_defer_links."""
    result = _rfp_defer_instead_of_ideas(_RFP_HORECA_DESC, _BAD_DRAFT_DEFER)
    assert result == "vague:rfp_defer_links"


def test_rfp_good_ideas_pass() -> None:
    """GOOD: draft содержит конкретные идеи → None."""
    result = _rfp_defer_instead_of_ideas(_RFP_HORECA_DESC, _GOOD_DRAFT_IDEAS)
    assert result is None


def test_rfp_no_tz_signal_no_false_positive() -> None:
    """ТЗ без RFP-сигнала + «пришлите ссылки на проекты» → не false-positive."""
    desc_no_rfp = "Нужен SMM. Бюджет 15 000 ₽/мес. Опыт в HoReCa приветствуется."
    draft_defer = "Здравствуйте! Пришлите ссылки на проекты, чтобы подготовить предложение."
    result = _rfp_defer_instead_of_ideas(desc_no_rfp, draft_defer)
    assert result is None


def test_rfp_vague_signal_variants() -> None:
    """Разные формулировки defer-паттерна срабатывают."""
    desc = "Что приложить к отклику: 2–3 идеи и кейсы с цифрами."
    for bad_draft in (
        "Здравствуйте! Вышлю в личке примеры работ и кейсы.",
        "Чтобы подготовить идеи — пришлите ваши проекты.",
        "Ссылки вышлю после согласования.",
        "Пришлите кейсы, тогда подготовлю предложение.",
    ):
        assert _rfp_defer_instead_of_ideas(desc, bad_draft) == "vague:rfp_defer_links", bad_draft


def test_shared_draft_too_vague_rfp_path() -> None:
    """_shared_draft_too_vague с description RFP-ТЗ и BAD draft → rfp_defer_links."""
    result = _shared_draft_too_vague(
        _BAD_DRAFT_DEFER,
        title="SMM для сети ресторанов Уфа",
        description=_RFP_HORECA_DESC,
    )
    assert result == "vague:rfp_defer_links"


def test_shared_draft_too_vague_good_pass() -> None:
    """GOOD draft с RFP-ТЗ → None."""
    result = _shared_draft_too_vague(
        _GOOD_DRAFT_IDEAS,
        title="SMM для сети ресторанов Уфа",
        description=_RFP_HORECA_DESC,
    )
    assert result is None


def test_shared_draft_too_vague_no_desc_no_fp() -> None:
    """Без description defer-паттерн в draft не даёт false-positive в guard."""
    result = _shared_draft_too_vague(
        "Пришлите ссылки на проекты.",
        title="SMM",
        description="",
    )
    assert result is None


# ── Промпт: build_shared_l2_system ──────────────────────────────────────────

def test_prompt_contains_rfp_section() -> None:
    """Промпт содержит блок RFP."""
    system = build_shared_l2_system()
    assert "RFP" in system or "что приложить к отклику" in system.casefold()


def test_prompt_contains_horeca_good_anchor() -> None:
    """Промпт содержит GOOD-пример с HoReCa идеями (гео-реклама / реактивация)."""
    system = build_shared_l2_system()
    low = system.casefold()
    assert "гео-реклам" in low or "реактивац" in low


def test_prompt_contains_rfp_bad_marker() -> None:
    """Промпт содержит BAD-паттерн «пришлите ссылки» как запрещённый."""
    system = build_shared_l2_system()
    assert "пришлите ссылки" in system.casefold() or "пришлите" in system.casefold()
