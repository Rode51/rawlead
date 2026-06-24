"""O105-w1: premium pay — formatters and callback parsing."""

from __future__ import annotations

import sys
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import Config  # noqa: E402
from premium_pay import (  # noqa: E402
    PayRates,
    _OWNER_CALLBACK_RE,
    _parse_user_callback,
    format_crypto_screen,
    format_pay_menu,
    format_sbp_screen,
    pay_available,
    pay_menu_markup,
)


def _cfg(**overrides: object) -> Config:
    base = dict(
        fl_projects_url="",
        kwork_projects_url="",
        poll_interval_minutes=5,
        legacy_neon_poll_sec=60,
        telegram_bot_token="tok",
        telegram_chat_id="1",
        sqlite_path=_ROOT / "data" / "x.sqlite",
        radar_log_path=_ROOT / "data" / "x.log",
        http_user_agent="test",
        tg_proxy_url="",
        ai_enabled=False,
        ai_api_key="",
        ai_api_key_l1_b="",
        ai_model="",
        ai_model_summary="",
        ai_model_premium="",
        ai_model_shared_draft="",
        ai_model_l3_uniquify="",
        ai_model_judge="",
        ai_provider="openrouter",
        min_budget_rub=0,
        ai_notify_skip=False,
        filter_wide=True,
        database_url="postgresql://x",
        radar_profile="site",
        ai_mode="split",
        filters_md_path=_ROOT / "docs" / "ops" / "FILTERS_SITE.md",
        site_notify_on_ai_unavailable=False,
        site_notify_owner=False,
        bot_notify_owner_start=False,
        radar_conveyor=False,
        l1_batch_per_cycle=1,
        l1_max_workers=1,
        l1_backlog_drain=False,
        match_push_enabled=False,
        stars_enabled=True,
        stars_price_xtr=300,
        stars_subscription_days=30,
        pay_premium_rub=790,
        pay_sbp_phone="+79249966496",
        pay_sbp_bank="T-Bank",
        pay_btc_address="bc1qtest",
        pay_eth_address="0xeth",
        pay_usdt_trc20_address="TUSDT",
        pay_usdt_erc20_address="0xusdt",
        pay_ton_address="UQTON",
        pay_crypto_memo_prefix="RL",
        pay_approve_bot="legacy",
        yookassa_shop_id="",
        yookassa_secret_key="",
        yookassa_return_url="https://rawlead.ru/cabinet/",
        yookassa_webhook_secret="",
        yookassa_save_payment_method=False,
    )
    base.update(overrides)
    return Config(**base)  # type: ignore[arg-type]


class TestPremiumPayFormat(unittest.TestCase):
    def test_pay_available_needs_requisites(self) -> None:
        self.assertTrue(pay_available(_cfg()))
        self.assertFalse(pay_available(_cfg(pay_sbp_phone="", pay_btc_address="", pay_usdt_trc20_address="", pay_ton_address="")))

    def test_menu_text_and_markup(self) -> None:
        cfg = _cfg()
        self.assertIn("790", format_pay_menu(cfg))
        markup = pay_menu_markup(cfg)
        self.assertIn("pay:sbp", markup)
        self.assertIn("pay:crypto", markup)
        self.assertIn("pay:stars", markup)

    def test_sbp_screen(self) -> None:
        text = format_sbp_screen(_cfg(), 12345, 7)
        self.assertIn("+79249966496", text)
        self.assertIn("790", text)
        self.assertIn("#7", text)

    def test_crypto_screen_all_networks(self) -> None:
        rates = PayRates(Decimal("95"), Decimal("450"), Decimal("9000000"), Decimal("300000"))
        text = format_crypto_screen(
            _cfg(),
            99,
            3,
            rates,
            amount_usdt=Decimal("8.32"),
            amount_ton=Decimal("1.76"),
        )
        self.assertIn("TUSDT", text)
        self.assertIn("UQTON", text)
        self.assertIn("bc1qtest", text)
        self.assertIn("RL99", text)

    def test_user_callback_parse(self) -> None:
        self.assertEqual(_parse_user_callback("pay:sbp"), ("sbp", "", ""))
        self.assertEqual(_parse_user_callback("pay:chk:42"), ("chk", "42", ""))
        self.assertEqual(_parse_user_callback("pay:cpy:usdt:5"), ("cpy", "usdt", "5"))
        self.assertIsNone(_parse_user_callback("draft:1"))

    def test_stars_intro_markup(self) -> None:
        from premium_pay import format_stars_intro, stars_intro_markup

        cfg = _cfg()
        self.assertIn("300", format_stars_intro(cfg))
        markup = stars_intro_markup(cfg)
        self.assertIn("pay:stinv", markup)
        self.assertIn("pay:menu", markup)


class TestPayRates(unittest.TestCase):
    def test_usdt_for_rub(self) -> None:
        rates = PayRates(Decimal("79"), None, None, None)
        self.assertEqual(rates.usdt_for_rub(790), Decimal("10.00"))


if __name__ == "__main__":
    unittest.main()
