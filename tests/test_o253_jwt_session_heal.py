"""O253: stale JWT sub heals via tg_id — no subscription FK 500."""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

os.environ.setdefault("RAWLEAD_JWT_SECRET", "test-jwt-secret-o253")
os.environ.setdefault("RAWLEAD_API_KEY", "test-jwt-secret-o253")
os.environ["RADAR_PROFILE"] = "site"

from fastapi import HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from src import api_server  # noqa: E402
from src.api_server import _JWT_ROTATION_HEADER, app  # noqa: E402
from src.jwt_auth import issue_access_token  # noqa: E402


class TestO253JwtSessionHeal(unittest.TestCase):
    def test_canonical_user_id_heals_from_tg_id(self) -> None:
        ghost_id = "00000000-0000-0000-0000-000000000099"
        real_id = "00000000-0000-0000-0000-000000000088"
        tg_id = 5177575757

        mock_cur = MagicMock()
        mock_cur.fetchone.side_effect = [None, (real_id,)]
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        with patch.object(api_server, "_db_conn") as mock_db:
            mock_db.return_value.__enter__.return_value = mock_conn
            result = api_server._canonical_user_id_from_jwt(
                {"sub": ghost_id, "tg_id": tg_id}
            )
        self.assertEqual(result, real_id)

    def test_canonical_user_id_session_stale_without_tg_id(self) -> None:
        ghost_id = "00000000-0000-0000-0000-000000000097"
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        with patch.object(api_server, "_db_conn") as mock_db:
            mock_db.return_value.__enter__.return_value = mock_conn
            with self.assertRaises(HTTPException) as ctx:
                api_server._canonical_user_id_from_jwt({"sub": ghost_id})
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "session_stale")

    def test_me_subscription_stale_jwt_200(self) -> None:
        ghost_id = "00000000-0000-0000-0000-000000000099"
        real_id = "00000000-0000-0000-0000-000000000088"
        tg_id = 5177575757
        token = issue_access_token(ghost_id, tg_user_id=tg_id)
        now = datetime.now(timezone.utc)

        heal_cur = MagicMock()
        heal_cur.fetchone.side_effect = [None, (real_id,)]
        heal_conn = MagicMock()
        heal_conn.cursor.return_value.__enter__.return_value = heal_cur

        sub_cur = MagicMock()
        sub_cur.fetchone.return_value = (1,)

        sub_conn = MagicMock()
        sub_conn.cursor.return_value.__enter__.return_value = sub_cur

        with patch.object(api_server, "_db_conn") as mock_db:
            mock_db.return_value.__enter__.return_value = heal_conn
            with patch.object(api_server, "psycopg") as mock_pg:
                mock_pg.connect.return_value.__enter__.return_value = sub_conn
                with patch.object(api_server, "expire_stale_trials"):
                    with patch.object(
                        api_server,
                        "fetch_subscription_row",
                        return_value=("agent", True, now + timedelta(days=30), None, None),
                    ):
                        with patch.object(
                            api_server,
                            "fetch_subscription_billing_fields",
                            return_value={
                                "auto_renew": False,
                                "has_payment_method": False,
                                "renew_canceled_at": None,
                            },
                        ):
                            with patch.object(
                                api_server, "yookassa_available", return_value=False
                            ):
                                client = TestClient(app)
                                resp = client.get(
                                    "/v1/me/subscription",
                                    headers={"Authorization": f"Bearer {token}"},
                                )

        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["plan"], "agent")
        self.assertTrue(body["effective_access"])
        rotated = resp.headers.get(_JWT_ROTATION_HEADER)
        self.assertTrue(rotated)
        self.assertNotEqual(rotated, token)


if __name__ == "__main__":
    unittest.main()
