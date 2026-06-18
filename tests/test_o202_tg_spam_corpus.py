"""O202: TG spam corpus — API + mark/hide + filter regression."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

os.environ.setdefault("RAWLEAD_JWT_SECRET", "test-jwt-secret-o202")
os.environ.setdefault("RAWLEAD_API_KEY", "test-jwt-secret-o202")
os.environ["RADAR_PROFILE"] = "site"

from src import api_server  # noqa: E402
from src.jwt_auth import issue_access_token  # noqa: E402
from src.tg_spam_corpus import (  # noqa: E402
    chat_id_from_tg_source,
    mark_tg_lead_spam,
)
from src.tg_spam_filter import is_tg_spam  # noqa: E402

_OWNER_ID = "00000000-0000-0000-0000-000000000001"
_DB = "postgresql://test:test@127.0.0.1:5432/test"
_OWNER_TOKEN = issue_access_token(_OWNER_ID, tg_user_id=1)


class TestChatIdFromTgSource(unittest.TestCase):
    def test_peer_negative(self) -> None:
        self.assertEqual(chat_id_from_tg_source("tg:-1001234567890"), -1001234567890)

    def test_non_tg(self) -> None:
        self.assertIsNone(chat_id_from_tg_source("fl"))
        self.assertIsNone(chat_id_from_tg_source("tg:abc"))


class TestMarkTgLeadSpam(unittest.TestCase):
    @patch("src.tg_spam_corpus.psycopg.connect")
    def test_rejects_non_tg(self, mock_connect: MagicMock) -> None:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_cur.fetchone.return_value = ("fl", "t", "b", True)

        with self.assertRaises(ValueError):
            mark_tg_lead_spam(_DB, 1, _OWNER_ID)

    @patch("src.tg_spam_corpus.psycopg.connect")
    def test_marks_and_hides(self, mock_connect: MagicMock) -> None:
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_cur.fetchone.return_value = (
            "tg:-100999",
            "Реклама услуг",
            "Мы предлагаем SEO под ключ",
            True,
        )
        mock_cur.rowcount = 1

        out = mark_tg_lead_spam(_DB, 42, _OWNER_ID, category="ad_services")
        self.assertEqual(out, {"ok": True, "lead_id": 42})
        executed = [call[0][0] for call in mock_cur.execute.call_args_list]
        self.assertTrue(any("INSERT INTO tg_spam_corpus" in sql for sql in executed))
        update_calls = [
            call for call in mock_cur.execute.call_args_list if "delist_reason" in call[0][0]
        ]
        self.assertEqual(len(update_calls), 1)
        self.assertEqual(update_calls[0][0][1][0], "owner_tg_spam")


class TestTgSpamApi(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(api_server.app)

    @patch.object(api_server, "psycopg")
    @patch.object(api_server, "is_owner_db_user", return_value=False)
    @patch.object(api_server, "_db_url", return_value=_DB)
    def test_forbidden_for_non_owner(
        self, _db: MagicMock, _owner: MagicMock, mock_pg: MagicMock
    ) -> None:
        conn = MagicMock()
        mock_pg.connect.return_value.__enter__.return_value = conn
        conn.cursor.return_value.__enter__.return_value = MagicMock()
        resp = self.client.post(
            "/v1/admin/leads/1/tg-spam",
            headers={"Authorization": f"Bearer {_OWNER_TOKEN}"},
        )
        self.assertEqual(resp.status_code, 403)

    @patch.object(api_server, "mark_tg_lead_spam", return_value={"ok": True, "lead_id": 7})
    @patch.object(api_server, "psycopg")
    @patch.object(api_server, "is_owner_db_user", return_value=True)
    @patch.object(api_server, "_db_url", return_value=_DB)
    def test_owner_ok(
        self,
        _db: MagicMock,
        _owner: MagicMock,
        mock_pg: MagicMock,
        mock_mark: MagicMock,
    ) -> None:
        conn = MagicMock()
        mock_pg.connect.return_value.__enter__.return_value = conn
        conn.cursor.return_value.__enter__.return_value = MagicMock()
        resp = self.client.post(
            "/v1/admin/leads/7/tg-spam",
            json={"category": "ad_services"},
            headers={"Authorization": f"Bearer {_OWNER_TOKEN}"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"ok": True, "lead_id": 7})
        mock_mark.assert_called_once()

    @patch.object(api_server, "mark_tg_lead_spam", side_effect=ValueError("not a TG lead"))
    @patch.object(api_server, "psycopg")
    @patch.object(api_server, "is_owner_db_user", return_value=True)
    @patch.object(api_server, "_db_url", return_value=_DB)
    def test_non_tg_400(
        self,
        _db: MagicMock,
        _owner: MagicMock,
        mock_pg: MagicMock,
        _mark: MagicMock,
    ) -> None:
        conn = MagicMock()
        mock_pg.connect.return_value.__enter__.return_value = conn
        conn.cursor.return_value.__enter__.return_value = MagicMock()
        resp = self.client.post(
            "/v1/admin/leads/3/tg-spam",
            headers={"Authorization": f"Bearer {_OWNER_TOKEN}"},
        )
        self.assertEqual(resp.status_code, 400)

    @patch.object(api_server, "mark_tg_lead_spam", return_value={"ok": True, "lead_id": 9})
    @patch.object(api_server, "psycopg")
    @patch.object(api_server, "is_owner_db_user", return_value=True)
    @patch.object(api_server, "_db_url", return_value=_DB)
    def test_owner_rejects_json_array_body(
        self,
        _db: MagicMock,
        _owner: MagicMock,
        mock_pg: MagicMock,
        mock_mark: MagicMock,
    ) -> None:
        conn = MagicMock()
        mock_pg.connect.return_value.__enter__.return_value = conn
        conn.cursor.return_value.__enter__.return_value = MagicMock()
        resp = self.client.post(
            "/v1/admin/leads/9/tg-spam",
            content=b"[]",
            headers={
                "Authorization": f"Bearer {_OWNER_TOKEN}",
                "Content-Type": "application/json",
            },
        )
        self.assertEqual(resp.status_code, 422)
        mock_mark.assert_not_called()

    @patch.object(api_server, "mark_tg_lead_spam", return_value={"ok": True, "lead_id": 11})
    @patch.object(api_server, "psycopg")
    @patch.object(api_server, "is_owner_db_user", return_value=True)
    @patch.object(api_server, "_db_url", return_value=_DB)
    def test_owner_empty_object_body_ok(
        self,
        _db: MagicMock,
        _owner: MagicMock,
        mock_pg: MagicMock,
        mock_mark: MagicMock,
    ) -> None:
        conn = MagicMock()
        mock_pg.connect.return_value.__enter__.return_value = conn
        conn.cursor.return_value.__enter__.return_value = MagicMock()
        resp = self.client.post(
            "/v1/admin/leads/11/tg-spam",
            content=b"{}",
            headers={
                "Authorization": f"Bearer {_OWNER_TOKEN}",
                "Content-Type": "application/json",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"ok": True, "lead_id": 11})
        mock_mark.assert_called_once()

    @patch.object(api_server, "fetch_corpus_summary", return_value={"count": 2, "recent": []})
    @patch.object(api_server, "psycopg")
    @patch.object(api_server, "is_owner_db_user", return_value=True)
    @patch.object(api_server, "_db_url", return_value=_DB)
    def test_corpus_summary(
        self,
        _db: MagicMock,
        _owner: MagicMock,
        mock_pg: MagicMock,
        mock_sum: MagicMock,
    ) -> None:
        conn = MagicMock()
        mock_pg.connect.return_value.__enter__.return_value = conn
        conn.cursor.return_value.__enter__.return_value = MagicMock()
        resp = self.client.get(
            "/v1/admin/tg-spam-corpus",
            headers={"Authorization": f"Bearer {_OWNER_TOKEN}"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["count"], 2)
        mock_sum.assert_called_once()


class TestTgSpamFilterRegression(unittest.TestCase):
    def test_seller_voice_still_spam(self) -> None:
        self.assertTrue(
            is_tg_spam(
                "SEO под ключ",
                "Мы предлагаем продвижение сайтов. Пишите в лс.",
            )
        )


@pytest.mark.parametrize(
    "source,expected",
    [
        ("tg:-100111", -100111),
        ("tg:12345", 12345),
    ],
)
def test_chat_id_param(source: str, expected: int) -> None:
    assert chat_id_from_tg_source(source) == expected


if __name__ == "__main__":
    unittest.main()
