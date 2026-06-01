"""O63: парсеры бирж (w1 YouDo/Freelance.ru · w2 FreelanceJob/Пчёл) и cross-source dedup."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from freelance_ru_parser import parse_listing_html as parse_freelance_ru  # noqa: E402
from freelancejob_parser import parse_listing_html as parse_freelancejob  # noqa: E402
from listing import (  # noqa: E402
    SOURCE_FREELANCE_RU,
    SOURCE_FREELANCEJOB,
    SOURCE_PCHYOL,
    SOURCE_YOUDO,
    ListingProject,
)
from listing_dedup import listing_content_hash  # noqa: E402
from pchyol_parser import parse_listing_html as parse_pchyol  # noqa: E402
from youdo_parser import parse_listing_html as parse_youdo  # noqa: E402

_FIXTURES = Path(__file__).resolve().parent / "fixtures"


class TestO63Parsers(unittest.TestCase):
    def test_freelance_ru_parse_fixture(self) -> None:
        html = (_FIXTURES / "o63_freelance_ru_listing.html").read_text(encoding="utf-8")
        projects = parse_freelance_ru(html, "https://freelance.ru/project/search")
        self.assertEqual(len(projects), 1)
        p = projects[0]
        self.assertEqual(p.project_id, 12345)
        self.assertEqual(p.source, SOURCE_FREELANCE_RU)
        self.assertIn("WordPress", p.title)
        self.assertIn("лендинг", p.listing_snippet)
        self.assertIn("25 000", p.budget_text)

    def test_youdo_parse_fixture(self) -> None:
        html = (_FIXTURES / "o63_youdo_listing.html").read_text(encoding="utf-8")
        projects = parse_youdo(html, "https://youdo.com/tasks-all-opened-all")
        self.assertEqual(len(projects), 1)
        p = projects[0]
        self.assertEqual(p.project_id, 99001)
        self.assertEqual(p.source, SOURCE_YOUDO)
        self.assertEqual(p.url, "https://youdo.com/t99001")
        self.assertIn("WordPress", p.listing_snippet)
        self.assertIn("15 000", p.budget_text)

    def test_cross_source_dedup_same_text(self) -> None:
        title = "Разработка сайта на WordPress"
        snippet = "Нужен лендинг с формой заявки до 25 000 ₽ на FL.ru"
        h_fl = listing_content_hash(title, snippet)
        h_youdo = listing_content_hash(
            title,
            "Нужен лендинг с формой заявки до 25 000 ₽ на YouDo",
        )
        self.assertEqual(h_fl, h_youdo)
        self.assertTrue(h_fl)

    def test_cross_source_dedup_brand_noise_stripped(self) -> None:
        a = listing_content_hash("Задача", "Текст с FL.ru и kwork в описании")
        b = listing_content_hash("Задача", "Текст с youdo и freelance.ru в описании")
        self.assertEqual(a, b)

    def test_freelancejob_parse_fixture(self) -> None:
        html = (_FIXTURES / "o63_freelancejob_listing.html").read_text(encoding="utf-8")
        projects = parse_freelancejob(html, "https://www.freelancejob.ru/projects/")
        self.assertEqual(len(projects), 1)
        p = projects[0]
        self.assertEqual(p.project_id, 77001)
        self.assertEqual(p.source, SOURCE_FREELANCEJOB)
        self.assertIn("WordPress", p.title)
        self.assertIn("30 000", p.budget_text)

    def test_pchyol_parse_fixture_skips_closed(self) -> None:
        html = (_FIXTURES / "o63_pchyol_listing_smoke.html").read_text(encoding="utf-8")
        projects = parse_pchyol(html, "https://pchel.net/jobs/?sort=date_desc")
        self.assertEqual(len(projects), 1)
        p = projects[0]
        self.assertEqual(p.project_id, 1626001)
        self.assertEqual(p.source, SOURCE_PCHYOL)
        self.assertIn("WordPress", p.title)
        self.assertIn("Пчёл", p.listing_snippet)

    def test_pchyol_filter_skips_at_or_below_floor(self) -> None:
        from pchyol_parser import filter_new_pchyol_projects  # noqa: E402

        class _FakeStorage:
            def max_project_id(self, source: str) -> int:
                assert source == SOURCE_PCHYOL
                return 1626000

        storage = _FakeStorage()
        projects = [
            ListingProject(
                project_id=1626001,
                title="New",
                budget_text="",
                url="https://pchel.net/jobs/x/1/",
                published_at="",
                listing_snippet="New",
                source=SOURCE_PCHYOL,
            ),
            ListingProject(
                project_id=1626000,
                title="Old",
                budget_text="",
                url="https://pchel.net/jobs/x/0/",
                published_at="",
                listing_snippet="Old",
                source=SOURCE_PCHYOL,
            ),
        ]
        kept = filter_new_pchyol_projects(projects, storage)
        self.assertEqual([p.project_id for p in kept], [1626001])


if __name__ == "__main__":
    unittest.main()
