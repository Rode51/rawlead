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


if __name__ == "__main__":
    unittest.main()
