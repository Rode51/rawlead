"""O175: multi-source feed filter + inbox replies visibility."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

os.environ.setdefault("RAWLEAD_JWT_SECRET", "test-jwt-secret-o175")
os.environ.setdefault("RAWLEAD_API_KEY", "test-jwt-secret-o175")
os.environ["RADAR_PROFILE"] = "site"

from fastapi.testclient import TestClient  # noqa: E402

from src import api_server  # noqa: E402
from src.api_server import (  # noqa: E402
    _feed_where_with_sources,
    _normalize_feed_prefs,
    app,
)
from src.jwt_auth import issue_access_token  # noqa: E402
from src.public_feed import (  # noqa: E402
    FEED_VISIBILITY_DAYS,
    INBOX_VISIBILITY_DAYS,
    feed_source_filter_sql,
    inbox_replies_where_sql,
    parse_feed_source_param,
)


class TestParseFeedSourceParam(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual(parse_feed_source_param(""), [])
        self.assertEqual(parse_feed_source_param("  "), [])

    def test_multi_keys(self) -> None:
        self.assertEqual(parse_feed_source_param("fl,kwork"), ["fl", "kwork"])

    def test_tg_and_dedupe(self) -> None:
        self.assertEqual(parse_feed_source_param("tg,fl,tg,unknown"), ["tg", "fl"])


class TestFeedSourceFilterSql(unittest.TestCase):
    def test_empty(self) -> None:
        sql, params = feed_source_filter_sql([])
        self.assertEqual(sql, "")
        self.assertEqual(params, [])

    def test_exact_sources(self) -> None:
        sql, params = feed_source_filter_sql(["fl", "kwork"])
        self.assertIn("source = ANY", sql)
        self.assertEqual(params, [["fl", "kwork"]])

    def test_tg_prefix(self) -> None:
        sql, params = feed_source_filter_sql(["tg"])
        self.assertIn("LIKE %s", sql)
        self.assertEqual(params, ["tg:%"])

    def test_mixed_with_alias(self) -> None:
        sql, params = feed_source_filter_sql(["fl", "tg"], alias="l")
        self.assertIn("l.source = ANY", sql)
        self.assertIn("l.source LIKE %s", sql)
        self.assertEqual(params, [["fl"], "tg:%"])


class TestFeedWhereWithSources(unittest.TestCase):
    def test_appends_source_filter(self) -> None:
        sql, params = _feed_where_with_sources(source_keys=["fl"])
        self.assertIn("is_visible = TRUE", sql)
        self.assertIn("source = ANY", sql)
        self.assertIn(FEED_VISIBILITY_DAYS, params)


class TestInboxRepliesWhere(unittest.TestCase):
    def test_uses_reply_window_not_lead_visible(self) -> None:
        sql, params = inbox_replies_where_sql(alias="ulr")
        self.assertIn("ulr.deleted_at IS NULL", sql)
        self.assertIn("ulr.created_at >=", sql)
        self.assertNotIn("is_visible", sql)
        self.assertEqual(params, [INBOX_VISIBILITY_DAYS])

    def test_me_replies_query_uses_inbox_where(self) -> None:
        user_id = "00000000-0000-0000-0000-000000000055"
        token = issue_access_token(user_id, tg_user_id=555)

        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            cur.fetchall.return_value = []
            cur.fetchone.return_value = (0,)

            client = TestClient(app)
            resp = client.get(
                "/v1/me/replies",
                headers={"Authorization": f"Bearer {token}"},
            )

        self.assertEqual(resp.status_code, 200)
        executed = "\n".join(str(c[0][0]) for c in cur.execute.call_args_list)
        self.assertIn("ulr.deleted_at IS NULL", executed)
        self.assertIn("ulr.created_at >=", executed)
        self.assertNotIn("is_visible", executed)


class TestFeedSourceParamEndpoint(unittest.TestCase):
    def test_feed_passes_source_keys_to_page(self) -> None:
        empty_page = ([], 0, 0)
        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            with patch.object(api_server, "_feed_page_time", return_value=empty_page) as mock_time:
                with patch.object(api_server, "_feed_today_count_cached", return_value=0):
                    client = TestClient(app)
                    resp = client.get("/v1/feed?source=fl,kwork&limit=5")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["source"], ["fl", "kwork"])
        mock_time.assert_called_once()
        self.assertEqual(mock_time.call_args.kwargs.get("source_keys"), ["fl", "kwork"])

    def test_logged_in_feed_source_fl_youdo(self) -> None:
        user_id = "00000000-0000-0000-0000-000000000044"
        token = issue_access_token(user_id, tg_user_id=444)
        empty_page = ([], 0, 0)
        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            with patch.object(
                api_server, "_personal_feed_page", return_value=empty_page
            ) as mock_personal:
                client = TestClient(app)
                resp = client.get(
                    "/v1/feed?sort=time&source=fl,youdo&limit=5",
                    headers={"Authorization": f"Bearer {token}"},
                )
        self.assertEqual(resp.status_code, 200)
        mock_personal.assert_called_once()
        self.assertEqual(mock_personal.call_args.kwargs.get("source_keys"), ["fl", "youdo"])

    def test_anon_feed_source_tg(self) -> None:
        empty_page = ([], 0, 0)
        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            with patch.object(api_server, "_feed_page_time", return_value=empty_page) as mock_time:
                with patch.object(api_server, "_feed_today_count_cached", return_value=0):
                    client = TestClient(app)
                    resp = client.get("/v1/feed?sort=time&source=tg&limit=5")
        self.assertEqual(resp.status_code, 200)
        mock_time.assert_called_once()
        self.assertEqual(mock_time.call_args.kwargs.get("source_keys"), ["tg"])

    def test_anon_feed_match_with_source(self) -> None:
        empty_page = ([], 0, 0)
        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            with patch.object(api_server, "_feed_page_match", return_value=empty_page) as mock_match:
                with patch.object(api_server, "_feed_today_count_cached", return_value=0):
                    client = TestClient(app)
                    resp = client.get("/v1/feed?sort=match&min_match=80&source=fl&limit=5")
        self.assertEqual(resp.status_code, 200)
        mock_match.assert_called_once()
        self.assertEqual(mock_match.call_args.kwargs.get("source_keys"), ["fl"])

    def test_me_feed_passes_source_keys(self) -> None:
        user_id = "00000000-0000-0000-0000-000000000066"
        token = issue_access_token(user_id, tg_user_id=666)
        empty_page = ([], 0, 0)
        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            with patch.object(
                api_server, "_personal_feed_page", return_value=empty_page
            ) as mock_personal:
                client = TestClient(app)
                resp = client.get(
                    "/v1/me/feed?sort=time&source=tg&limit=5",
                    headers={"Authorization": f"Bearer {token}"},
                )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["source"], ["tg"])
        mock_personal.assert_called_once()
        self.assertEqual(mock_personal.call_args.kwargs.get("source_keys"), ["tg"])

    def test_me_feed_source_fl_only(self) -> None:
        user_id = "00000000-0000-0000-0000-000000000067"
        token = issue_access_token(user_id, tg_user_id=667)
        empty_page = ([], 0, 0)
        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            with patch.object(
                api_server, "_personal_feed_page", return_value=empty_page
            ) as mock_personal:
                client = TestClient(app)
                resp = client.get(
                    "/v1/me/feed?source=fl&limit=5",
                    headers={"Authorization": f"Bearer {token}"},
                )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["source"], ["fl"])
        mock_personal.assert_called_once()
        self.assertEqual(mock_personal.call_args.kwargs.get("source_keys"), ["fl"])


class TestFeedPrefsSource(unittest.TestCase):
    def test_normalize_source_csv(self) -> None:
        prefs = _normalize_feed_prefs({"source": "fl,tg,fl"})
        self.assertEqual(prefs["source"], "fl,tg")


if __name__ == "__main__":
    unittest.main()
