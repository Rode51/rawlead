"""Дедуп одинаковых объявлений (один текст — одно уведомление)."""

from __future__ import annotations

import hashlib
import re

__all__ = ["listing_content_hash", "normalize_listing_text"]

_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_MENTION_RE = re.compile(r"@\w+")
_NON_WORD_RE = re.compile(r"[^\w\s]+", re.UNICODE)
_WS_RE = re.compile(r"\s+")


def normalize_listing_text(title: str, snippet: str = "") -> str:
    """Нормализация для сравнения: без URL, @, лишних пробелов."""
    raw = f"{(title or '').strip()}\n{(snippet or '').strip()}".casefold()
    raw = _URL_RE.sub(" ", raw)
    raw = _MENTION_RE.sub(" ", raw)
    raw = _NON_WORD_RE.sub(" ", raw)
    raw = _WS_RE.sub(" ", raw).strip()
    return raw[:2000]


def listing_content_hash(title: str, snippet: str = "") -> str:
    norm = normalize_listing_text(title, snippet)
    if not norm:
        return ""
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:32]
