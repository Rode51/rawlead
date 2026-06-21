"""O116-WP-FEED: feed prefs, JWT delay, display_replies."""

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
from src.api_server import (  # noqa: E402
    _FEED_PREFS_MIN_MATCH,
    _normalize_feed_prefs,
    app,
)
from src.feed_social import display_replies  # noqa: E402
from src.jwt_auth import issue_access_token  # noqa: E402


class TestDisplayReplies(unittest.TestCase):
    def test_in_band_one_reply(self) -> None:
        self.assertEqual(display_replies(100, 12), 1)

    def test_below_threshold(self) -> None:
        self.assertEqual(display_replies(101, 9), 0)

    def test_out_of_band(self) -> None:
        self.assertEqual(display_replies(50, 20), 0)


class TestFeedPrefsNormalize(unittest.TestCase):
    def test_defaults(self) -> None:
        prefs = _normalize_feed_prefs(None)
        self.assertEqual(prefs["sort"], "time")
        self.assertEqual(prefs["min_match"], 80)

    def test_valid_min_match(self) -> None:
        for mm in _FEED_PREFS_MIN_MATCH:
            prefs = _normalize_feed_prefs({"min_match": mm})
            self.assertEqual(prefs["min_match"], mm)


class TestFeedDelayedJwt(unittest.TestCase):
    def test_bearer_feed_delayed_false(self) -> None:
        user_id = "00000000-0000-0000-0000-000000000099"
        token = issue_access_token(user_id, tg_user_id=4242)
        empty_page = ([], 0, 0)

        with patch.object(api_server, "_db_conn") as mock_db:
            conn = MagicMock()
            cur = MagicMock()
            mock_db.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            with patch.object(api_server, "_personal_feed_page", return_value=empty_page):
                with patch.object(api_server, "_feed_today_count", return_value=0):
                    client = TestClient(app)
                    resp = client.get(
                        "/v1/feed",
                        headers={"Authorization": f"Bearer {token}"},
                    )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["feed_delayed"])


if __name__ == "__main__":
    unittest.main()
