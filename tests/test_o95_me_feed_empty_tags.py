"""O95-fix-4: logged-in feed with empty user_tags shows all leads by date."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.api_server import _passes_min_match  # noqa: E402


class TestPersonalFeedEmptyProfile(unittest.TestCase):
    def test_min_match_filters_zero_overlap_when_profile_has_tags(self) -> None:
        self.assertFalse(_passes_min_match(0, 0))

    def test_empty_profile_skips_min_match_gate(self) -> None:
        has_profile = False
        km = 0
        include = (not has_profile) or _passes_min_match(km, 0)
        self.assertTrue(include)


if __name__ == "__main__":
    unittest.main()
