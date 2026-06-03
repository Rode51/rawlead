"""Guard: AiLiteAnalysis must not be constructed with verdict= (property only)."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"


def _find_bad_calls() -> list[str]:
    bad: list[str] = []
    for path in sorted(_SRC.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = None
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name != "AiLiteAnalysis":
                continue
            for kw in node.keywords:
                if kw.arg == "verdict":
                    bad.append(f"{path.name}:{node.lineno}")
    return bad


class TestIngestAiLiteContract(unittest.TestCase):
    def test_no_verdict_kwarg_on_ai_lite_analysis(self) -> None:
        bad = _find_bad_calls()
        self.assertEqual(
            bad,
            [],
            "AiLiteAnalysis(verdict=...) breaks radar when ai_analyze uses feed_visible: "
            + ", ".join(bad),
        )


if __name__ == "__main__":
    unittest.main()
