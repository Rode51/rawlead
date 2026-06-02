"""TG-AUTH-500-HOTFIX: /v1/auth/telegram smoke — invalid hash → 401, not 500."""

from __future__ import annotations

import os
import sys
import time
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456789:ABCDEF_fake_test_token")
os.environ["RADAR_PROFILE"] = "site"

from fastapi.testclient import TestClient  # noqa: E402

from src.api_server import app  # noqa: E402


class TestTelegramAuth(unittest.TestCase):
    def test_invalid_hash_returns_401_not_500(self) -> None:
        client = TestClient(app)
        resp = client.post(
            "/v1/auth/telegram",
            json={
                "id": 1,
                "first_name": "Test",
                "auth_date": int(time.time()),
                "hash": "deadbeef",
            },
        )
        self.assertEqual(resp.status_code, 401)
        self.assertIn("invalid telegram hash", resp.json()["detail"])

    def test_bot_complete_missing_token_returns_400(self) -> None:
        client = TestClient(app)
        resp = client.post("/v1/auth/bot-complete", json={"auth_token": ""})
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
