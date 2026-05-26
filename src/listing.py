"""Общая модель карточки листинга (FL, Kwork, …)."""

from __future__ import annotations

from dataclasses import dataclass

SOURCE_FL = "fl"
SOURCE_KWORK = "kwork"
SOURCE_TELEGRAM = "telegram"
SOURCE_VC_RU = "vc_ru"
SOURCE_FREELANCEHUNT = "freelancehunt"
SOURCE_HABR_FREELANCE = "habr_freelance"
SOURCE_HABR_CAREER = "habr_career"


def telegram_source(chat_id: int) -> str:
    """Ключ дедупа в SQLite: один чат — свой source."""
    return f"tg:{chat_id}"


@dataclass(frozen=True)
class ListingProject:
    project_id: int
    title: str
    budget_text: str
    url: str
    published_at: str
    listing_snippet: str = ""
    source: str = SOURCE_FL
    listing_category: str = ""
    chat_invite_url: str = ""
    chat_title: str = ""
