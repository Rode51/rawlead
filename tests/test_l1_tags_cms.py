"""O47: L1 lead_tags — CMS ≠ wordpress_dev (golden + post-validate)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from skills_catalog import sanitize_l1_cms_tags  # noqa: E402


_GOLDEN = (
    {
        "name": "joomla_captcha",
        "title": "Замена капчи на сайте Joomla",
        "snippet": "BaForms + SmartCaptcha Yandex, правка PHP-модуля формы",
        "input_tags": ("wordpress_dev", "php"),
        "expected": ("php",),
    },
    {
        "name": "wp_plugin",
        "title": "Разработка плагина WordPress",
        "snippet": "WooCommerce hooks, wp plugin для checkout",
        "input_tags": ("wordpress_dev", "php"),
        "expected": ("wordpress_dev", "php"),
    },
    {
        "name": "clean_api",
        "title": "REST API для приёма лидов",
        "snippet": "FastAPI webhook PostgreSQL, OpenAPI документация",
        "input_tags": ("python", "api_integration", "fastapi"),
        "expected": ("python", "api_integration", "fastapi"),
    },
    {
        "name": "tg_bot",
        "title": "Telegram-бот на Python",
        "snippet": "aiogram 3, парсинг каналов, PostgreSQL",
        "input_tags": ("telegram_bot_dev", "python"),
        "expected": ("telegram_bot_dev", "python"),
    },
    {
        "name": "tilda_turnkey",
        "title": "Сайт под ключ",
        "snippet": (
            "Нужен специалист по Tilda для интернет-магазина цифровых товаров. "
            "Zero Block, Tilda Commerce, корзина и ЮKassa."
        ),
        "input_tags": ("wordpress_dev", "html_css"),
        "expected": ("html_css", "tilda_dev"),
    },
    {
        "name": "tilda_zero_block",
        "title": "Сделать лендинг",
        "snippet": "Сверстать сайт на Тильде по макету, Zero Block, формы",
        "input_tags": ("wordpress_dev",),
        "expected": ("tilda_dev",),
    },
)


class SanitizeL1CmsTagsTest(TestCase):
    def test_golden_cases(self) -> None:
        for case in _GOLDEN:
            with self.subTest(case=case["name"]):
                got = sanitize_l1_cms_tags(
                    case["input_tags"],
                    title=case["title"],
                    snippet=case["snippet"],
                )
                self.assertEqual(got, case["expected"], case["name"])

    def test_joomla_strips_wordpress_adds_php_when_empty(self) -> None:
        got = sanitize_l1_cms_tags(
            ("wordpress_dev",),
            title="Joomla сайт",
            snippet="BaForms captcha",
        )
        self.assertEqual(got, ("php",))

    def test_bitrix24_strips_wordpress(self) -> None:
        got = sanitize_l1_cms_tags(
            ("wordpress_dev", "api_integration"),
            title="Webhook Bitrix24",
            snippet="REST интеграция CRM",
        )
        self.assertNotIn("wordpress_dev", got)
        self.assertIn("api_integration", got)

    def test_no_marker_keeps_wordpress_dev(self) -> None:
        got = sanitize_l1_cms_tags(
            ("wordpress_dev",),
            title="Правка темы WordPress",
            snippet="Elementor + custom plugin",
        )
        self.assertEqual(got, ("wordpress_dev",))
