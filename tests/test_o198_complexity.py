"""O198: quiz complexity pool + cx_pref rank multiplier."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

os.environ.setdefault("RAWLEAD_JWT_SECRET", "test-jwt-secret-o198")
os.environ.setdefault("RAWLEAD_API_KEY", "test-jwt-secret-o198")
os.environ["RADAR_PROFILE"] = "site"

from fastapi.testclient import TestClient  # noqa: E402

from src import api_server  # noqa: E402
from src.api_server import (  # noqa: E402
    _upsert_imported_user_tags,
    app,
)
from src.jwt_auth import issue_access_token  # noqa: E402
from src.quiz_adaptive import (  # noqa: E402
    QUIZ_POOL_EXCLUDE_IDS,
    _query_card,
    build_profile,
)
from rank import CX_PREF_TAG, complexity_multiplier  # noqa: E402


class TestQuizPoolFilter(unittest.TestCase):
    def test_query_card_excludes_bad_ids_and_prefers_cx12(self) -> None:
        cur = MagicMock()
        cur.fetchone.return_value = None
        _query_card(cur, "dev", "python", [22141])
        sql_calls = [call[0][0] for call in cur.execute.call_args_list]
        self.assertTrue(any("complexity" in sql for sql in sql_calls))
        exclude_params = [call[0][1] for call in cur.execute.call_args_list if len(call[0]) > 1]
        self.assertTrue(any(set(QUIZ_POOL_EXCLUDE_IDS).issubset(set(params[-1])) for params in exclude_params))

    def test_query_card_fallback_relaxes_cx_filter(self) -> None:
        cur = MagicMock()
        cur.fetchone.side_effect = [None, (22304, "Task", "dev", ["python"], {"complexity": 3})]
        row = _query_card(cur, "dev", "python", [])
        self.assertIsNotNone(row)
        sql_calls = [call[0][0] for call in cur.execute.call_args_list]
        self.assertIn(sql_calls[0], sql_calls)
        self.assertTrue(any("complexity" not in sql for sql in sql_calls[1:]))


class TestCxPrefProfile(unittest.TestCase):
    def test_build_profile_cx_pref_from_liked_cards(self) -> None:
        history = [
            {"card_id": "1", "liked": True, "tags": ["python"], "complexity": 1},
            {"card_id": "2", "liked": True, "tags": ["ui_ux"], "complexity": 2},
            {"card_id": "3", "liked": False, "tags": ["seo"], "complexity": 2},
        ]
        cats = {"1": "dev", "2": "design", "3": "marketing"}
        profile = build_profile(history, cats, 180)
        assert profile is not None
        self.assertEqual(profile["cx_pref"], 1.5)


class TestComplexityMultiplier(unittest.TestCase):
    def test_examples_from_spec(self) -> None:
        self.assertEqual(complexity_multiplier(3, 1.5), 0.85)
        self.assertEqual(complexity_multiplier(2, 2.0), 1.0)


class TestCxPrefImport(unittest.TestCase):
    def test_import_writes_cx_pref_tag(self) -> None:
        cur = MagicMock()
        user_id = "00000000-0000-0000-0000-000000000099"
        n = _upsert_imported_user_tags(cur, user_id, {CX_PREF_TAG: 1.4, "python": 4.0})
        self.assertEqual(n, 2)
        tags_written = [call[0][1][1] for call in cur.execute.call_args_list]
        self.assertIn(CX_PREF_TAG, tags_written)

    def test_import_endpoint_accepts_cx_pref(self) -> None:
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
                        json={"tags": {"python": 4.0}, "cx_pref": 1.4},
                    )
        self.assertEqual(resp.status_code, 200)
        replace_import.assert_called_once()
        tags_map = replace_import.call_args[0][2]
        self.assertEqual(tags_map[CX_PREF_TAG], 1.4)


if __name__ == "__main__":
    unittest.main()
