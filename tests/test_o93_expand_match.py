"""O93: parent → children expand in keyword_match."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from rank import keyword_match, tags_as_weights  # noqa: E402
from skills_catalog import EXPAND_MAP, expand_user_tags_for_match  # noqa: E402


class TestO93ExpandMatch(TestCase):
    def test_expand_map_includes_parent(self) -> None:
        for parent, children in EXPAND_MAP.items():
            self.assertIn(parent, children)

    def test_expand_user_tags_telegram_bot_dev(self) -> None:
        expanded = expand_user_tags_for_match({"telegram_bot_dev"})
        self.assertIn("aiogram", expanded)
        self.assertIn("telethon", expanded)

    def test_telegram_bot_dev_matches_aiogram_lead(self) -> None:
        user = tags_as_weights(["telegram_bot_dev"])
        self.assertGreater(keyword_match(["aiogram"], user), 0)

    def test_python_matches_django_lead(self) -> None:
        user = tags_as_weights(["python"])
        self.assertGreater(keyword_match(["django"], user), 0)

    def test_l3_only_selection_matches_exact(self) -> None:
        user = tags_as_weights(["django"])
        self.assertGreater(keyword_match(["django"], user), 0)
        self.assertEqual(keyword_match(["fastapi"], user), 0)

    def test_unknown_tag_no_expand(self) -> None:
        expanded = expand_user_tags_for_match({"figma"})
        self.assertEqual(expanded, {"figma"})

    def test_python_expands_flask_scrapy(self) -> None:
        expanded = expand_user_tags_for_match({"python"})
        self.assertIn("flask", expanded)
        self.assertIn("scrapy", expanded)

    def test_mobile_dev_expands_react_native(self) -> None:
        expanded = expand_user_tags_for_match({"mobile_dev"})
        self.assertIn("react_native", expanded)
        self.assertIn("flutter", expanded)

    def test_seo_expands_technical_seo(self) -> None:
        expanded = expand_user_tags_for_match({"seo"})
        self.assertIn("technical_seo", expanded)

    def test_typescript_expands_javascript(self) -> None:
        expanded = expand_user_tags_for_match({"typescript"})
        self.assertIn("javascript", expanded)

    def test_flask_lead_matches_python_user(self) -> None:
        user = tags_as_weights(["python"])
        self.assertGreater(keyword_match(["flask"], user), 0)
