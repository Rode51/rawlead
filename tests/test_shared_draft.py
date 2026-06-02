"""O89: shared base + per-user uniquify cache."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.match_push import DraftResult, generate_and_store_lead_draft  # noqa: E402


_USER_A = "00000000-0000-0000-0000-000000000101"
_USER_B = "00000000-0000-0000-0000-000000000102"
_LEAD_ID = 9001

_LEAD_ROW = (
    _LEAD_ID,
    "fl",
    "Test lead",
    "body",
    "https://fl.ru/1",
    "50000",
    80,
    "Брать",
    '["python"]',
    "[]",
    None,
    "dev",
    "Need Python API",
    '["python", "fastapi"]',
    "",
)


class TestSharedDraftCache(unittest.TestCase):
    @patch("src.match_push.psycopg.connect")
    @patch("src.match_push.rephrase_reply_draft_per_user")
    @patch("src.match_push._fetch_saved_draft", return_value="Cached user text")
    @patch("src.match_push._fetch_lead_row", return_value=_LEAD_ROW)
    @patch("src.match_push._user_effective_access", return_value=True)
    @patch("src.match_push._canonical_lead_tags", return_value=["python"])
    @patch("src.match_push._load_user_tags", return_value={"python": 1.0})
    @patch("src.match_push.keyword_match", return_value=80)
    @patch("src.match_push.draft_rate_limit_retry_after", return_value=None)
    def test_repeat_click_uses_cached_user_reply(
        self,
        _rate: MagicMock,
        _km: MagicMock,
        _tags: MagicMock,
        _canonical: MagicMock,
        _access: MagicMock,
        _row: MagicMock,
        _saved: MagicMock,
        rephrase: MagicMock,
        _connect: MagicMock,
    ) -> None:
        cfg = MagicMock()
        cfg.ai_active = True
        cfg.database_url = "postgresql://test"
        conn = MagicMock()
        cur = MagicMock()
        _connect.return_value.__enter__.return_value = conn
        conn.cursor.return_value.__enter__.return_value = cur
        out = generate_and_store_lead_draft(cfg, user_id=_USER_A, lead_id=_LEAD_ID, enforce_rate_limit=False)
        self.assertEqual(out.reply_draft, "Cached user text")
        rephrase.assert_not_called()

    @patch("src.match_push.psycopg.connect")
    @patch("src.match_push.rephrase_reply_draft_per_user")
    @patch("src.match_push.keyword_match", return_value=80)
    @patch("src.match_push._canonical_lead_tags", return_value=["python"])
    @patch("src.match_push._user_effective_access", return_value=True)
    @patch("src.match_push._fetch_lead_row")
    @patch("src.match_push._fetch_saved_draft")
    @patch("src.match_push._load_user_tags", return_value={"python": 1.0})
    @patch("src.match_push.draft_rate_limit_retry_after", return_value=None)
    @patch("src.match_push.note_draft_request")
    @patch("src.match_push.strip_reply_draft_price_deadline", side_effect=lambda x: x)
    def test_user_gets_personalized_from_shared_cache(
        self,
        _strip: MagicMock,
        _note: MagicMock,
        _rate: MagicMock,
        _tags: MagicMock,
        fetch_saved: MagicMock,
        fetch_row: MagicMock,
        _access: MagicMock,
        _canonical: MagicMock,
        _km: MagicMock,
        rephrase: MagicMock,
        _connect: MagicMock,
    ) -> None:
        cfg = MagicMock()
        cfg.ai_active = True
        cfg.database_url = "postgresql://test"

        conn = MagicMock()
        cur = MagicMock()
        _connect.return_value.__enter__.return_value = conn
        conn.cursor.return_value.__enter__.return_value = cur

        shared_row = _LEAD_ROW[:14] + ("Shared draft text.",)
        fetch_saved.return_value = None
        fetch_row.return_value = shared_row
        rephrase.return_value = "Personalized B"

        with patch("src.match_push._insert_user_draft") as insert:
            result = generate_and_store_lead_draft(
                cfg,
                user_id=_USER_B,
                lead_id=_LEAD_ID,
                enforce_rate_limit=False,
            )

        rephrase.assert_called_once()
        insert.assert_called_once()
        self.assertEqual(result.reply_draft, "Personalized B")

    @patch("src.match_push.psycopg.connect")
    @patch("src.match_push._analyze_shared_ondemand", return_value="Fresh shared draft.")
    @patch("src.match_push.rephrase_reply_draft_per_user")
    @patch("src.match_push.keyword_match", return_value=80)
    @patch("src.match_push._canonical_lead_tags", return_value=["python"])
    @patch("src.match_push._parse_ai_reasons", return_value=[])
    @patch("src.match_push._parse_tools_required", return_value=["python", "fastapi"])
    @patch("src.match_push._user_effective_access", return_value=True)
    @patch("src.match_push._fetch_lead_row", return_value=_LEAD_ROW)
    @patch("src.match_push._fetch_saved_draft", return_value=None)
    @patch("src.match_push._load_user_tags", return_value={"python": 1.0})
    @patch("src.match_push.draft_rate_limit_retry_after", return_value=None)
    @patch("src.match_push.note_draft_request")
    @patch("src.match_push.strip_reply_draft_price_deadline", side_effect=lambda x: x)
    def test_first_user_calls_ai_once(
        self,
        _strip: MagicMock,
        _note: MagicMock,
        _rate: MagicMock,
        _tags: MagicMock,
        _saved: MagicMock,
        _row: MagicMock,
        _access: MagicMock,
        parse_tools: MagicMock,
        parse_reasons: MagicMock,
        _canonical: MagicMock,
        _km: MagicMock,
        rephrase: MagicMock,
        analyze: MagicMock,
        _connect: MagicMock,
    ) -> None:
        cfg = MagicMock()
        cfg.ai_active = True
        cfg.database_url = "postgresql://test"

        conn = MagicMock()
        cur = MagicMock()
        _connect.return_value.__enter__.return_value = conn
        conn.cursor.return_value.__enter__.return_value = cur

        rephrase.return_value = "User A text"
        with patch("src.match_push._insert_user_draft"):
            result = generate_and_store_lead_draft(
                cfg,
                user_id=_USER_A,
                lead_id=_LEAD_ID,
                enforce_rate_limit=False,
            )

        analyze.assert_called_once()
        rephrase.assert_called_once()
        self.assertIsInstance(result, DraftResult)
        self.assertEqual(result.reply_draft, "User A text")

    @patch("src.match_push.psycopg.connect")
    @patch("src.match_push._analyze_shared_ondemand", return_value="Fresh shared draft.")
    @patch("src.match_push.rephrase_reply_draft_per_user", side_effect=["A text", "B text"])
    @patch("src.match_push.keyword_match", return_value=80)
    @patch("src.match_push._canonical_lead_tags", return_value=["python"])
    @patch("src.match_push._parse_ai_reasons", return_value=[])
    @patch("src.match_push._parse_tools_required", return_value=["python", "fastapi"])
    @patch("src.match_push._user_effective_access", return_value=True)
    @patch("src.match_push._fetch_lead_row", return_value=_LEAD_ROW)
    @patch("src.match_push._fetch_saved_draft", return_value=None)
    @patch("src.match_push._load_user_tags", return_value={"python": 1.0})
    @patch("src.match_push.draft_rate_limit_retry_after", return_value=None)
    @patch("src.match_push.note_draft_request")
    @patch("src.match_push.strip_reply_draft_price_deadline", side_effect=lambda x: x)
    def test_two_users_get_different_texts(
        self,
        _strip: MagicMock,
        _note: MagicMock,
        _rate: MagicMock,
        _tags: MagicMock,
        _saved: MagicMock,
        _row: MagicMock,
        _access: MagicMock,
        _parse_tools: MagicMock,
        _parse_reasons: MagicMock,
        _canonical: MagicMock,
        _km: MagicMock,
        _rephrase: MagicMock,
        _analyze: MagicMock,
        _connect: MagicMock,
    ) -> None:
        cfg = MagicMock()
        cfg.ai_active = True
        cfg.database_url = "postgresql://test"
        conn = MagicMock()
        cur = MagicMock()
        _connect.return_value.__enter__.return_value = conn
        conn.cursor.return_value.__enter__.return_value = cur
        with patch("src.match_push._insert_user_draft"):
            a = generate_and_store_lead_draft(cfg, user_id=_USER_A, lead_id=_LEAD_ID, enforce_rate_limit=False)
            b = generate_and_store_lead_draft(cfg, user_id=_USER_B, lead_id=_LEAD_ID, enforce_rate_limit=False)
        self.assertNotEqual(a.reply_draft, b.reply_draft)


if __name__ == "__main__":
    unittest.main()
