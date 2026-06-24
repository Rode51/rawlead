"""O86: bot @rawlead_bot — mute auth errors and admin-command noise for subscribers."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456789:ABCDEF_fake_test_token")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@127.0.0.1:5432/test")
os.environ["RADAR_PROFILE"] = "site"

import telegram_control as tc  # noqa: E402


def _cfg() -> MagicMock:
    cfg = MagicMock()
    cfg.database_url = os.environ["DATABASE_URL"]
    cfg.telegram_bot_token = os.environ["TELEGRAM_BOT_TOKEN"]
    cfg.telegram_chat_id = "999001"
    cfg.bot_notify_owner_start = False
    return cfg


class TestTelegramO86(unittest.TestCase):
    @patch.object(tc, "_send_to_chat")
    @patch("bot_auth.mint_bot_first_login_url", side_effect=RuntimeError("boom"))
    def test_bot_login_error_muted(self, _mint: MagicMock, send: MagicMock) -> None:
        cfg = _cfg()
        errors: list[str] = []
        message = {"from": {"id": 42, "username": "u"}, "chat": {"id": 42}}
        handled = tc._handle_bot_login_link(
            cfg, message, chat_id=42, user_id=42, errors=errors
        )
        self.assertTrue(handled)
        send.assert_not_called()
        self.assertTrue(any("bot_login:err" in e for e in errors))

    @patch.object(tc, "_send_to_chat")
    @patch(
        "bot_auth.authorize_bot_auth_session",
        return_value=(False, "", "session expired"),
    )
    def test_bot_auth_fail_notifies_user(self, _auth: MagicMock, send: MagicMock) -> None:
        cfg = _cfg()
        errors: list[str] = []
        message = {"from": {"id": 42}, "chat": {"id": 42}}
        handled = tc._handle_bot_auth_start(
            cfg,
            message,
            auth_token="tok",
            chat_id=42,
            user_id=42,
            errors=errors,
        )
        self.assertTrue(handled)
        send.assert_called_once()
        self.assertIn("истекла", send.call_args[0][2].casefold())
        self.assertTrue(any("bot_auth:fail" in e for e in errors))

    @patch.object(tc, "_send_to_chat")
    def test_admin_command_on_subscriber_muted(self, send: MagicMock) -> None:
        cfg = _cfg()
        errors: list[str] = []
        message = {"from": {"id": 42}, "chat": {"id": 42}, "text": "/pause"}
        handled = tc._handle_subscriber_message(
            message, cfg, "/pause", errors, is_admin=False
        )
        self.assertTrue(handled)
        send.assert_not_called()


class TestM1Welcome(unittest.TestCase):
    """M1-bot: /start → welcome text + inline UTM button."""

    @patch.object(tc, "upsert_subscriber_chat_id")
    @patch.object(tc, "_send_to_chat")
    def test_bare_start_sends_welcome_with_utm(self, send: MagicMock, _upsert: MagicMock) -> None:
        cfg = _cfg()
        errors: list[str] = []
        message = {"from": {"id": 100}, "chat": {"id": 100}}
        handled = tc._handle_subscriber_message(
            message, cfg, "/start", errors, is_admin=False
        )
        self.assertTrue(handled)
        self.assertEqual(send.call_count, 2)
        # First call: welcome + inline UTM
        text = send.call_args_list[0][0][2]
        self.assertIn("RawLead", text)
        self.assertIn("Trial", text)
        markup = send.call_args_list[0][1]["reply_markup"]
        self.assertIn("utm_content=bot_welcome", markup)
        self.assertIn("Попробовать →", markup)
        # Second call: reply keyboard hint
        hint_markup = send.call_args_list[1][1]["reply_markup"]
        self.assertIn(tc._BTN_M1_START, hint_markup)

    @patch.object(tc, "upsert_subscriber_chat_id")
    @patch.object(tc, "_send_to_chat")
    def test_m1_chat_start_utm_content(self, send: MagicMock, _upsert: MagicMock) -> None:
        cfg = _cfg()
        errors: list[str] = []
        message = {"from": {"id": 101}, "chat": {"id": 101}}
        handled = tc._handle_subscriber_message(
            message, cfg, "/start m1_chat", errors, is_admin=False
        )
        self.assertTrue(handled)
        self.assertEqual(send.call_count, 2)
        markup = send.call_args_list[0][1]["reply_markup"]
        self.assertIn("utm_content=m1_chat", markup)
        self.assertNotIn("bot_welcome", markup)

    @patch.object(tc, "upsert_subscriber_chat_id")
    @patch.object(tc, "_send_to_chat")
    def test_start_login_not_broken(self, send: MagicMock, _upsert: MagicMock) -> None:
        cfg = _cfg()
        errors: list[str] = []
        message = {"from": {"id": 102}, "chat": {"id": 102}}
        with patch("bot_auth.mint_bot_first_login_url", return_value="https://t.me/rawlead_bot?start=auth_xyz"):
            handled = tc._handle_subscriber_message(
                message, cfg, "/start login", errors, is_admin=False
            )
        self.assertTrue(handled)
        # login sends via _send_to_chat with inline URL, not welcome text
        if send.called:
            text = send.call_args[0][2]
            self.assertNotIn("Trial бесплатно", text)

    @patch.object(tc, "upsert_subscriber_chat_id")
    @patch.object(tc, "_send_pay_flow")
    def test_start_pay_not_broken(self, _pay: MagicMock, _upsert: MagicMock) -> None:
        cfg = _cfg()
        errors: list[str] = []
        message = {"from": {"id": 103}, "chat": {"id": 103}}
        handled = tc._handle_subscriber_message(
            message, cfg, "/start pay", errors, is_admin=False
        )
        self.assertTrue(handled)
        _pay.assert_called_once()

    def test_m1_welcome_url_default(self) -> None:
        url = tc._m1_welcome_url()
        self.assertIn("utm_content=bot_welcome", url)
        self.assertIn("utm_source=telegram", url)
        self.assertIn("utm_campaign=m1_test_v0", url)

    def test_m1_welcome_url_m1_chat(self) -> None:
        url = tc._m1_welcome_url("m1_chat")
        self.assertIn("utm_content=m1_chat", url)

    @patch.object(tc, "upsert_subscriber_chat_id")
    @patch.object(tc, "_send_to_chat")
    def test_start_button_tap_sends_welcome(self, send: MagicMock, _upsert: MagicMock) -> None:
        """▶️ Старт button tap → same as /start."""
        cfg = _cfg()
        errors: list[str] = []
        message = {"from": {"id": 200}, "chat": {"id": 200}}
        handled = tc._handle_subscriber_message(
            message, cfg, tc._BTN_M1_START, errors, is_admin=False
        )
        self.assertTrue(handled)
        self.assertEqual(send.call_count, 2)
        markup = send.call_args_list[0][1]["reply_markup"]
        self.assertIn("utm_content=bot_welcome", markup)
        self.assertIn("Попробовать →", markup)

    @patch.object(tc, "_send_to_chat")
    def test_random_text_gets_welcome(self, send: MagicMock) -> None:
        """Non-admin 'привет' → welcome + inline (not silence)."""
        cfg = _cfg()
        errors: list[str] = []
        message = {"from": {"id": 300}, "chat": {"id": 300}}
        handled = tc._handle_subscriber_message(
            message, cfg, "привет", errors, is_admin=False
        )
        self.assertTrue(handled)
        send.assert_called_once()
        text = send.call_args[0][2]
        self.assertIn("RawLead", text)
        markup = send.call_args[1]["reply_markup"]
        self.assertIn("Попробовать →", markup)

    @patch.object(tc, "_send_to_chat")
    def test_admin_text_not_welcome(self, send: MagicMock) -> None:
        """Admin /pause still muted — catch-all doesn't fire for admin."""
        cfg = _cfg()
        errors: list[str] = []
        message = {"from": {"id": 999}, "chat": {"id": 999}}
        handled = tc._handle_subscriber_message(
            message, cfg, "/pause", errors, is_admin=True
        )
        # admin: _resolve_action returns "pause" but is_admin=True → falls to return False
        self.assertFalse(handled)
        send.assert_not_called()


