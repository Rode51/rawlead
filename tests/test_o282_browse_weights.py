"""O282-A: browse without expand_no_reply penalty — weights stay ≥ quiz baseline."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

os.environ.setdefault("RAWLEAD_JWT_SECRET", "test-jwt-secret-o282")
os.environ.setdefault("RAWLEAD_API_KEY", "test-jwt-secret-o282")
os.environ["RADAR_PROFILE"] = "site"

from src.api_server import (  # noqa: E402
    _TAG_WEIGHT_MAX,
    _TAG_WEIGHT_MIN,
    _WEIGHT_EVENT_SPECS,
    _apply_tag_weight_event,
    _replace_quiz_import_user_tags,
)

_FEED_JS = _ROOT / "wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js"
_CABINET_JS = _ROOT / "wordpress/rawlead-kadence-child/assets/js/rawlead-cabinet.js"

_QUIZ_BASELINE = {
    "python": 4.0,
    "fastapi": 3.5,
    "django": 3.0,
    "api_integration": 2.5,
}


class _TagRow:
    __slots__ = ("weight", "interaction_count", "last_active_at")

    def __init__(
        self,
        weight: float = 0.0,
        interaction_count: int = 0,
        last_active_at: object | None = "now",
    ) -> None:
        self.weight = weight
        self.interaction_count = interaction_count
        self.last_active_at = last_active_at


class InMemoryUserTagsCursor:
    """Minimal user_tags store for weight_delta + quiz import tests."""

    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], _TagRow] = {}

    def execute(self, sql: str, params: tuple[Any, ...]) -> None:
        normalized = " ".join(sql.split())
        if normalized.startswith("DELETE FROM user_tags"):
            user_id = str(params[0])
            for key in list(self.rows):
                if key[0] == user_id:
                    del self.rows[key]
            return

        if "INSERT INTO user_tags" not in normalized:
            return

        user_id = str(params[0])
        tag = str(params[1])
        key = (user_id, tag)

        if len(params) == 9:
            delta = float(params[6])
            interaction_delta = int(params[7])
            start_weight = float(params[2]) if delta > 0 else 0.0
            existing = self.rows.get(key)
            if existing is None:
                self.rows[key] = _TagRow(
                    weight=start_weight,
                    interaction_count=max(0, interaction_delta),
                )
            else:
                existing.weight = max(
                    _TAG_WEIGHT_MIN,
                    min(_TAG_WEIGHT_MAX, existing.weight + delta),
                )
                existing.interaction_count += interaction_delta
            return

        if len(params) == 3:
            weight = float(params[2])
            interaction = 0 if ", 0)" in normalized.split("VALUES")[-1][:40] else 1
            self.rows[key] = _TagRow(weight=weight, interaction_count=interaction)
            return


def _quiz_import(cur: InMemoryUserTagsCursor, user_id: str) -> None:
    _replace_quiz_import_user_tags(cur, user_id, dict(_QUIZ_BASELINE), ["dev"])


def _skill_weights(cur: InMemoryUserTagsCursor, user_id: str) -> dict[str, float]:
    return {
        tag: row.weight
        for (uid, tag), row in cur.rows.items()
        if uid == user_id and not tag.startswith("__")
    }


class TestO282ExpandNoReplyRemoved(unittest.TestCase):
    def test_specs_exclude_expand_no_reply(self) -> None:
        self.assertNotIn("expand_no_reply", _WEIGHT_EVENT_SPECS)

    def test_js_has_no_expand_no_reply(self) -> None:
        for path in (_FEED_JS, _CABINET_JS):
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("expand_no_reply", text)


class TestO282BrowseWeights(unittest.TestCase):
    def test_fifteen_expands_do_not_lower_quiz_weights(self) -> None:
        user_id = "00000000-0000-0000-0000-000000000282"
        cur = InMemoryUserTagsCursor()
        _quiz_import(cur, user_id)
        baseline = _skill_weights(cur, user_id)
        self.assertTrue(baseline)

        expand_tags = [
            ["python"],
            ["fastapi"],
            ["django"],
            ["python", "api_integration"],
            ["fastapi"],
            ["django"],
            ["python"],
            ["api_integration"],
            ["fastapi", "python"],
            ["django"],
            ["python"],
            ["fastapi"],
            ["django"],
            ["api_integration"],
            ["python"],
        ]
        for tags in expand_tags:
            _apply_tag_weight_event(cur, user_id, "expand", tags)

        after = _skill_weights(cur, user_id)
        for tag, base_w in baseline.items():
            self.assertGreaterEqual(
                after.get(tag, 0.0),
                base_w,
                f"{tag}: {after.get(tag)} < baseline {base_w}",
            )

    def test_push_nope_lowers_tag_weight(self) -> None:
        user_id = "00000000-0000-0000-0000-000000000283"
        cur = InMemoryUserTagsCursor()
        _quiz_import(cur, user_id)
        before = _skill_weights(cur, user_id)["python"]

        for _ in range(3):
            _apply_tag_weight_event(cur, user_id, "push_nope", ["python"])

        after = _skill_weights(cur, user_id)["python"]
        self.assertLess(after, before)


if __name__ == "__main__":
    unittest.main()
