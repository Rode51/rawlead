"""Общая модель карточки листинга (FL, Kwork, …)."""

from __future__ import annotations

from dataclasses import dataclass

SOURCE_FL = "fl"
SOURCE_KWORK = "kwork"
SOURCE_YOUDO = "youdo"
SOURCE_FREELANCE_RU = "freelance_ru"
SOURCE_FREELANCEJOB = "freelancejob"
SOURCE_PCHYOL = "pchyol"
SOURCE_TELEGRAM = "telegram"
SOURCE_VC_RU = "vc_ru"
SOURCE_FREELANCEHUNT = "freelancehunt"
SOURCE_HABR_CAREER = "habr_career"


def canonical_tg_peer(chat_id: int) -> int:
    """Supergroup/channel peer как в PUBLIC_FEED_SOURCES (tg:-100…)."""
    cid = int(chat_id)
    s = str(cid)
    if s.startswith("-100"):
        return cid
    if cid < 0:
        return int(f"-100{abs(cid)}")
    return int(f"-100{cid}")


def telegram_source(chat_id: int) -> str:
    """Ключ дедупа в SQLite / Neon: один чат — канонический tg:-100… peer."""
    return f"tg:{canonical_tg_peer(chat_id)}"


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
