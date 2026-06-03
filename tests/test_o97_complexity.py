"""O97: L1 complexity 1–4 → ai_reasons JSONB → API difficulty."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from ai_analyze import _parse_lite_analysis  # noqa: E402
from ai_reasons import (  # noqa: E402
    difficulty_from_ai_reasons,
    parse_ai_reasons_raw,
    serialize_lite_ai_reasons,
)


class TestAiReasonsJson(unittest.TestCase):
    def test_legacy_array(self) -> None:
        raw = ["VPS", "3X-UI"]
        reasons, c = parse_ai_reasons_raw(raw)
        self.assertEqual(reasons, ["VPS", "3X-UI"])
        self.assertIsNone(c)
        self.assertIsNone(difficulty_from_ai_reasons(raw))

    def test_o97_object(self) -> None:
        raw = {"reasons": ["FastAPI", "Neon"], "complexity": 3}
        reasons, c = parse_ai_reasons_raw(raw)
        self.assertEqual(reasons, ["FastAPI", "Neon"])
        self.assertEqual(c, 3)
        self.assertEqual(difficulty_from_ai_reasons(raw), 3)

    def test_serialize_with_complexity(self) -> None:
        out = serialize_lite_ai_reasons(("a", "b"), complexity=2)
        self.assertIsNotNone(out)
        data = json.loads(out or "")
        self.assertEqual(data["complexity"], 2)
        self.assertEqual(data["reasons"], ["a", "b"])


class TestL1ParseComplexity(unittest.TestCase):
    def test_parse_complexity_field(self) -> None:
        lite = _parse_lite_analysis(
            {
                "primary_category": "dev",
                "feed_visible": True,
                "task_summary": "Скрипт на Python для выгрузки CSV.",
                "lead_tags": ["python"],
                "ai_reasons": ["Python", "CSV"],
                "complexity": 1,
            }
        )
        self.assertEqual(lite.complexity, 1)

    def test_legacy_five_maps_to_four(self) -> None:
        raw = {"reasons": ["spam"], "complexity": 5}
        _, c = parse_ai_reasons_raw(raw)
        self.assertEqual(c, 4)
        self.assertEqual(difficulty_from_ai_reasons(raw), 4)

    def test_invalid_complexity_zero(self) -> None:
        lite = _parse_lite_analysis(
            {
                "primary_category": "dev",
                "feed_visible": True,
                "task_summary": "API интеграция.",
                "lead_tags": ["python"],
                "ai_reasons": ["API"],
                "complexity": 9,
            }
        )
        self.assertEqual(lite.complexity, 2)

    def test_default_complexity_when_missing(self) -> None:
        lite = _parse_lite_analysis(
            {
                "primary_category": "dev",
                "feed_visible": True,
                "task_summary": "Парсер CSV.",
                "lead_tags": ["python"],
                "ai_reasons": ["Python"],
            }
        )
        self.assertEqual(lite.complexity, 2)

    def test_no_default_complexity_when_hidden(self) -> None:
        lite = _parse_lite_analysis(
            {
                "feed_visible": False,
                "task_summary": "",
                "lead_tags": [],
                "ai_reasons": ["спам"],
            }
        )
        self.assertEqual(lite.complexity, 0)


if __name__ == "__main__":
    unittest.main()
