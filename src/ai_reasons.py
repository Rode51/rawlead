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


def parse_tz_attachment_from_raw(raw: Any) -> dict[str, Any] | None:
    """O108: {status, filename, size_mb, reason} из ai_reasons JSONB."""
    if raw is None:
        return None
    if isinstance(raw, dict):
        tz = raw.get("tz_attachment")
        return tz if isinstance(tz, dict) else None
    if isinstance(raw, str) and raw.strip():
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return parse_tz_attachment_from_raw(data)
    return None


def merge_tz_attachment_into_reasons_json(
    reasons_json: str | None,
    tz: dict[str, Any] | None,
) -> str | None:
    if tz is None:
        return reasons_json
    payload: dict[str, Any]
    if reasons_json:
        try:
            data = json.loads(reasons_json)
        except json.JSONDecodeError:
            data = {"reasons": [reasons_json.strip()]}
        if isinstance(data, list):
            payload = {"reasons": data}
        elif isinstance(data, dict):
            payload = dict(data)
        else:
            payload = {}
    else:
        payload = {}
    payload["tz_attachment"] = tz
    return json.dumps(payload, ensure_ascii=False)