class TestBotNotifyOwnerStart(unittest.TestCase):
    """BOT-NOTIFY-START — owner ping on first /start only."""

    def _owner_send_calls(self, send: MagicMock, owner_chat: str = "999001") -> list:
        return [
            c
            for c in send.call_args_list
            if str(c[0][1]) == owner_chat and c[1].get("with_admin_keyboard") is False
        ]

    @patch.object(tc, "upsert_subscriber_chat_id")
    @patch.object(tc, "_send_to_chat")
    @patch("telegram_control.psycopg.connect")
    def test_first_start_notifies_owner(
        self, mock_connect: MagicMock, send: MagicMock, _upsert: MagicMock
    ) -> None:
        cfg = _cfg()
        cfg.bot_notify_owner_start = True
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = (None,)
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn

        errors: list[str] = []
        message = {"from": {"id": 501, "username": "newbie"}, "chat": {"id": 501}}
        handled = tc._handle_subscriber_message(
            message, cfg, "/start", errors, is_admin=False
        )
        self.assertTrue(handled)
        owner_calls = self._owner_send_calls(send)
        self.assertEqual(len(owner_calls), 1)
        owner_text = owner_calls[0][0][2]
        self.assertIn("🆕 /start @rawlead_bot", owner_text)
        self.assertIn("@newbie", owner_text)
        self.assertIn("tg 501", owner_text)
        self.assertIn("start: —", owner_text)
        mock_cur.execute.assert_any_call(
            """
                    UPDATE users
                    SET bot_start_owner_notified_at = NOW()
                    WHERE tg_user_id = %s
                    """,
            (501,),
        )
        user_calls = [c for c in send.call_args_list if str(c[0][1]) == "501"]
        self.assertEqual(len(user_calls), 2)

    @patch.object(tc, "upsert_subscriber_chat_id")
    @patch.object(tc, "_send_to_chat")
    @patch("telegram_control.psycopg.connect")
    def test_second_start_skips_owner(
        self, mock_connect: MagicMock, send: MagicMock, _upsert: MagicMock
    ) -> None:
        cfg = _cfg()
        cfg.bot_notify_owner_start = True
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = ("2026-06-21T12:00:00+00:00",)
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_connect.return_value = mock_conn

        errors: list[str] = []
        message = {"from": {"id": 502}, "chat": {"id": 502}}
        handled = tc._handle_subscriber_message(
            message, cfg, "/start", errors, is_admin=False
        )
        self.assertTrue(handled)
        self.assertEqual(len(self._owner_send_calls(send)), 0)

    @patch.object(tc, "upsert_subscriber_chat_id")
    @patch.object(tc, "_send_to_chat")
    @patch("telegram_control.psycopg.connect")
    def test_admin_start_skips_owner(
        self, mock_connect: MagicMock, send: MagicMock, _upsert: MagicMock
    ) -> None:
        cfg = _cfg()
        cfg.bot_notify_owner_start = True
        errors: list[str] = []
        message = {"from": {"id": 999001}, "chat": {"id": 999001}}
        handled = tc._handle_subscriber_message(
            message, cfg, "/start", errors, is_admin=True
        )
        self.assertTrue(handled)
        mock_connect.assert_not_called()
        self.assertEqual(len(self._owner_send_calls(send)), 0)

    @patch.object(tc, "upsert_subscriber_chat_id")
    @patch.object(tc, "_send_to_chat")
    @patch("telegram_control.psycopg.connect")
    def test_flag_off_skips_owner(
        self, mock_connect: MagicMock, send: MagicMock, _upsert: MagicMock
    ) -> None:
        cfg = _cfg()
        cfg.bot_notify_owner_start = False
        errors: list[str] = []
        message = {"from": {"id": 503}, "chat": {"id": 503}}
        handled = tc._handle_subscriber_message(
            message, cfg, "/start", errors, is_admin=False
        )
        self.assertTrue(handled)
        mock_connect.assert_not_called()
        self.assertEqual(len(self._owner_send_calls(send)), 0)


