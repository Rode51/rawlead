"""O72e-L2-r8: L1 complexity canon — assert COMPLEXITY block in _LITE_SYSTEM."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from ai_analyze import _LITE_SYSTEM  # noqa: E402


class TestL1ComplexityCanon(unittest.TestCase):
    def test_complexity_never_null_in_lite_system(self) -> None:
        """_LITE_SYSTEM содержит жёсткое правило «Никогда null»."""
        self.assertIn("Никогда null", _LITE_SYSTEM)

    def test_complexity_mandatory_json_in_lite_system(self) -> None:
        """_LITE_SYSTEM содержит «обязательно в каждом JSON»."""
        self.assertIn("обязательно в каждом JSON", _LITE_SYSTEM)

    def test_complexity_audit_anchors_present(self) -> None:
        """Якоря из аудита присутствуют в _LITE_SYSTEM."""
        self.assertIn("Google/YouTube Ads", _LITE_SYSTEM)
        self.assertIn("лидgen 4000 заявок", _LITE_SYSTEM)

    def test_complexity_design_vs_dev_anchor(self) -> None:
        """Правило design vs dev для макетов присутствует."""
        self.assertIn("design vs dev", _LITE_SYSTEM)
        self.assertIn("primary_category **design**, complexity **2**", _LITE_SYSTEM)


if __name__ == "__main__":
    unittest.main()
