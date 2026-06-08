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
    @patch("src.api_server.keyword_match", return_value=82)
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
