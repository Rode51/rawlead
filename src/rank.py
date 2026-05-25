"""Персональный rank: keyword_match + final_rank (NEON_SCHEMA §3)."""

from __future__ import annotations

import os
from typing import Any

_RANK_WEIGHT_AI = float(os.getenv("RANK_WEIGHT_AI", "0.6"))
_RANK_WEIGHT_TAGS = float(os.getenv("RANK_WEIGHT_TAGS", "0.4"))


def normalize_tags(tags: list[str]) -> list[str]:
    """Lowercase, без #, уникальные, порядок сохраняется."""
    out: list[str] = []
    seen: set[str] = set()
    for raw in tags:
        t = str(raw).strip().lower().lstrip("#")
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def keyword_match(lead_tags: list[str], user_tags: dict[str, float]) -> int:
    """Weighted overlap → 0..100."""
    if not user_tags:
        return 0
    lead_set = {str(t).strip().lower() for t in lead_tags if t}
    matched = sum(w for tag, w in user_tags.items() if tag in lead_set)
    total = sum(user_tags.values())
    if total <= 0:
        return 0
    return min(100, round(matched / total * 100))


def final_rank(ai_score: int | None, keyword_match_val: int) -> int:
    ai = ai_score if ai_score is not None else 0
    return round(ai * _RANK_WEIGHT_AI + keyword_match_val * _RANK_WEIGHT_TAGS)


def open_rank(ai_score: int | None) -> int:
    """Открытая лента без user_tags (keyword_match = 0)."""
    return final_rank(ai_score, 0)


def parse_lead_tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return normalize_tags([str(t) for t in raw])
    return []


def tags_as_weights(tags: list[str]) -> dict[str, float]:
    """Равные веса для фильтра skills / user_tags."""
    return {t: 1.0 for t in normalize_tags(tags)}
