"""O97: ai_reasons JSONB — строки «почему» + опциональный complexity 1–4."""

from __future__ import annotations

import json
from typing import Any


def _clamp_complexity(value: Any) -> int | None:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    if n == 5:
        n = 4
    if 1 <= n <= 4:
        return n
    return None


def parse_ai_reasons_raw(raw: Any) -> tuple[list[str], int | None]:
    """Разбор Neon JSONB: legacy-массив или {reasons, complexity}."""
    if raw is None:
        return [], None
    if isinstance(raw, dict):
        reasons_raw = raw.get("reasons", raw.get("items"))
        complexity = _clamp_complexity(raw.get("complexity"))
        reasons: list[str] = []
        if isinstance(reasons_raw, list):
            reasons = [str(x).strip() for x in reasons_raw if str(x).strip()]
        return reasons, complexity
    if isinstance(raw, list):
        reasons = [str(x).strip() for x in raw if str(x).strip()]
        return reasons, None
    if isinstance(raw, str) and raw.strip():
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return [raw.strip()], None
        return parse_ai_reasons_raw(data)
    return [], None


def difficulty_from_ai_reasons(raw: Any) -> int | None:
    _, complexity = parse_ai_reasons_raw(raw)
    return complexity


def serialize_lite_ai_reasons(
    reasons: tuple[str, ...] | list[str],
    *,
    complexity: int = 0,
) -> str | None:
    """JSON для INSERT/UPDATE leads.ai_reasons."""
    rows = [str(r).strip() for r in reasons if str(r).strip()]
    c = _clamp_complexity(complexity)
    if not rows and c is None:
        return None
    if c is None:
        return json.dumps(rows, ensure_ascii=False)
    payload: dict[str, Any] = {"reasons": rows, "complexity": c}
    return json.dumps(payload, ensure_ascii=False)
