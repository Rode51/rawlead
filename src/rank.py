"""Персональный rank: keyword_match + final_rank (NEON_SCHEMA §3, O195 weighted)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

_RANK_WEIGHT_AI = float(os.getenv("RANK_WEIGHT_AI", "0.6"))
_RANK_WEIGHT_TAGS = float(os.getenv("RANK_WEIGHT_TAGS", "0.4"))
_DECAY_BASE = float(os.getenv("RANK_DECAY_BASE", "0.95"))
_DECAY_DAYS = float(os.getenv("RANK_DECAY_DAYS", "3"))
_DECAY_MIN_WEIGHT = float(os.getenv("RANK_DECAY_MIN_WEIGHT", "0.5"))
CX_PREF_TAG = "__cx_pref"
CX_MULTIPLIER_FLOOR = 0.80
CX_MULTIPLIER_STEP = 0.10  # per 1.0 distance in complexity units
EMPTY_PROFILE_KEYWORD_MATCH = 50
_LEAD_COVERAGE_REF_W = float(os.getenv("LEAD_COVERAGE_REF_W", "4.0"))

# O220-F: match-only synonym expansion on lead side (hidden from UI chips).
TAG_SYNONYMS: dict[str, tuple[str, ...]] = {
    "wordpress_dev": ("html_css", "php"),
    "python": ("api_integration",),
    "smm": ("content_marketing",),
    "ui_ux": ("figma", "brand_identity"),
    "video_editing": ("motion_design",),
    "seo": ("content_marketing", "article_writing"),
    "copywriting": ("content_marketing", "smm", "sales_copywriting"),
    "article_writing": ("technical_writing", "seo_copywriting", "seo"),
}


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


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def decay_factor(last_active_at: datetime | None, *, now: datetime | None = None) -> float:
    """O195: -5% каждые 3 дня неактивности по тегу."""
    ts = _as_utc(last_active_at)
    if ts is None:
        return 1.0
    ref = _as_utc(now) or datetime.now(timezone.utc)
    days = max(0, (ref - ts).days)
    return float(_DECAY_BASE ** (days / _DECAY_DAYS))


def effective_weight(weight: float, last_active_at: datetime | None) -> float | None:
    if weight <= 0:
        return None
    eff = weight * decay_factor(last_active_at)
    if eff < _DECAY_MIN_WEIGHT:
        return None
    return eff


def effective_user_tag_weights(rows: list[tuple[Any, ...]]) -> dict[str, float]:
    """Apply decay to DB rows: (tag, weight, last_active_at?)."""
    out: dict[str, float] = {}
    for row in rows:
        raw_tag = row[0]
        try:
            weight = float(row[1] if len(row) > 1 and row[1] is not None else 1.0)
        except (TypeError, ValueError):
            weight = 1.0
        last_active = row[2] if len(row) > 2 else None
        canonical = _resolve_canonical(str(raw_tag))
        if not canonical:
            t = str(raw_tag).strip().lower().lstrip("#")
            canonical = t or None
        if not canonical:
            continue
        eff = effective_weight(weight, last_active)
        if eff is not None:
            out[canonical] = eff
    return out


def _tag_matches_lead(user_tag: str, lead_set: set[str]) -> bool:
    from skills_catalog import expand_user_tags_for_match

    expanded = expand_user_tags_for_match({user_tag})
    return bool(expanded & lead_set)


def expand_lead_tags_for_match(lead_tags: list[str]) -> set[str]:
    """O220-F: canonical lead tags + TAG_SYNONYMS (match-only, not UI)."""
    canonical = _canonical_tag_list(lead_tags)
    expanded: set[str] = set(canonical)
    for tag in canonical:
        for syn in TAG_SYNONYMS.get(tag, ()):
            expanded.add(syn)
    return expanded


def _positive_user_tag_weights(user_tags: dict[str, float]) -> dict[str, float]:
    positive: dict[str, float] = {}
    for raw, weight in user_tags.items():
        if str(raw).startswith("__"):
            continue
        try:
            w = float(weight)
        except (TypeError, ValueError):
            continue
        if w <= 0:
            continue
        canonical = _resolve_canonical(str(raw))
        if not canonical:
            t = str(raw).strip().lower().lstrip("#")
            canonical = t or None
        if not canonical:
            continue
        positive[canonical] = max(positive.get(canonical, 0.0), w)
    return positive


def keyword_match(lead_tags: list[str], user_tags: dict[str, float]) -> int | None:
    """O195 weighted: Σ(weight×match)/Σ(weight)×100, cap 100; weight≤0 excluded."""
    lead_set = set(_canonical_tag_list(lead_tags))
    if not lead_set:
        return None
    if not user_tags:
        return 0

    positive = _positive_user_tag_weights(user_tags)
    if not positive:
        return 0

    weight_sum = sum(positive.values())
    if weight_sum <= 0:
        return 0

    matched_weight = 0.0
    for tag, w in positive.items():
        if _tag_matches_lead(tag, lead_set):
            matched_weight += w

    if matched_weight <= 0:
        return 0
    return min(100, round(100.0 * matched_weight / weight_sum))


def priority_keyword_match(lead_tags: list[str], user_tags: dict[str, float]) -> int | None:
    """O220-D: top-weight base + bonus for extra matches; lead synonyms O220-F."""
    lead_set = expand_lead_tags_for_match(lead_tags)
    if not lead_set:
        return None

    positive = _positive_user_tag_weights(user_tags)
    if not positive:
        return 0

    weight_sum = sum(positive.values())
    if weight_sum <= 0:
        return 0

    top_tag = max(positive, key=lambda tag: positive[tag])
    top_matched = _tag_matches_lead(top_tag, lead_set)
    score = 0.0

    if top_matched:
        score = 100.0 * positive[top_tag] / weight_sum
        for tag, w in positive.items():
            if tag != top_tag and _tag_matches_lead(tag, lead_set):
                score += 100.0 * w / weight_sum
    else:
        for tag, w in positive.items():
            if _tag_matches_lead(tag, lead_set):
                score += 100.0 * w / weight_sum

    if score <= 0:
        return 0
    return min(100, round(score))


def _lead_row_match_set(lead_tag: str) -> set[str]:
    row = {lead_tag}
    for syn in TAG_SYNONYMS.get(lead_tag, ()):
        row.add(syn)
    return row


def _best_user_weight_for_lead_row(
    lead_tag: str, positive: dict[str, float]
) -> float:
    """Direct user tag or TAG_SYNONYMS on lead row only (no parent expansion)."""
    lead_row = _lead_row_match_set(lead_tag)
    best = positive.get(lead_tag, 0.0)
    for user_tag, w in positive.items():
        if user_tag in lead_row:
            best = max(best, w)
    return best


def lead_coverage_match(lead_tags: list[str], user_tags: dict[str, float]) -> int | None:
    """O220-D: coverage over lead tags only; extra user skills do not lower score."""
    canonical_lead = _canonical_tag_list(lead_tags)
    if not canonical_lead:
        return None

    positive = _positive_user_tag_weights(user_tags)
    if not positive:
        return 0

    ref_w = _LEAD_COVERAGE_REF_W
    numerator = 0.0
    denominator = 0.0

    for lead_tag in canonical_lead:
        matched_w = _best_user_weight_for_lead_row(lead_tag, positive)
        direct_w = positive.get(lead_tag, 0.0)
        denominator += max(direct_w, ref_w)
        if matched_w > 0:
            numerator += matched_w

    if denominator <= 0:
        return 0
    if numerator <= 0:
        return 0
    return min(100, round(100.0 * numerator / denominator))


def keyword_match_breakdown(lead_tags: list[str], user_tags: dict[str, float]) -> dict[str, int]:
    """Для UI/API: matched/total user tags + weighted percent."""
    lead_set = set(_canonical_tag_list(lead_tags))
    positive = {
        tag: w
        for tag, w in user_tags.items()
        if isinstance(w, (int, float)) and float(w) > 0
    }
    km = keyword_match(lead_tags, user_tags)
    if not lead_set or not positive:
        return {"matched": 0, "total": len(positive), "percent": km if km is not None else 0}

    matched = 0
    for tag in positive:
        canonical = _resolve_canonical(str(tag)) or str(tag).strip().lower().lstrip("#")
        if canonical and _tag_matches_lead(canonical, lead_set):
            matched += 1
    return {
        "matched": matched,
        "total": len(positive),
        "percent": km if km is not None else 0,
    }


def complexity_multiplier(lead_cx: int | None, user_cx_pref: float) -> float:
    lead = float(lead_cx if lead_cx is not None else 2)
    pref = float(user_cx_pref if user_cx_pref else 2.0)
    delta = abs(lead - pref)
    return max(CX_MULTIPLIER_FLOOR, 1.0 - delta * CX_MULTIPLIER_STEP)


def cx_pref_from_user_tags(user_tags: dict[str, float] | None) -> float:
    if not user_tags:
        return 2.0
    try:
        return float(user_tags.get(CX_PREF_TAG, 2.0))
    except (TypeError, ValueError):
        return 2.0


def final_rank(
    ai_score: int | None,
    keyword_match_val: int,
    *,
    lead_complexity: int | None = None,
    user_cx_pref: float | None = None,
) -> int:
    ai = ai_score if ai_score is not None else 0
    base = ai * _RANK_WEIGHT_AI + keyword_match_val * _RANK_WEIGHT_TAGS
    cx_mult = complexity_multiplier(lead_complexity, user_cx_pref if user_cx_pref is not None else 2.0)
    return int(base * cx_mult)


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
