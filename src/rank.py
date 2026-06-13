"""Персональный rank: keyword_match + final_rank (NEON_SCHEMA §3)."""

from __future__ import annotations

import os
from typing import Any

_RANK_WEIGHT_AI = float(os.getenv("RANK_WEIGHT_AI", "0.6"))
_RANK_WEIGHT_TAGS = float(os.getenv("RANK_WEIGHT_TAGS", "0.4"))
_RANK_MATCH_LEAD_WEIGHT = float(os.getenv("RANK_MATCH_LEAD_WEIGHT", "0.65"))
_RANK_MATCH_USER_WEIGHT = float(os.getenv("RANK_MATCH_USER_WEIGHT", "0.35"))
_USER_TAG_CAP = int(os.getenv("RANK_MATCH_USER_CAP", "6"))


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


def _resolve_canonical(raw: str) -> str | None:
    from skills_catalog import resolve_canonical_tag

    return resolve_canonical_tag(raw)


def _canonical_tag_list(tags: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in tags:
        canonical = _resolve_canonical(raw)
        if not canonical:
            t = str(raw).strip().lower().lstrip("#")
            canonical = t or None
        if not canonical or canonical in seen:
            continue
        seen.add(canonical)
        out.append(canonical)
    return out


def _canonical_user_keys(user_tags: dict[str, float]) -> set[str]:
    keys: set[str] = set()
    for raw in user_tags:
        canonical = _resolve_canonical(str(raw))
        if not canonical:
            t = str(raw).strip().lower().lstrip("#")
            canonical = t or None
        if canonical:
            keys.add(canonical)
    return keys


def _expanded_user_keys(user_tags: dict[str, float]) -> set[str]:
    from skills_catalog import expand_user_tags_for_match

    return expand_user_tags_for_match(_canonical_user_keys(user_tags))


def keyword_match(lead_tags: list[str], user_tags: dict[str, float]) -> int:
    """Lead-coverage %: matched lead tags / all lead tags (O185 t4)."""
    from skills_catalog import expand_user_tags_for_match

    lead_set = _canonical_tag_list(lead_tags)
    if not lead_set or not user_tags:
        return 0
    user_base = _canonical_user_keys(user_tags)
    if not user_base:
        return 0
    user_expanded = expand_user_tags_for_match(user_base)
    matched = sum(1 for tag in lead_set if tag in user_expanded)
    if matched <= 0:
        return 0
    return min(100, round(100.0 * matched / len(lead_set)))


def keyword_match_breakdown(lead_tags: list[str], user_tags: dict[str, float]) -> dict[str, int]:
    """Для UI/API: matched/total lead tags + percent."""
    from skills_catalog import expand_user_tags_for_match

    lead_set = _canonical_tag_list(lead_tags)
    if not lead_set or not user_tags:
        return {"matched": 0, "total": len(lead_set), "percent": 0}
    user_base = _canonical_user_keys(user_tags)
    user_expanded = expand_user_tags_for_match(user_base)
    matched = sum(1 for tag in lead_set if tag in user_expanded)
    return {
        "matched": matched,
        "total": len(lead_set),
        "percent": keyword_match(lead_tags, user_tags),
    }


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
    out: dict[str, float] = {}
    for t in _canonical_tag_list(normalize_tags(tags)):
        out[t] = 1.0
    return out
