"""On-demand draft rate limit (O48 / O60b)."""

from __future__ import annotations

import os


def draft_hourly_limit() -> int:
    """DRAFT_HOURLY_LIMIT: 0 = без лимита · default 10 (O220 r1)."""
    raw = os.environ.get("DRAFT_HOURLY_LIMIT", "10").strip()
    try:
        n = int(raw)
    except ValueError:
        n = 0
    return max(0, n)


def draft_rate_limit_detail() -> str:
    lim = draft_hourly_limit()
    if lim <= 0:
        return ""
    return f"Лимит — {lim} черновиков в час. Попробуй позже."


def draft_warm_hourly_cap() -> int:
    """DRAFT_WARM_HOURLY_CAP: pre-warm on premium expand (default 30). 0 = без лимита."""
    raw = os.environ.get("DRAFT_WARM_HOURLY_CAP", "30").strip()
    try:
        n = int(raw)
    except ValueError:
        n = 30
    return max(0, n)
