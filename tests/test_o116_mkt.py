"""O116-WP-MKT — public site-stats for header ticker."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

os.environ.setdefault("RAWLEAD_JWT_SECRET", "test-jwt-secret-o116")
os.environ.setdefault("RAWLEAD_API_KEY", "test-jwt-secret-o116")
os.environ["RADAR_PROFILE"] = "site"

from fastapi.testclient import TestClient  # noqa: E402

from src.api_server import (  # noqa: E402
    _leads_week_display,
    _public_leads_week_count,
    app,
)


class TestO116Mkt(unittest.TestCase):
    def test_leads_week_display_buckets_tens(self) -> None:
        self.assertEqual(_leads_week_display(0), 0)
        self.assertEqual(_leads_week_display(9), 9)
        self.assertEqual(_leads_week_display(47), 40)
        self.assertEqual(_leads_week_display(847), 840)

    @patch("src.api_server._public_leads_week_count", return_value=847)
    def test_public_site_stats_endpoint(self, mock_count) -> None:
        client = TestClient(app)
        resp = client.get("/v1/public/site-stats")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["radar_online"])
        self.assertEqual(data["leads_week"], 847)
        self.assertEqual(data["leads_week_display"], 840)
        mock_count.assert_called_once()

    @patch("src.api_server.psycopg.connect")
    def test_public_leads_week_count_sql(self, mock_connect) -> None:
        cur = mock_connect.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value
        cur.fetchone.return_value = (123,)
        self.assertEqual(_public_leads_week_count(), 123)


if __name__ == "__main__":
    unittest.main()
