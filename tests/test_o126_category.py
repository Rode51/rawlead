"""O126: category filter = resolve_lead_category; hints / default other."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.lead_category import (  # noqa: E402
    OTHER_CATEGORY,
    infer_lead_category,
    resolve_lead_category,
)
from src.skills_catalog import lead_tags_for_feed  # noqa: E402


def _canonical_lead_tags(raw: Any) -> list[str]:
    slugs, _ = lead_tags_for_feed(raw)
    return slugs


def _row_resolved_category(row: tuple[Any, ...]) -> str:
    """Зеркало api_server._row_resolved_category (O126)."""
    tags = _canonical_lead_tags(row[8])
    return resolve_lead_category(row[11], row[2] or "", row[3] or "", tags)


def _passes_category_filter(row: tuple[Any, ...], categories: list[str]) -> bool:
    if not categories:
        return True
    return _row_resolved_category(row) in categories


def _feed_row(
    *,
    lead_id: int = 1,
    title: str = "",
    body: str = "",
    stored_category: str = "dev",
    lead_tags: list | None = None,
    ai_score: int = 80,
) -> tuple[Any, ...]:
    now = datetime.now(timezone.utc)
    tags_json = lead_tags or []
    return (
        lead_id,
        "fl",
        title,
        body,
        "https://example.com/p/1",
        "5000 ₽",
        ai_score,
        "OK",
        tags_json,
        None,
        now,
        stored_category,
        None,
        [],
        None,
    )


class TestO126LeadCategory(unittest.TestCase):
    def test_hint_tekst_not_dev(self) -> None:
        cat = infer_lead_category("Написать тексты для карточек", "SEO-тексты товаров", [])
        self.assertEqual(cat, "text")

    def test_score_zero_default_other(self) -> None:
        cat = infer_lead_category("Общий заказ без маркеров", "Описание проекта", [])
        self.assertEqual(cat, OTHER_CATEGORY)

    def test_resolve_stored_dev_inferred_text(self) -> None:
        resolved = resolve_lead_category(
            "dev",
            "Копирайтинг описаний",
            "Нужны тексты для маркетплейса",
            [],
        )
        self.assertEqual(resolved, "text")

    def test_resolve_stale_dev_no_hints_becomes_other(self) -> None:
        resolved = resolve_lead_category("dev", "Заказ на бирже", "Подробности в ЛС", [])
        self.assertEqual(resolved, OTHER_CATEGORY)

    def test_tie_break_text_over_dev(self) -> None:
        cat = infer_lead_category("Контент для API документации", "Написать контент", [])
        self.assertEqual(cat, "text")


class TestO126FeedCategoryFilter(unittest.TestCase):
    def test_passes_category_filter_uses_resolved_not_stored(self) -> None:
        row = _feed_row(
            stored_category="dev",
            title="Рерайт статей",
            body="Нужен рерайтинг 10 статей",
        )
        self.assertEqual(_row_resolved_category(row), "text")
        self.assertFalse(_passes_category_filter(row, ["dev"]))
        self.assertTrue(_passes_category_filter(row, ["text"]))

    def test_feed_dev_filter_excludes_resolved_text(self) -> None:
        """Зеркало _feed_page_time: category=dev → только resolved dev."""
        rows = [
            _feed_row(lead_id=1, stored_category="dev", title="Python скрипт", body="FastAPI"),
            _feed_row(
                lead_id=2,
                stored_category="dev",
                title="Тексты для сайта",
                body="Копирайтинг главной",
            ),
            _feed_row(lead_id=3, stored_category="dev", title="React frontend", body="Вёрстка"),
        ]
        items = [r for r in rows if _passes_category_filter(r, ["dev"])]
        cats = {_row_resolved_category(r) for r in items}
        self.assertNotIn("text", cats)
        self.assertTrue(all(c == "dev" for c in cats))
        self.assertEqual(len(items), 2)


if __name__ == "__main__":
    unittest.main()
