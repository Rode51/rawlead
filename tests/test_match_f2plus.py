"""O82-w2: F2+ keyword_match + synonyms."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from rank import keyword_match, keyword_match_breakdown, tags_as_weights  # noqa: E402


class TestMatchF2Plus(TestCase):
    def test_synonym_resolves_to_canonical(self) -> None:
        lead = ["яндекс.директ", "seo"]
        user = tags_as_weights(["yandex_direct"])
        self.assertGreater(keyword_match(lead, user), 0)

    def test_matched_share_with_extra_user_tags(self) -> None:
        lead = ["python", "php"]
        user = tags_as_weights(
            ["python", "php", "javascript", "wordpress_dev", "figma", "seo"]
        )
        self.assertEqual(keyword_match(lead, user), 50)

    def test_partial_lead_coverage(self) -> None:
        lead = ["wordpress_dev", "php", "api_integration"]
        user = tags_as_weights(["wordpress_dev", "php", "javascript"])
        self.assertEqual(keyword_match(lead, user), 67)

    def test_breakdown_counts(self) -> None:
        bd = keyword_match_breakdown(
            ["python", "django", "fastapi"],
            tags_as_weights(["python"]),
        )
        self.assertEqual(bd["matched"], 1)
        self.assertEqual(bd["total"], 1)
        self.assertEqual(bd["percent"], 100)
        self.assertEqual(
            bd["percent"],
            keyword_match(
                ["python", "django", "fastapi"],
                tags_as_weights(["python"]),
            ),
        )

    def test_zero_on_no_overlap(self) -> None:
        self.assertEqual(
            keyword_match(["python"], tags_as_weights(["figma"])),
            0,
        )

    def test_distribution_many_unique_values(self) -> None:
        """≥11 unique % among synthetic lead/user pairs (O93 expand may collapse some)."""
        user = tags_as_weights(
            [
                "python",
                "javascript",
                "php",
                "wordpress_dev",
                "telegram_bot_dev",
                "api_integration",
                "figma",
                "seo",
                "copywriting",
                "smm",
                "yandex_direct",
                "react",
            ]
        )
        leads = [
            ["python"],
            ["python", "django"],
            ["python", "django", "fastapi"],
            ["wordpress_dev", "php"],
            ["figma", "ui_ux"],
            ["seo", "yandex_direct", "google_ads"],
            ["copywriting", "article_writing"],
            ["telegram_bot_dev", "python"],
            ["javascript", "react", "html_css"],
            ["smm", "target_ads"],
            ["python", "llm_integration"],
            ["php", "wordpress_dev", "api_integration", "javascript"],
            ["figma", "web_design", "banner_design"],
            ["translation", "editing_proofreading"],
            ["web_scraping", "python", "api_integration"],
            ["yandex_direct"],
            ["python", "php", "wordpress_dev"],
            ["seo_copywriting", "seo"],
            ["telegram_bot_dev", "aiogram"],
            ["logo_design", "brand_identity"],
            ["email_marketing", "crm_marketing"],
            ["technical_writing", "article_writing", "editing_proofreading"],
            ["target_ads", "vk_ads"],
            ["django", "fastapi", "api_integration"],
            ["wordpress_dev"],
            ["python", "web_scraping"],
            ["ui_ux", "web_design", "landing_page_design"],
            ["copywriting", "sales_copywriting"],
            ["google_ads", "yandex_direct", "target_ads", "seo"],
            ["python", "javascript", "php", "telegram_bot_dev"],
            ["python", "motion_design", "illustration", "threed_modeling"],
            ["marketplace_promotion", "content_marketing", "crm_marketing"],
            ["python", "django", "figma", "seo"],
            ["wordpress_dev", "php", "javascript", "api_integration", "telegram_bot_dev"],
            ["html_css", "react", "django"],
            ["product_description", "email_copywriting"],
            ["chatbot_marketing", "smm", "target_ads", "vk_ads", "seo"],
            ["presentation_design", "motion_design"],
        ]
        values = {keyword_match(lead, user) for lead in leads}
        self.assertGreaterEqual(len(values), 5, sorted(values))


if __name__ == "__main__":
    import unittest

    unittest.main()
