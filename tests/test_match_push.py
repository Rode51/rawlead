"""O158: match push order dedup + lead detail keyword_match."""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

os.environ.setdefault("RAWLEAD_JWT_SECRET", "test-jwt-secret-o158")
os.environ.setdefault("RAWLEAD_API_KEY", "test-jwt-secret-o158")
os.environ["RADAR_PROFILE"] = "site"

from fastapi.testclient import TestClient  # noqa: E402

from src import api_server  # noqa: E402
from src.api_server import app  # noqa: E402
from src.jwt_auth import issue_access_token  # noqa: E402
from match_push import (  # noqa: E402
    _lite_from_lead_row,
    _normalize_order_url,
    _user_already_pushed_for_order,
)


class TestNormalizeOrderUrl(unittest.TestCase):
    def test_strips_query_and_trailing_slash(self) -> None:
        self.assertEqual(
            _normalize_order_url(
                "https://Freelance.ru/task/view/2245/?ref=1"
            ),
            "https://freelance.ru/task/view/2245",
        )

    def test_empty(self) -> None:
        self.assertEqual(_normalize_order_url(""), "")
        self.assertEqual(_normalize_order_url("   "), "")


class TestPushOrderDedup(unittest.TestCase):
    def test_by_source_external_id(self) -> None:
        cur = MagicMock()
        cur.fetchone.side_effect = [(1,), None]
        self.assertTrue(
            _user_already_pushed_for_order(
                cur,
                "00000000-0000-0000-0000-000000000001",
                source="freelance_ru",
                external_id="2245",
                order_url="",
            )
        )
        self.assertEqual(cur.execute.call_count, 1)

    def test_by_normalized_url_when_no_external_hit(self) -> None:
        cur = MagicMock()
        cur.fetchone.side_effect = [None, (1,)]
        url = "https://freelance.ru/task/view/2245"
        self.assertTrue(
            _user_already_pushed_for_order(
                cur,
                "00000000-0000-0000-0000-000000000001",
                source="freelance_ru",
                external_id="2245",
                order_url=url,
            )
        )
        self.assertEqual(cur.execute.call_count, 2)

    def test_not_sent(self) -> None:
        cur = MagicMock()
        cur.fetchone.side_effect = [None, None]
        self.assertFalse(
            _user_already_pushed_for_order(
                cur,
                "00000000-0000-0000-0000-000000000001",
                source="freelance_ru",
                external_id="9999",
                order_url="https://freelance.ru/task/view/9999",
            )
        )


class TestO200LiteFromLeadRow(unittest.TestCase):
    """O200-L2-CAT-80 t3: match_push primary_category from leads.category (row[11])."""

    def _sample_row(self, category: str | None) -> tuple:
        return (
            19954,
            "fl",
            "Title",
            "Body",
            "https://example.com/1",
            "10000",
            80,
            "Брать",
            '["python"]',
            "[]",
            None,
            category,
            "Summary",
            '["python"]',
            "",
        )

    def test_primary_category_from_row11(self) -> None:
        for cat in ("dev", "design", "marketing", "text"):
            with self.subTest(category=cat):
                lite = _lite_from_lead_row(self._sample_row(cat))
                self.assertEqual(lite.primary_category, cat)

    def test_other_or_empty_category_not_passed(self) -> None:
        for cat in ("other", None, ""):
            with self.subTest(category=cat):
                lite = _lite_from_lead_row(self._sample_row(cat))
                self.assertEqual(lite.primary_category, "")


def _sample_lead_row(lead_id: int = 42) -> tuple:
    return (
        lead_id,
        "freelance_ru",
        "Test task",
        "body",
        "https://freelance.ru/task/view/2245",
        "10 000 ₽",
        80,
        "ok",
        '["python", "django"]',
        "[]",
        datetime.now(timezone.utc),
        "dev",
        "summary",
        [],
        "",
    )


class TestGetLeadKeywordMatch(unittest.TestCase):
    def test_anon_no_keyword_match(self) -> None:
        row = _sample_lead_row()
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchone.return_value = row
        conn.cursor.return_value.__enter__.return_value = cur
        with patch.object(api_server, "psycopg") as mock_pg:
            mock_pg.connect.return_value.__enter__.return_value = conn
            client = TestClient(app)
            resp = client.get("/v1/leads/42")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsNone(data.get("keyword_match"))
        self.assertEqual(data.get("reply_draft"), "")

    @patch("src.api_server._attach_personal_replies")
    @patch("src.api_server.lead_coverage_match", return_value=82)
    def test_bearer_returns_keyword_match(
        self, _km: MagicMock, _attach: MagicMock
    ) -> None:
        row = _sample_lead_row()
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchone.return_value = row
        cur.fetchall.return_value = [("python",), ("django",)]
        conn.cursor.return_value.__enter__.return_value = cur
        token = issue_access_token(
            "00000000-0000-0000-0000-000000000099",
            tg_user_id=4242,
        )
        with patch.object(api_server, "psycopg") as mock_pg:
            mock_pg.connect.return_value.__enter__.return_value = conn
            client = TestClient(app)
            resp = client.get(
                "/v1/leads/42",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json().get("keyword_match"), 82)
        _attach.assert_called_once()


