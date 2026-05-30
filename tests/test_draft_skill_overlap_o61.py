"""O61: paid draft allowed at keyword_match=0 — no skill overlap gate."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.draft_async import DraftPollResponse, submit_draft  # noqa: E402
from src.match_push import generate_and_store_lead_draft, materialize_shared_draft_for_user  # noqa: E402

_USER = "00000000-0000-0000-0000-000000000201"
_LEAD_ID = 9101

_LEAD_ROW = (
    _LEAD_ID,
    "fl",
    "Joomla site",
    "body",
    "https://fl.ru/9101",
    "30000",
    80,
    "Брать",
    '["joomla"]',
    "[]",
    None,
    "dev",
    "Need Joomla dev",
    '["joomla"]',
    "",
)


class TestDraftNoKmGate(unittest.TestCase):
    @patch("src.match_push.psycopg.connect")
    @patch("src.match_push._analyze_shared_ondemand", return_value="Draft at zero overlap.")
    @patch("src.match_push.keyword_match", return_value=0)
    @patch("src.match_push._canonical_lead_tags", return_value=["joomla"])
    @patch("src.match_push._parse_ai_reasons", return_value=[])
    @patch("src.match_push._parse_tools_required", return_value=["joomla"])
    @patch("src.match_push._user_effective_access", return_value=True)
    @patch("src.match_push._fetch_lead_row", return_value=_LEAD_ROW)
    @patch("src.match_push._fetch_saved_draft", return_value=None)
    @patch("src.match_push._load_user_tags", return_value={"python": 1.0})
    @patch("src.match_push.draft_rate_limit_retry_after", return_value=None)
    @patch("src.match_push.note_draft_request")
    @patch("src.match_push.strip_reply_draft_price_deadline", side_effect=lambda x: x)
    def test_generate_draft_km_zero_ok(
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

        with patch("src.match_push._insert_user_draft"):
            result = generate_and_store_lead_draft(
                cfg,
                user_id=_USER,
                lead_id=_LEAD_ID,
                enforce_rate_limit=False,
            )

        analyze.assert_called_once()
        self.assertEqual(result.reply_draft, "Draft at zero overlap.")
        self.assertEqual(result.keyword_match, 0)

    @patch("src.match_push.psycopg.connect")
    @patch("src.match_push.keyword_match", return_value=0)
    @patch("src.match_push._canonical_lead_tags", return_value=["joomla"])
    @patch("src.match_push._user_effective_access", return_value=True)
    @patch("src.match_push._fetch_saved_draft", return_value=None)
    @patch("src.match_push._load_user_tags", return_value={"python": 1.0})
    @patch("src.match_push.strip_reply_draft_price_deadline", side_effect=lambda x: x)
    def test_materialize_shared_km_zero_ok(
        self,
        _strip: MagicMock,
        _tags: MagicMock,
        _saved: MagicMock,
        _access: MagicMock,
        _canonical: MagicMock,
        _km: MagicMock,
        _connect: MagicMock,
    ) -> None:
        cfg = MagicMock()
        cfg.database_url = "postgresql://test"
        shared_row = _LEAD_ROW[:14] + ("Cached shared draft.",)

        conn = MagicMock()
        cur = MagicMock()
        _connect.return_value.__enter__.return_value = conn
        conn.cursor.return_value.__enter__.return_value = cur

        with (
            patch("src.match_push._fetch_lead_row", return_value=shared_row),
            patch("src.match_push._insert_user_draft") as insert,
        ):
            result = materialize_shared_draft_for_user(
                cfg,
                user_id=_USER,
                lead_id=_LEAD_ID,
            )

        self.assertIsNotNone(result)
        assert result is not None
        insert.assert_called_once()
        self.assertEqual(result.reply_draft, "Cached shared draft.")
        self.assertEqual(result.keyword_match, 0)

    @patch("src.draft_async._try_materialize_shared")
    @patch("src.draft_async._ensure_draft_tables")
    @patch("src.draft_async.psycopg.connect")
    def test_submit_draft_materializes_at_km_zero(
        self,
        mock_connect: MagicMock,
        _ensure: MagicMock,
        materialize: MagicMock,
    ) -> None:
        cfg = MagicMock()
        cfg.ai_active = True
        cfg.database_url = "postgresql://test"
        materialize.return_value = DraftPollResponse(
            status="ready",
            lead_id=_LEAD_ID,
            reply_draft="Ready at 0%",
            keyword_match=0,
        )

        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_connect.return_value = mock_conn

        with patch("src.draft_async._fetch_saved_draft", return_value=None):
            resp = submit_draft(
                cfg,
                user_id=_USER,
                lead_id=_LEAD_ID,
                quick_wait_sec=0,
            )

        self.assertEqual(resp.status, "ready")
        self.assertEqual(resp.reply_draft, "Ready at 0%")
        self.assertEqual(resp.keyword_match, 0)


if __name__ == "__main__":
    unittest.main()
