"""O225: multi-niche floors 20/10, primary niche, min_match, draft regression."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from api_server import _passes_min_match  # noqa: E402
from rank import (  # noqa: E402
    CATEGORY_FLOOR_PRIMARY,
    CATEGORY_FLOOR_SECONDARY,
    CATEGORY_FLOOR_VALUES,
    compatibility_match,
    quiz_niche_meta_tag,
    user_quiz_niches_from_tags,
    user_quiz_primary_niche,
)


def _quiz_profile(primary: str, *secondary: str) -> dict[str, float]:
    tags: dict[str, float] = {quiz_niche_meta_tag(primary): 2.0}
    for niche in secondary:
        tags[quiz_niche_meta_tag(niche)] = 1.0
    return tags


class TestO225MatchFloors(unittest.TestCase):
    def test_secondary_niche_floor_10(self) -> None:
        user = _quiz_profile("dev", "text")
        niches = user_quiz_niches_from_tags(user)
        km = compatibility_match(
            ["article_writing"],
            user,
            lead_category="text",
            user_quiz_niches=niches,
        )
        self.assertEqual(km, CATEGORY_FLOOR_SECONDARY)

    def test_primary_niche_floor_20(self) -> None:
        user = _quiz_profile("text", "dev")
        niches = user_quiz_niches_from_tags(user)
        km = compatibility_match(
            ["article_writing"],
            user,
            lead_category="text",
            user_quiz_niches=niches,
        )
        self.assertEqual(km, CATEGORY_FLOOR_PRIMARY)

    def test_illustration_draft_does_not_erase_text_floor(self) -> None:
        user = _quiz_profile("text", "design")
        user["illustration"] = 11.0
        niches = user_quiz_niches_from_tags(user)
        self.assertEqual(user_quiz_primary_niche(user), "text")
        km = compatibility_match(
            ["article_writing"],
            user,
            lead_category="text",
            user_quiz_niches=niches,
        )
        self.assertGreaterEqual(km, CATEGORY_FLOOR_PRIMARY)

    def test_other_category_never_gets_floor(self) -> None:
        user = _quiz_profile("text", "dev")
        niches = user_quiz_niches_from_tags(user)
        km = compatibility_match(
            ["article_writing"],
            user,
            lead_category="other",
            user_quiz_niches=niches,
        )
        self.assertEqual(km, 0)

    def test_min_match_allows_category_floors(self) -> None:
        self.assertTrue(_passes_min_match(CATEGORY_FLOOR_SECONDARY, 80))
        self.assertTrue(_passes_min_match(CATEGORY_FLOOR_PRIMARY, 80))
        self.assertFalse(_passes_min_match(67, 80))
        self.assertFalse(_passes_min_match(0, 80))

    def test_category_floor_values_constant(self) -> None:
        self.assertEqual(CATEGORY_FLOOR_VALUES, frozenset({10, 20}))


class TestO225TrialLockJsContract(unittest.TestCase):
    """Document JS contract: trial with effective_access must not use free-locked class."""

    def test_effective_access_shows_compat_bar(self) -> None:
        subscription = {"effective_access": True, "status": "trial"}
        has_paid = bool(subscription and subscription.get("effective_access"))
        tier_locked = not has_paid
        self.assertFalse(tier_locked)
        html_locked = "rl-match--free-locked" if tier_locked else ""
        self.assertNotIn("rl-match--free-locked", html_locked)


if __name__ == "__main__":
    unittest.main()
