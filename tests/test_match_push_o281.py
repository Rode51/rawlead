"""O281: nope callback deletes push message from TG chat."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

from match_push import _delete_message, handle_tg_nope_callback  # noqa: E402


def _mock_db_conn(user_id: str = "00000000-0000-0000-0000-000000000099") -> MagicMock:
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = (user_id,)
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    return mock_conn


class TestO281NopeDeleteMessage(TestCase):
    def test_nope_calls_delete_after_weight(self) -> None:
        cfg = MagicMock()
        cfg.database_url = "postgresql://test"
        cfg.telegram_bot_token = "123:ABC"

        callback = {
            "id": "cb1",
            "data": "nope:321",
            "from": {"id": 424242},
            "message": {"message_id": 55, "chat": {"id": 999}},
        }
        errors: list[str] = []

        with (
            patch("match_push.psycopg.connect", return_value=_mock_db_conn()),
            patch("match_push._answer_callback_query"),
            patch("api_server._apply_tag_weight_event_for_lead") as apply_weight,
            patch("match_push._delete_message") as delete_msg,
        ):
            handled = handle_tg_nope_callback(cfg, callback, errors)

        self.assertTrue(handled)
        apply_weight.assert_called_once_with(
            "00000000-0000-0000-0000-000000000099",
            321,
            "push_nope",
        )
        delete_msg.assert_called_once_with(cfg, 999, 55)
        self.assertTrue(any("tg:push:nope lead=321" in e for e in errors))

    def test_nope_without_message_skips_delete(self) -> None:
        cfg = MagicMock()
        cfg.database_url = "postgresql://test"
        cfg.telegram_bot_token = "123:ABC"

        callback = {
            "id": "cb1",
            "data": "nope:321",
            "from": {"id": 424242},
        }
        errors: list[str] = []

        with (
            patch("match_push.psycopg.connect", return_value=_mock_db_conn()),
            patch("match_push._answer_callback_query"),
            patch("api_server._apply_tag_weight_event_for_lead"),
            patch("match_push._delete_message") as delete_msg,
        ):
            handled = handle_tg_nope_callback(cfg, callback, errors)

        self.assertTrue(handled)
        delete_msg.assert_not_called()

    def test_delete_message_hits_telegram_api(self) -> None:
        cfg = MagicMock()
        cfg.telegram_bot_token = "123:ABC"

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"ok": True}

        mock_session = MagicMock()
        mock_session.post.return_value = mock_resp

        with (
            patch("match_push.telegram_requests_proxies", return_value={}),
            patch("match_push.requests.Session", return_value=mock_session),
        ):
            _delete_message(cfg, 999, 55)

        mock_session.post.assert_called_once()
        call_kwargs = mock_session.post.call_args
        self.assertIn("deleteMessage", call_kwargs[0][0])
        self.assertEqual(call_kwargs[1]["data"]["chat_id"], "999")
        self.assertEqual(call_kwargs[1]["data"]["message_id"], "55")

    def test_delete_message_failure_does_not_raise(self) -> None:
        cfg = MagicMock()
        cfg.telegram_bot_token = "123:ABC"

        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = "Bad Request: message can't be deleted"
        mock_resp.json.return_value = {
            "ok": False,
            "description": "Bad Request: message can't be deleted",
        }

        mock_session = MagicMock()
        mock_session.post.return_value = mock_resp

        with (
            patch("match_push.telegram_requests_proxies", return_value={}),
            patch("match_push.requests.Session", return_value=mock_session),
        ):
            _delete_message(cfg, 999, 55)
