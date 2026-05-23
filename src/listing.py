"""Общая модель карточки листинга (FL, Kwork, …)."""

from __future__ import annotations

from dataclasses import dataclass

SOURCE_FL = "fl"
SOURCE_KWORK = "kwork"
SOURCE_TELEGRAM = "telegram"


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
    chat_invite_url: str = ""
    chat_title: str = ""
