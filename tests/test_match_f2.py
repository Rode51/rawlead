"""O195-w2: weighted keyword_match (was O42 F2 lead-coverage)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from rank import keyword_match, tags_as_weights  # noqa: E402
from skills_catalog import normalize_user_tags  # noqa: E402


class TestKeywordMatchWeighted(TestCase):
    def test_example_67_percent(self) -> None:
        lead = ["wordpress_dev", "php", "api_integration"]
        user = tags_as_weights(["wordpress_dev", "php", "javascript"])
        self.assertEqual(keyword_match(lead, user), 67)

    def test_matched_share_of_user_tags(self) -> None:
        lead = ["wordpress", "php", "woocommerce"]
        user = tags_as_weights(["wordpress", "php", "woocommerce", "javascript", "python"])
        self.assertEqual(keyword_match(lead, user), 60)

    def test_extra_user_tags_lower_percent(self) -> None:
        lead = ["python", "php"]
        user = tags_as_weights(
            ["python", "php", "javascript", "wordpress_dev", "figma", "seo", "smm", "copywriting"]
        )
        self.assertEqual(keyword_match(lead, user), 38)

    def test_single_matching_user_tag(self) -> None:
        km = keyword_match(["python"], tags_as_weights(["python", "php"]))
        self.assertEqual(km, 50)

    def test_no_overlap(self) -> None:
        self.assertEqual(keyword_match(["python"], tags_as_weights(["figma"])), 0)

    def test_empty_user_tags(self) -> None:
        self.assertEqual(keyword_match(["python", "php"], {}), 0)

    def test_empty_lead_tags(self) -> None:
        self.assertIsNone(keyword_match([], tags_as_weights(["python"])))

    def test_one_user_tag_covers_lead_via_expand(self) -> None:
        km = keyword_match(["a", "b", "c"], tags_as_weights(["a"]))
        self.assertEqual(km, 100)


class TestUserTagsNoCap(TestCase):
    def test_normalize_keeps_all_canonical_tags(self) -> None:
        tags = [
            "python",
            "javascript",
            "php",
            "wordpress_dev",
            "telegram_bot_dev",
            "api_integration",
            "figma",
            "ui_ux",
            "smm",
            "seo",
            "copywriting",
            "translation",
            "email_marketing",
        ]
        out = normalize_user_tags(tags)
        self.assertEqual(len(out), 13)


if __name__ == "__main__":
    import unittest

    unittest.main()