class TestKeywordMatchForUser(unittest.TestCase):
    def test_empty_profile_returns_zero_not_placeholder(self) -> None:
        from src.api_server import _keyword_match_for_user

        self.assertEqual(
            _keyword_match_for_user(["python"], {}, has_profile=False),
            0,
        )

    def test_profile_uses_real_match(self) -> None:
        from src.api_server import _keyword_match_for_user

        km = _keyword_match_for_user(
            ["python", "django"],
            {"python": 1.0},
            has_profile=True,
        )
        self.assertGreater(km, 0)
        self.assertLessEqual(km, 100)


class TestO220LeadCoverageMatch(unittest.TestCase):
    def test_empty_lead_tags_returns_none(self) -> None:
        from rank import keyword_match, lead_coverage_match, tags_as_weights

        user = tags_as_weights(["python"])
        self.assertIsNone(keyword_match([], user))
        self.assertIsNone(lead_coverage_match([], user))

    def test_full_lead_coverage_100(self) -> None:
        from rank import lead_coverage_match

        user = {"python": 8.0, "fastapi": 4.0, "figma": 2.0, "copywriting": 2.0}
        self.assertEqual(lead_coverage_match(["python", "fastapi"], user), 100)

    def test_partial_missing_lead_tag_67(self) -> None:
        from rank import lead_coverage_match

        user = {"python": 8.0, "django": 4.0}
        self.assertEqual(lead_coverage_match(["python", "fastapi"], user), 67)

    def test_half_weight_on_one_tag_50(self) -> None:
        from rank import lead_coverage_match

        user = {"python": 4.0}
        self.assertEqual(lead_coverage_match(["python", "fastapi"], user), 50)

    def test_no_overlap_returns_zero(self) -> None:
        from rank import lead_coverage_match

        user = {"figma": 6.0}
        self.assertEqual(lead_coverage_match(["python", "fastapi"], user), 0)

    def test_python_synonym_counts_as_coverage(self) -> None:
        from rank import lead_coverage_match

        user = {"api_integration": 8.0, "django": 1.0}
        km = lead_coverage_match(["python"], user)
        self.assertIsNotNone(km)
        assert km is not None
        self.assertGreaterEqual(km, 70)

    def test_quiz_import_weight_reaches_100_on_full_lead(self) -> None:
        from rank import lead_coverage_match

        user = {"smm": 4.0, "content_marketing": 4.0}
        self.assertEqual(lead_coverage_match(["smm", "content_marketing"], user), 100)

    def test_weight_one_caps_at_25(self) -> None:
        from rank import lead_coverage_match

        user = {"smm": 1.0, "content_marketing": 1.0}
        self.assertEqual(lead_coverage_match(["smm", "content_marketing"], user), 25)


class TestO220TagWeightCanonicalize(unittest.TestCase):
    def test_merge_preserves_max_weight(self) -> None:
        from src.api_server import _merge_user_tag_rows

        merged = _merge_user_tag_rows(
            [
                ("SMM", 4.0, None, 1),
                ("smm", 1.0, None, 2),
            ]
        )
        self.assertEqual(list(merged.keys()), ["smm"])
        self.assertEqual(merged["smm"][0], 4.0)

    def test_rewrite_needed_for_alias(self) -> None:
        from src.api_server import _merge_user_tag_rows, _user_tags_need_canonical_rewrite

        rows = [("SMM", 4.0, None, 1)]
        merged = _merge_user_tag_rows(rows)
        self.assertTrue(_user_tags_need_canonical_rewrite(rows, merged))


class TestO220PriorityMatch(unittest.TestCase):
    def test_empty_lead_tags_returns_none(self) -> None:
        from rank import keyword_match, priority_keyword_match, tags_as_weights

        user = tags_as_weights(["python"])
        self.assertIsNone(keyword_match([], user))
        self.assertIsNone(priority_keyword_match([], user))

    def test_python_dev_priority_match(self) -> None:
        from rank import priority_keyword_match

        user = {"python": 8.0, "django": 1.0, "javascript": 1.0}
        km = priority_keyword_match(["python"], user)
        self.assertIsNotNone(km)
        assert km is not None
        self.assertGreaterEqual(km, 70)
        self.assertLessEqual(km, 90)

    def test_python_synonym_via_api_integration(self) -> None:
        from rank import priority_keyword_match

        user = {"api_integration": 8.0, "django": 1.0}
        km = priority_keyword_match(["python"], user)
        self.assertIsNotNone(km)
        assert km is not None
        self.assertGreaterEqual(km, 70)

    def test_no_overlap_returns_zero(self) -> None:
        from rank import priority_keyword_match, tags_as_weights

        km = priority_keyword_match(["figma"], tags_as_weights(["python"]))
        self.assertEqual(km, 0)
