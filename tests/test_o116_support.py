"""O116-W4 — support tickets + TG notify + thread."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

os.environ.setdefault("RAWLEAD_JWT_SECRET", "test-jwt-secret-o116")
os.environ.setdefault("RAWLEAD_API_KEY", "test-jwt-secret-o116")
os.environ["RADAR_PROFILE"] = "site"

from fastapi.testclient import TestClient  # noqa: E402

from src import api_server  # noqa: E402
from src.api_server import app  # noqa: E402
from src.jwt_auth import issue_access_token  # noqa: E402
from src.support_tickets import (  # noqa: E402
    normalize_body,
    normalize_guest_token,
    preview_text,
    send_owner_support_notice,
)


class TestSupportNormalize(unittest.TestCase):
    def test_guest_token(self) -> None:
        self.assertIsNotNone(normalize_guest_token("abc12345_xyz"))
        self.assertIsNone(normalize_guest_token("bad token!"))

    def test_body_bounds(self) -> None:
        self.assertEqual(normalize_body("hello"), "hello")
        with self.assertRaises(ValueError):
            normalize_body("ab")

    def test_preview(self) -> None:
        long = "x" * 400
        self.assertTrue(len(preview_text(long)) <= 280)


class TestSupportApi(unittest.TestCase):
    def test_ticket_and_thread(self) -> None:
        guest = "gtest_token_12345678"
        owner_id = "00000000-0000-0000-0000-000000000001"
        owner_token = issue_access_token(owner_id, tg_user_id=1)

        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur

            cur.fetchone.side_effect = [
                None,
                (1,),
                (1,),
                (1,),
                (1,),
                (1,),
            ]
            cur.fetchall.side_effect = [
                [],
                [
                    (1, "user", "Привет", None, None),
                ],
            ]

            with patch.object(
                api_server,
                "create_user_ticket",
                return_value={"ok": True, "ticket_id": 1, "is_new_ticket": True, "owner_notified": True},
            ):
                client = TestClient(app)
                resp = client.post(
                    "/v1/support/ticket",
                    headers={"X-RawLead-Guest-Token": guest},
                    json={"message": "Нужна помощь с лентой", "source": "fab"},
                )
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(resp.json()["ok"])

            with patch.object(
                api_server,
                "get_user_thread",
                return_value={"ticket_id": 1, "messages": [{"from": "user", "body": "x"}], "unread": 0},
            ):
                thread = client.get(
                    "/v1/support/thread",
                    headers={"X-RawLead-Guest-Token": guest},
                )
            self.assertEqual(thread.status_code, 200)
            self.assertEqual(thread.json()["ticket_id"], 1)

            with patch.object(
                api_server,
                "admin_list_tickets",
                return_value=[{"id": 1, "last_preview": "x"}],
            ):
                with patch.object(api_server, "is_owner_db_user", return_value=True):
                    listing = client.get(
                        "/v1/admin/support/tickets",
                        headers={"Authorization": f"Bearer {owner_token}"},
                    )
            self.assertEqual(listing.status_code, 200)
            self.assertEqual(len(listing.json()["tickets"]), 1)


class TestSupportTg(unittest.TestCase):
    @patch("src.support_tickets._send_to_chat")
    def test_notify_owner(self, mock_send: MagicMock) -> None:
        cfg = MagicMock()
        cfg.telegram_chat_id = "123"
        cfg.telegram_bot_token = "token"
        ok = send_owner_support_notice(
            cfg,
            ticket_id=42,
            tg_username="tester",
            tg_user_id=99,
            user_id="uuid-here",
            preview="Короткий вопрос",
            is_new_ticket=True,
        )
        self.assertTrue(ok)
        mock_send.assert_called_once()
        text = mock_send.call_args[0][2]
        self.assertIn("Тикет от пользователя 42", text)
        self.assertIn("@tester", text)


if __name__ == "__main__":
    unittest.main()
