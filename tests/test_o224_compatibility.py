"""O224: compatibility_match — category floor 20%, tag overlap unchanged."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from rank import (  # noqa: E402
    CATEGORY_FLOOR_MATCH,
    compatibility_match,
    lead_coverage_match,
    quiz_niche_meta_tag,
    tags_as_weights,
    user_quiz_niches_from_tags,
)


class TestO224CompatibilityMatch(unittest.TestCase):
    def test_full_tag_overlap_unchanged(self) -> None:
        user = {"python": 8.0, "fastapi": 4.0, "figma": 2.0, "copywriting": 2.0}
        lead = ["python", "fastapi"]
        cov = lead_coverage_match(lead, user)
        self.assertEqual(cov, 100)
        self.assertEqual(
            compatibility_match(lead, user, lead_category="dev"),
            cov,
        )

    def test_partial_overlap_unchanged(self) -> None:
        user = {"python": 8.0, "django": 4.0}
        lead = ["python", "fastapi"]
        cov = lead_coverage_match(lead, user)
        self.assertEqual(cov, 67)
        self.assertEqual(
            compatibility_match(lead, user, lead_category="dev"),
            cov,
        )

    def test_category_only_floor_20(self) -> None:
        user = {
            quiz_niche_meta_tag("dev"): 1.0,
        }
        niches = user_quiz_niches_from_tags(user)
        self.assertIn("dev", niches)
        km = compatibility_match(
            ["wordpress_dev"],
            user,
            lead_category="dev",
            user_quiz_niches=niches,
        )
        self.assertEqual(km, CATEGORY_FLOOR_MATCH)

    def test_quiz_niche_same_category_never_zero(self) -> None:
        user = tags_as_weights(["figma"])
        user[quiz_niche_meta_tag("design")] = 1.0
        niches = user_quiz_niches_from_tags(user)
        km = compatibility_match(
            ["seo"],
            user,
            lead_category="design",
            user_quiz_niches=niches,
        )
        self.assertEqual(km, CATEGORY_FLOOR_MATCH)

    def test_no_overlap_wrong_category_zero(self) -> None:
        user = {quiz_niche_meta_tag("dev"): 1.0}
        km = compatibility_match(
            ["figma"],
            user,
            lead_category="design",
            user_quiz_niches={"dev"},
        )
        self.assertEqual(km, 0)

    def test_empty_lead_tags_returns_none(self) -> None:
        user = tags_as_weights(["python"])
        self.assertIsNone(compatibility_match([], user, lead_category="dev"))


if __name__ == "__main__":
    unittest.main()
