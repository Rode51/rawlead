"""O72e-9: 4 canonical tags · hierarchical L1 · sanitize gate anchors."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import TestCase

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from ai_analyze import (  # noqa: E402
    _finalize_lite_analysis,
    _parse_lite_analysis,
    resolve_l1_primary_category,
    sanitize_l1_category,
    validate_l1_tags_for_category,
)
from skills_catalog import CANONICAL_TAGS, category_for_canonical_tag  # noqa: E402


class O72e9CatalogTagsTest(TestCase):
    def test_four_new_canonical_tags(self) -> None:
        for tag, cat in (
            ("server_administration", "dev"),
            ("technical_seo", "dev"),
            ("infographic_design", "design"),
            ("transcription", "text"),
        ):
            self.assertIn(tag, CANONICAL_TAGS)
            self.assertEqual(category_for_canonical_tag(tag), cat)


class O72e9HierarchicalParseTest(TestCase):
    def test_parse_primary_category_and_filter_tags(self) -> None:
        raw = {
            "primary_category": "dev",
            "feed_visible": True,
            "task_summary": "Настроить 3X-UI на VPS MacOS Ventura через SSH.",
            "lead_tags": ["server_administration", "illustration"],
            "ai_reasons": ["VPS", "3X-UI"],
        }
        lite = _parse_lite_analysis(raw)
        out = _finalize_lite_analysis(
            lite,
            title="Установка 3X-UI",
            snippet="Настройка панели на VPS Mac",
        )
        self.assertEqual(out.primary_category, "dev")
        self.assertIn("server_administration", out.lead_tags)
        self.assertNotIn("illustration", out.lead_tags)


class O72e9SanitizeCategoryTest(TestCase):
    def test_gate_anchor_categories(self) -> None:
        cases = [
            ("design", "Установка 3X-UI на VPS", "SSH MacOS 3X-UI", "dev"),
            ("dev", "Инфографика для WB", "карточки wildberries", "design"),
            ("design", "Тильда не в индексе", "Search Console robots sitemap", "dev"),
            ("design", "Трафик в телеграм бот", "привлечь пользователей реферал", "marketing"),
            ("dev", "Спрайты для игры", "нарисовать спрайты", "design"),
            ("design", "Транскрибация", "расшифровка аудио перевод", "text"),
        ]
        for stored, title, body, expected in cases:
            got = sanitize_l1_category(stored, title=title, snippet=body)
            self.assertEqual(got, expected, msg=title)

    def test_resolve_from_lite_tags_not_neon(self) -> None:
        cat = resolve_l1_primary_category(
            "design",
            ("infographic_design", "illustration"),
            title="Инфографика WB",
            snippet="wildberries карточки",
        )
        self.assertEqual(cat, "design")

    def test_validate_strips_cross_niche_tags(self) -> None:
        got = validate_l1_tags_for_category(
            ("server_administration", "smm"),
            "dev",
        )
        self.assertEqual(got, ("server_administration",))
