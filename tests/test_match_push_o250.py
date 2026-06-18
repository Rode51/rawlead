"""O250/O250b/O250d: push_match_for_lead — UUID safety + feed km parity."""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

from match_push import _load_user_tags, _push_km_for_lead_row, _uid8, push_match_for_lead  # noqa: E402
from rank import compatibility_match, effective_user_tag_weights, keyword_match, tags_as_weights  # noqa: E402

class TestO250Uid8(TestCase):
    def test_uid8_uuid_and_str(self) -> None:
        uid = uuid.UUID("aabbccdd-eeee-ffff-0000-000000000001")
        self.assertEqual(_uid8(uid), "aabbccdd")
        self.assertEqual(_uid8("aabbccdd-eeee-ffff-0000-000000000001"), "aabbccdd")


class TestO250PushUuidUserId(TestCase):
    def test_push_match_for_lead_uuid_user_id_no_crash(self) -> None:
        cfg = MagicMock()
        cfg.match_push_enabled = True
        cfg.database_url = "postgresql://test"
        cfg.telegram_bot_token = "123:ABC"

        lead_row = (
            21767,
            "fl",
            "Test lead",
            "body",
            "https://fl.ru/projects/1",
            "10 000 ₽",
            80,
            "Брать",
            ["python"],
            (),
            None,
            "dev",
            "summary",
            ["python"],
            None,
        )
        user_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
        user_row = (
            user_uuid,
            8688264540,
            "agent",
            True,
            None,
            None,
            60,
            True,
        )

        mock_cur = MagicMock()
        mock_cur.fetchone.side_effect = [
            lead_row,
            ("proj-1",),
            None,
            None,
            None,
            ("agent", True, None, None),
        ]
        mock_cur.fetchall.side_effect = [
            [user_row],
            [("python",)],
        ]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        errors: list[str] = []
        with (
            patch("match_push.psycopg.connect", return_value=mock_conn),
            patch("match_push._load_user_tags", return_value={"python": 4.0}),
            patch("match_push._send_push_message", return_value=(True, "")) as mock_send,
        ):
            sent = push_match_for_lead(
                cfg,
                21767,
                title="Test lead",
                task_summary="summary",
                lead_tags=["python"],
                errors=errors,
            )

        self.assertEqual(sent, 1)
        mock_send.assert_called_once()
        self.assertTrue(any("push:match:user=00000000" in e for e in errors))
        self.assertFalse(any("push:match:err" in e for e in errors))


class TestO250bPushMatchParity(TestCase):
    """Feed 100% (lead-coverage) must push when keyword_match alone would skip."""

    def test_push_uses_compatibility_match_not_keyword_match(self) -> None:
        lead_tags = ["python"]
        user_tags = {"python": 4.0}
        for i in range(29):
            user_tags[f"skill_{i}"] = 1.0
        self.assertEqual(keyword_match(lead_tags, user_tags), 12)
        self.assertEqual(
            compatibility_match(lead_tags, user_tags, lead_category="dev"),
            100,
        )

        cfg = MagicMock()
        cfg.match_push_enabled = True
        cfg.database_url = "postgresql://test"
        cfg.telegram_bot_token = "123:ABC"

        lead_row = (
            26785,
            "fl",
            "Закупка рекламы у блогеров",
            "body",
            "https://fl.ru/projects/26785",
            "50 000 ₽",
            80,
            "Брать",
            lead_tags,
            (),
            None,
            "dev",
            "summary",
            [],
            None,
        )
        user_uuid = uuid.UUID("00000000-0000-0000-0000-000000000001")
        user_row = (
            user_uuid,
            8688264540,
            "agent",
            True,
            None,
            None,
            80,
            True,
        )

        mock_cur = MagicMock()
        mock_cur.fetchone.side_effect = [
            lead_row,
            ("fl-26785",),
            None,
            None,
            None,
            ("agent", True, None, None),
        ]
        mock_cur.fetchall.return_value = [user_row]

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        errors: list[str] = []
        with (
            patch("match_push.psycopg.connect", return_value=mock_conn),
            patch("match_push._load_user_tags", return_value=user_tags),
            patch("match_push._send_push_message", return_value=(True, "")) as mock_send,
        ):
            sent = push_match_for_lead(
                cfg,
                26785,
                title="Закупка рекламы у блогеров",
                task_summary="summary",
                lead_tags=lead_tags,
                errors=errors,
            )

        self.assertEqual(sent, 1)
        mock_send.assert_called_once()
        push_text = mock_send.call_args[0][2]
        self.assertIn("Match 100%", push_text)
        self.assertTrue(any("push:match:user=00000000" in e and "km=100" in e for e in errors))


class TestO250dPushKmLoaderParity(TestCase):
    """Lead 27204-class: push must use effective_user_tag_weights like feed API."""

    def test_load_user_tags_uses_effective_weights(self) -> None:
        rows = [("python", 4.0, None), ("django", 2.0, None)]
        mock_cur = MagicMock()
        mock_cur.fetchall.return_value = rows
        with patch("pg_storage._ensure_user_tags_columns"):
            with patch("config.load_config") as mock_cfg:
                mock_cfg.return_value.database_url = "postgresql://test"
                result = _load_user_tags(mock_cur, "00000000-0000-0000-0000-000000000001")
        self.assertEqual(result, effective_user_tag_weights(rows))

    def test_feed_and_push_km_match_monica_like_profile(self) -> None:
        from src.api_server import _km_for_lead_row

        now = datetime.now(timezone.utc)
        stale = now - timedelta(days=60)
        rows: list[tuple[str, float, datetime]] = [("python", 4.0, now)]
        for i in range(29):
            rows.append((f"skill_{i}", 1.0, stale))
        effective = effective_user_tag_weights(rows)
        flat = tags_as_weights([r[0] for r in rows])

        lead_row = (
            27204,
            "tg",
            "бот в ТG",
            "body",
            "https://t.me/prompt-test/1",
            "50 000 ₽",
            80,
            "Брать",
            ["python"],
            (),
            None,
            "dev",
            "summary",
            ["python"],
            None,
        )

        feed_km = _km_for_lead_row(lead_row, effective)
        push_km = _push_km_for_lead_row(lead_row, effective)
        self.assertEqual(feed_km, push_km)
        self.assertGreaterEqual(feed_km or 0, 60)

        broken_km = _push_km_for_lead_row(lead_row, flat)
        self.assertLess(broken_km or 0, feed_km or 0)
