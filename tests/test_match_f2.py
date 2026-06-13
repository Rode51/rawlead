"""O42: keyword_match F2 — overlap / len(lead_tags), user cap 12."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from rank import keyword_match, tags_as_weights  # noqa: E402
from skills_catalog import _USER_MAX_TAGS, normalize_user_tags  # noqa: E402


class TestKeywordMatchF2(TestCase):
    def test_example_67_percent(self) -> None:
        lead = ["wordpress_dev", "php", "api_integration"]
        user = tags_as_weights(["wordpress_dev", "php", "javascript"])
        self.assertEqual(keyword_match(lead, user), 67)

    def test_all_lead_tags_matched_100(self) -> None:
        lead = ["wordpress", "php", "woocommerce"]
        user = tags_as_weights(["wordpress", "php", "woocommerce", "javascript", "python"])
        self.assertEqual(keyword_match(lead, user), 100)

    def test_extra_user_tags_do_not_penalize(self) -> None:
        lead = ["python", "php"]
        user = tags_as_weights(
            ["python", "php", "javascript", "wordpress_dev", "figma", "seo", "smm", "copywriting"]
        )
        self.assertEqual(keyword_match(lead, user), 100)

    def test_single_lead_tag_full_match(self) -> None:
        km = keyword_match(["python"], tags_as_weights(["python", "php"]))
        self.assertEqual(km, 100)

    def test_no_overlap(self) -> None:
        self.assertEqual(keyword_match(["python"], tags_as_weights(["figma"])), 0)

    def test_empty_user_tags(self) -> None:
        self.assertEqual(keyword_match(["python", "php"], {}), 0)

    def test_empty_lead_tags(self) -> None:
        self.assertEqual(keyword_match([], tags_as_weights(["python"])), 0)

    def test_partial_match_rounds(self) -> None:
        km = keyword_match(["a", "b", "c"], tags_as_weights(["a"]))
        self.assertGreater(km, 0)
        self.assertLessEqual(km, 60)


class TestUserTagsCap12(TestCase):
    def test_user_max_tags_constant(self) -> None:
        self.assertEqual(_USER_MAX_TAGS, 12)

    def test_normalize_truncates_at_12(self) -> None:
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
        self.assertEqual(len(out), 12)


if __name__ == "__main__":
    import unittest

    unittest.main()