class TestSupportTgReply(unittest.TestCase):
    """O116-SUPPORT-TG-REPLY — owner answers ticket from admin chat."""

    @patch.object(tc, "_send_message")
    @patch("support_tickets.admin_reply", return_value={"ok": True, "ticket_id": 5})
    def test_reply_to_notice_calls_admin_reply(self, mock_reply: MagicMock, send: MagicMock) -> None:
        cfg = _cfg()
        cfg.telegram_chat_id = "999001"
        errors: list[str] = []
        message = {
            "from": {"id": 999001},
            "chat": {"id": 999001},
            "text": "Мой ответ пользователю",
            "reply_to_message": {
                "text": "Тикет от пользователя 5\nTG: @u · id 1\nuser_id: guest\n\nвопрос",
            },
        }
        handled = tc._handle_admin_support_reply(message, cfg, message["text"], errors)
        self.assertTrue(handled)
        mock_reply.assert_called_once_with(cfg.database_url, ticket_id=5, body="Мой ответ пользователю")
        send.assert_called_once_with(cfg, "✓ Ответ в тикете #5")

    @patch.object(tc, "_send_message")
    @patch("support_tickets.admin_reply", return_value={"ok": True, "ticket_id": 9})
    def test_fallback_hash_format(self, mock_reply: MagicMock, send: MagicMock) -> None:
        cfg = _cfg()
        errors: list[str] = []
        message = {"from": {"id": 999001}, "chat": {"id": 999001}, "text": "#9 текст ответа"}
        handled = tc._handle_admin_support_reply(message, cfg, message["text"], errors)
        self.assertTrue(handled)
        mock_reply.assert_called_once_with(cfg.database_url, ticket_id=9, body="текст ответа")
        send.assert_called_once()

    @patch.object(tc, "_send_message")
    @patch("support_tickets.admin_reply", side_effect=ValueError("ticket not found"))
    def test_ticket_not_found(self, mock_reply: MagicMock, send: MagicMock) -> None:
        cfg = _cfg()
        errors: list[str] = []
        message = {"from": {"id": 999001}, "chat": {"id": 999001}, "text": "#99 нет такого"}
        handled = tc._handle_admin_support_reply(message, cfg, message["text"], errors)
        self.assertTrue(handled)
        send.assert_called_once()
        self.assertIn("не найден", send.call_args[0][1].casefold())

    @patch("support_tickets.admin_reply")
    @patch.object(tc, "_send_to_chat")
    def test_non_admin_hash_ignored(self, send: MagicMock, mock_reply: MagicMock) -> None:
        """Non-admin `#1 hi` → welcome, not admin_reply."""
        cfg = _cfg()
        errors: list[str] = []
        message = {"from": {"id": 300}, "chat": {"id": 300}}
        handled = tc._handle_subscriber_message(
            message, cfg, "#1 hi there friend", errors, is_admin=False
        )
        self.assertTrue(handled)
        mock_reply.assert_not_called()
        send.assert_called_once()
        self.assertIn("RawLead", send.call_args[0][2])


if __name__ == "__main__":
    unittest.main()
