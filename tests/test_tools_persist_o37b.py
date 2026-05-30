"""O37b: tools_required persist on on-demand draft."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from ai_analyze import AiAnalysis  # noqa: E402
from match_push import generate_and_store_lead_draft  # noqa: E402


def _lead_row(*, tools=None, shared=""):
    return (
        99,
        "fl",
        "Title",
        "Body text",
        "https://fl.ru/1",
        "1000 ₽",
        80,
        "Брать",
        '["python"]',
        "[]",
        None,
        None,
        "Task summary",
        tools,
        shared,
    )


class TestToolsPersistO37b(unittest.TestCase):
    @patch("match_push.note_draft_request")
    @patch("match_push._user_effective_access", return_value=True)
    @patch("match_push._fetch_saved_draft", return_value=None)
    @patch("match_push.analyze_premium")
    @patch("match_push.psycopg.connect")
    def test_empty_tools_uses_premium_and_updates_neon(
        self, mock_connect, mock_premium, *_mocks
    ) -> None:
        mock_premium.return_value = AiAnalysis(
            verdict="Брать",
            work_summary="w",
            tools_required=("python", "fastapi"),
            difficulty="mid",
            approach="a; b",
            time_for_client="1d",
            money="m",
            reply_draft="Hello draft",
            risks="r",
            lead_tags=("python",),
        )
        mock_cur = MagicMock()
        mock_cur.fetchone.side_effect = [
            _lead_row(tools=None, shared=""),
            _lead_row(tools='["python", "fastapi"]', shared=""),
        ]
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_connect.return_value = mock_conn

        cfg = MagicMock()
        cfg.ai_active = True
        cfg.database_url = "postgresql://test"

        with patch("match_push._load_user_tags", return_value=[]):
            with patch("match_push.keyword_match", return_value=50):
                result = generate_and_store_lead_draft(
                    cfg, user_id="00000000-0000-0000-0000-000000000099", lead_id=99
                )

        self.assertEqual(result.reply_draft, "Hello draft")
        self.assertEqual(result.tools_required, ["python", "fastapi"])
        sqls = [str(c[0][0]) for c in mock_cur.execute.call_args_list]
        self.assertTrue(any("tools_required" in s for s in sqls))


if __name__ == "__main__":
    unittest.main()
