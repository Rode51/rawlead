"""O265: match-push bot — 4 buttons + nope/draft callbacks."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

from match_push import (  # noqa: E402
    _NOPE_CALLBACK_RE,
    _push_keyboard,
    _send_tg_draft_result,
    handle_tg_draft_callback,
    handle_tg_nope_callback,
)
from src.api_server import _WEIGHT_EVENT_SPECS  # noqa: E402


class TestO265PushKeyboard(TestCase):
    def test_keyboard_four_buttons_exact_labels(self) -> None:
        raw = _push_keyboard(
            show_generate=True,
            lead_id=9012,
            order_url="https://fl.ru/projects/9012/",
        )
        data = json.loads(raw)
        labels = [btn["text"] for row in data["inline_keyboard"] for btn in row]
        self.assertEqual(
            labels,
            ["Не моё", "Отклик", "Смотреть в ленте", "Смотреть на бирже"],
        )

    def test_deeplink_lenta_and_exchange_urls(self) -> None:
        raw = _push_keyboard(
            show_generate=False,
            lead_id=555,
            order_url="https://youdo.com/tasks/abc",
        )
        data = json.loads(raw)
        row2 = data["inline_keyboard"][1]
        self.assertEqual(row2[0]["url"], "https://rawlead.ru/lenta/?lead=555")
        self.assertEqual(row2[1]["url"], "https://youdo.com/tasks/abc")

    def test_nope_callback_pattern(self) -> None:
        m = _NOPE_CALLBACK_RE.match("nope:777")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "777")


class TestO265NopeCallback(TestCase):
    def test_nope_applies_push_nope_weight(self) -> None:
        cfg = MagicMock()
        cfg.database_url = "postgresql://test"
        cfg.telegram_bot_token = "123:ABC"

        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = ("00000000-0000-0000-0000-000000000099",)
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        callback = {
            "id": "cb1",
            "data": "nope:321",
            "from": {"id": 424242},
        }
        errors: list[str] = []

        with (
            patch("match_push.psycopg.connect", return_value=mock_conn),
            patch("match_push._answer_callback_query") as answer,
            patch("api_server._apply_tag_weight_event_for_lead") as apply_weight,
        ):
            handled = handle_tg_nope_callback(cfg, callback, errors)

        self.assertTrue(handled)
        answer.assert_called_once()
        self.assertIn("Учтём в профиле", answer.call_args[0][2])
        apply_weight.assert_called_once_with(
            "00000000-0000-0000-0000-000000000099",
            321,
            "push_nope",
        )
        self.assertTrue(any("tg:push:nope lead=321" in e for e in errors))

    def test_push_nope_weight_spec(self) -> None:
        delta, interaction, touch = _WEIGHT_EVENT_SPECS["push_nope"]
        self.assertEqual(delta, -1.0)
        self.assertEqual(interaction, 1)
        self.assertTrue(touch)


class TestO265DraftCallback(TestCase):
    def test_send_tg_draft_result_applies_draft_weight(self) -> None:
        cfg = MagicMock()
        errors: list[str] = []
        with (
            patch("match_push._send_draft_reply"),
            patch("api_server._apply_tag_weight_event_for_lead") as apply_weight,
        ):
            _send_tg_draft_result(
                cfg,
                222,
                888,
                "Здравствуйте, готов взяться.",
                errors,
                "00000000-0000-0000-0000-000000000001",
            )
        apply_weight.assert_called_once_with(
            "00000000-0000-0000-0000-000000000001",
            888,
            "draft",
        )

    def test_draft_ready_triggers_send_result(self) -> None:
        cfg = MagicMock()
        cfg.database_url = "postgresql://test"
        cfg.telegram_bot_token = "123:ABC"

        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = ("00000000-0000-0000-0000-000000000001",)
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        draft_resp = MagicMock()
        draft_resp.status = "ready"
        draft_resp.reply_draft = "Здравствуйте, готов взяться."

        callback = {
            "id": "cb2",
            "data": "draft:888",
            "from": {"id": 111},
            "message": {"chat": {"id": 222}},
        }
        errors: list[str] = []

        with (
            patch("match_push.psycopg.connect", return_value=mock_conn),
            patch("match_push._user_effective_access", return_value=True),
            patch("match_push._answer_callback_query"),
            patch("match_push._send_tg_draft_result") as send_result,
            patch("draft_async.submit_draft", return_value=draft_resp),
        ):
            handled = handle_tg_draft_callback(cfg, callback, errors)

        self.assertTrue(handled)
        send_result.assert_called_once()

    def test_draft_rate_limit_no_submit(self) -> None:
        cfg = MagicMock()
        cfg.database_url = "postgresql://test"
        cfg.telegram_bot_token = "123:ABC"

        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = ("00000000-0000-0000-0000-000000000001",)
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        callback = {
            "id": "cb4",
            "data": "draft:777",
            "from": {"id": 111},
            "message": {"chat": {"id": 222}},
        }
        errors: list[str] = []

        with (
            patch("match_push.psycopg.connect", return_value=mock_conn),
            patch("match_push._user_effective_access", return_value=True),
            patch("match_push.draft_rate_limit_retry_after", return_value=120),
            patch("match_push._answer_callback_query") as answer,
            patch("draft_async.submit_draft") as submit,
        ):
            handled = handle_tg_draft_callback(cfg, callback, errors)

        self.assertTrue(handled)
        submit.assert_not_called()
        self.assertIn("Лимит", answer.call_args[0][2])
        self.assertIn("черновиков в час", answer.call_args[0][2])
        self.assertTrue(any("tg:draft:mute" in e and "rate_limit" in e for e in errors))

    def test_draft_forbidden_upsell_no_submit(self) -> None:
        cfg = MagicMock()
        cfg.database_url = "postgresql://test"
        cfg.telegram_bot_token = "123:ABC"

        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = ("00000000-0000-0000-0000-000000000001",)
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        callback = {
            "id": "cb3",
            "data": "draft:999",
            "from": {"id": 111},
            "message": {"chat": {"id": 222}},
        }
        errors: list[str] = []

        with (
            patch("match_push.psycopg.connect", return_value=mock_conn),
            patch("match_push._user_effective_access", return_value=False),
            patch("match_push._answer_callback_query") as answer,
            patch("draft_async.submit_draft") as submit,
        ):
            handled = handle_tg_draft_callback(cfg, callback, errors)

        self.assertTrue(handled)
        submit.assert_not_called()
        self.assertIn("cabinet", answer.call_args[0][2].casefold())
        self.assertTrue(any("tg:draft:mute" in e and "forbidden" in e for e in errors))
