"""O98: tools catalog aliases, TZ hints, finalize_tools_for_lead."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from tools_catalog import (  # noqa: E402
    finalize_tools_for_lead,
    is_known_tool,
    normalize_tools_required,
    tools_from_tz_text,
)


class TestToolsCatalogO98(unittest.TestCase):
    def test_alias_adobe_photoshop(self) -> None:
        out = normalize_tools_required(["adobe_photoshop", "figma"])
        self.assertIn("photoshop", out)
        self.assertIn("figma", out)
        self.assertTrue(all(is_known_tool(t) for t in out))

    def test_alias_google_sheets(self) -> None:
        out = normalize_tools_required(["google_sheets"])
        self.assertEqual(out, ("google_sheets_api",))

    def test_alias_wordpress(self) -> None:
        out = normalize_tools_required(["wordpress", "elementor"])
        self.assertIn("wordpress_dev", out)

    def test_tools_from_tz_text_wordpress(self) -> None:
        hints = tools_from_tz_text(
            "Доработка сайта",
            "Нужен WordPress + Elementor, правки на главной.",
        )
        self.assertIn("wordpress_dev", hints)

    def test_finalize_fills_from_tz_when_sparse(self) -> None:
        out = finalize_tools_for_lead(
            ("motion_design_software",),
            title="Презентация",
            snippet="Сделать презентацию в PowerPoint, 15 слайдов.",
            task_summary="Презентация PowerPoint",
        )
        self.assertGreaterEqual(len(out), 2)
        self.assertTrue(all(is_known_tool(t) for t in out))
        self.assertIn("powerpoint", out)

    def test_vendor_lock_stripped_by_normalize(self) -> None:
        out = normalize_tools_required(["neon", "python"])
        self.assertIn("python", out)
        self.assertNotIn("neon", out)

    def test_normalize_accepts_tuple(self) -> None:
        out = normalize_tools_required(("adobe_photoshop", "figma"))
        self.assertEqual(out, ("photoshop", "figma"))

    def test_consulting_stripped_without_consultation_markers(self) -> None:
        out = finalize_tools_for_lead(
            ("consulting", "seo", "excel"),
            title="Продвижение на Яндекс маркете",
            snippet="Настроить рекламу и карточки товаров.",
            task_summary="SEO и продвижение на маркетплейсе",
        )
        self.assertNotIn("consulting", out)
        self.assertGreaterEqual(len(out), 2)
        self.assertTrue(all(is_known_tool(t) for t in out))

    def test_rhino_stripped_on_chat_bot_gas(self) -> None:
        out = finalize_tools_for_lead(
            ("javascript", "google_apps_script", "rhino", "google_sheets_api"),
            title="Разработать чат бот, форма тренажер",
            snippet="Бот в Telegram, форма на Google Apps Script и таблица.",
            task_summary="Чат-бот + GAS + Google Таблица",
        )
        self.assertNotIn("rhino", out)
        self.assertIn("javascript", out)
        self.assertIn("google_apps_script", out)

    def test_cyrillic_slugs_dropped(self) -> None:
        out = normalize_tools_required(["макс", "массовая_рассылка", "javascript"])
        self.assertEqual(out, ("javascript",))

    def test_html_css_alias_to_javascript(self) -> None:
        out = normalize_tools_required(["html", "css", "php"])
        self.assertIn("javascript", out)
        self.assertIn("php", out)
        self.assertNotIn("html", out)
        self.assertNotIn("css", out)


if __name__ == "__main__":
    unittest.main()
