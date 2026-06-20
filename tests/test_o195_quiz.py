"""O195: tags import + weight_delta + weighted rank."""

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

os.environ.setdefault("RAWLEAD_JWT_SECRET", "test-jwt-secret-o195")
os.environ.setdefault("RAWLEAD_API_KEY", "test-jwt-secret-o195")
os.environ["RADAR_PROFILE"] = "site"

from fastapi.testclient import TestClient  # noqa: E402

from src import api_server  # noqa: E402
from src.api_server import (  # noqa: E402
    _apply_tag_weight_event,
    _resolve_user_id,
    _upsert_imported_user_tags,
    app,
)
from src.jwt_auth import issue_access_token  # noqa: E402
from skills_catalog import user_tags_input_count  # noqa: E402
from rank import (  # noqa: E402
    EMPTY_PROFILE_KEYWORD_MATCH,
    decay_factor,
    effective_weight,
    keyword_match,
    tags_as_weights,
)


class TestTagsImport(unittest.TestCase):
    def test_upsert_writes_weight_and_counters(self) -> None:
        cur = MagicMock()
        user_id = "00000000-0000-0000-0000-000000000099"
        n = _upsert_imported_user_tags(cur, user_id, {"python": 4.0, "ui_ux": -1.0})
        self.assertEqual(n, 2)
        sql = cur.execute.call_args_list[0][0][0]
        self.assertIn("last_active_at", sql)
        self.assertIn("interaction_count", sql)

    def test_import_endpoint(self) -> None:
        user_id = "00000000-0000-0000-0000-000000000099"
        token = issue_access_token(user_id, tg_user_id=5151)
        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            with patch.object(
                api_server, "_replace_quiz_import_user_tags", return_value=2
            ) as replace_import:
                with patch("pg_storage._ensure_user_tags_columns"):
                    client = TestClient(app)
                    resp = client.post(
                        "/v1/me/tags/import",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"tags": {"python": 4.0, "ui_ux": -1.0}},
                    )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["imported"], 2)
        replace_import.assert_called_once()

    def test_import_accepts_over_twelve_quiz_liked_tags(self) -> None:
        user_id = "00000000-0000-0000-0000-000000000099"
        token = issue_access_token(user_id, tg_user_id=5151)
        many_tags = {f"python": 4.0}
        for i, slug in enumerate(
            (
                "javascript",
                "php",
                "typescript",
                "wordpress_dev",
                "telegram_bot_dev",
                "api_integration",
                "web_scraping",
                "llm_integration",
                "mobile_dev",
                "data_analysis",
                "ecommerce_dev",
                "figma",
                "ui_ux",
                "smm",
            )
        ):
            many_tags[slug] = 4.0 - i * 0.01
        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            with patch.object(
                api_server, "_replace_quiz_import_user_tags", return_value=15
            ) as replace_import:
                with patch("pg_storage._ensure_user_tags_columns"):
                    client = TestClient(app)
                    resp = client.post(
                        "/v1/me/tags/import",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"tags": many_tags, "niches": ["dev", "marketing"]},
                    )
        self.assertEqual(resp.status_code, 200)
        passed_tags = replace_import.call_args[0][2]
        skill_keys = [k for k in passed_tags if not str(k).startswith("__")]
        self.assertEqual(
            user_tags_input_count(skill_keys),
            15,
        )

    def test_replace_import_deletes_before_upsert(self) -> None:
        cur = MagicMock()
        user_id = "00000000-0000-0000-0000-000000000099"
        tags = {"python": 4.0, "fastapi": 4.0}
        with patch.object(api_server, "_upsert_imported_user_tags", return_value=2) as upsert:
            n = api_server._replace_quiz_import_user_tags(cur, user_id, tags)
        self.assertEqual(n, 2)
        delete_sql = cur.execute.call_args_list[0][0][0]
        self.assertIn("DELETE FROM user_tags", delete_sql)
        upsert.assert_called_once_with(cur, user_id, tags)


class TestWeightedRank(unittest.TestCase):
    def test_empty_profile_constant(self) -> None:
        self.assertEqual(EMPTY_PROFILE_KEYWORD_MATCH, 50)

    def test_decay_reduces_weight(self) -> None:
        old = datetime.now(timezone.utc) - timedelta(days=6)
        self.assertLess(decay_factor(old), 1.0)

    def test_effective_weight_floor(self) -> None:
        old = datetime.now(timezone.utc) - timedelta(days=365)
        self.assertIsNone(effective_weight(5.0, old))

    def test_weighted_keyword_match(self) -> None:
        user = {"python": 3.0, "figma": 1.0}
        self.assertEqual(keyword_match(["python", "php"], user), 75)


class TestWeightDelta(unittest.TestCase):
    def test_apply_expand_delta(self) -> None:
        cur = MagicMock()
        user_id = "00000000-0000-0000-0000-000000000099"
        n = _apply_tag_weight_event(cur, user_id, "expand", ["python"])
        self.assertEqual(n, 1)
        sql = cur.execute.call_args_list[0][0][0]
        self.assertIn("interaction_count", sql)

    def test_weight_delta_endpoint(self) -> None:
        user_id = "00000000-0000-0000-0000-000000000099"
        token = issue_access_token(user_id, tg_user_id=5151)
        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            with patch.object(api_server, "_apply_tag_weight_event", return_value=1) as apply:
                with patch("pg_storage._ensure_user_tags_columns"):
                    client = TestClient(app)
                    resp = client.post(
                        "/v1/me/tags/weight_delta",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"event": "expand", "tags": ["python"]},
                    )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["updated"], 1)
        apply.assert_called_once()

    def test_weight_delta_rejects_expand_no_reply(self) -> None:
        user_id = "00000000-0000-0000-0000-000000000099"
        token = issue_access_token(user_id, tg_user_id=5151)
        app.dependency_overrides[_resolve_user_id] = lambda: user_id
        try:
            client = TestClient(app)
            resp = client.post(
                "/v1/me/tags/weight_delta",
                headers={"Authorization": f"Bearer {token}"},
                json={"event": "expand_no_reply", "tags": ["python", "fastapi"]},
            )
        finally:
            app.dependency_overrides.clear()
        self.assertEqual(resp.status_code, 400)
        self.assertIn("event must be one of", resp.json()["detail"])
        self.assertNotIn("expand_no_reply", resp.json()["detail"])


if __name__ == "__main__":
    unittest.main()
