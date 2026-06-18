"""O231: inbox delete reverses draft weight + fires reply_delete."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

os.environ.setdefault("RAWLEAD_JWT_SECRET", "test-jwt-secret-o231")
os.environ.setdefault("RAWLEAD_API_KEY", "test-jwt-secret-o231")
os.environ["RADAR_PROFILE"] = "site"

from fastapi.testclient import TestClient  # noqa: E402

from src import api_server  # noqa: E402
from src.api_server import _WEIGHT_EVENT_SPECS, app  # noqa: E402
from src.jwt_auth import issue_access_token  # noqa: E402


class TestO231ReplyDeleteWeight(unittest.TestCase):
    def test_reply_delete_spec_mirrors_draft(self) -> None:
        draft = _WEIGHT_EVENT_SPECS["draft"]
        reply_delete = _WEIGHT_EVENT_SPECS["reply_delete"]
        self.assertEqual(reply_delete[0], -draft[0])
        self.assertEqual(reply_delete[1], -draft[1])
        self.assertFalse(reply_delete[2])

    def test_me_reply_delete_applies_reply_delete_and_inbox_delete(self) -> None:
        user_id = "00000000-0000-0000-0000-000000000231"
        lead_id = 23101
        token = issue_access_token(user_id, tg_user_id=2310)
        lead_row = (
            lead_id,
            "fl",
            "Title",
            "Body",
            "https://example.com",
            "1000",
            80,
            "ok",
            '["python"]',
            "[]",
            None,
            "dev",
            "",
            [],
            "",
        )

        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            cur.fetchone.side_effect = [(lead_id,), lead_row]
            with patch.object(api_server, "_canonical_lead_tags", return_value=["python"]):
                with patch.object(api_server, "_apply_tag_weight_event", return_value=1) as apply:
                    client = TestClient(app)
                    resp = client.delete(
                        f"/v1/me/replies/{lead_id}",
                        headers={"Authorization": f"Bearer {token}"},
                    )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"id": lead_id, "deleted": True})
        self.assertEqual(apply.call_count, 2)
        apply.assert_any_call(cur, user_id, "reply_delete", ["python"])
        apply.assert_any_call(cur, user_id, "inbox_delete", ["python"])

    def test_me_reply_delete_idempotent_when_already_deleted(self) -> None:
        user_id = "00000000-0000-0000-0000-000000000232"
        lead_id = 23102
        token = issue_access_token(user_id, tg_user_id=2320)

        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            cur.fetchone.return_value = None
            with patch.object(api_server, "_apply_tag_weight_event", return_value=1) as apply:
                client = TestClient(app)
                resp = client.delete(
                    f"/v1/me/replies/{lead_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )

        self.assertEqual(resp.status_code, 404)
        apply.assert_not_called()


if __name__ == "__main__":
    unittest.main()
