"""L1 round-robin OpenRouter keys."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from config import Config  # noqa: E402


def _cfg(*, b: str = "") -> Config:
    return Config(
        fl_projects_url="https://example.com",
        kwork_projects_url="",
        poll_interval_minutes=1,
        legacy_neon_poll_sec=60,
        telegram_bot_token="t",
        telegram_chat_id="1",
        sqlite_path=_ROOT / "data" / "x.db",
        radar_log_path=_ROOT / "data" / "x.log",
        http_user_agent="ua",
        tg_proxy_url="http://127.0.0.1:8000:a:b",
        ai_enabled=True,
        ai_api_key="key-a",
        ai_api_key_l1_b=b,
        ai_model="m",
        ai_model_summary="m",
        ai_model_premium="m",
        ai_model_shared_draft="m",
        ai_model_judge="m",
        ai_provider="openrouter",
        min_budget_rub=0,
        ai_notify_skip=False,
        filter_wide=True,
        database_url="",
        radar_profile="site",
        ai_mode="split",
        filters_md_path=_ROOT / "docs" / "ops" / "FILTERS_SITE.md",
        site_notify_on_ai_unavailable=False,
        site_notify_owner=False,
        bot_notify_owner_start=False,
        radar_conveyor=True,
        l1_batch_per_cycle=40,
        l1_max_workers=4,
        l1_backlog_drain=False,
        match_push_enabled=False,
        stars_enabled=False,
        stars_price_xtr=1,
        stars_subscription_days=30,
        pay_premium_rub=790,
        pay_sbp_phone="",
        pay_sbp_bank="T-Bank",
        pay_btc_address="",
        pay_eth_address="",
        pay_usdt_trc20_address="",
        pay_usdt_erc20_address="",
        pay_ton_address="",
        pay_crypto_memo_prefix="RL",
        pay_approve_bot="legacy",
        yookassa_shop_id="",
        yookassa_secret_key="",
        yookassa_return_url="https://rawlead.ru/cabinet/",
        yookassa_webhook_secret="",
        yookassa_save_payment_method=False,
    )


class TestL1DualApiKey(unittest.TestCase):
    def test_no_alt_key(self) -> None:
        c = _cfg()
        self.assertEqual(c.l1_openrouter_api_key(1), "key-a")
        self.assertEqual(c.l1_openrouter_api_key(2), "key-a")

    def test_round_robin(self) -> None:
        c = _cfg(b="key-b")
        self.assertEqual(c.l1_openrouter_api_key(1), "key-a")
        self.assertEqual(c.l1_openrouter_api_key(2), "key-b")
        self.assertEqual(c.l1_openrouter_api_key(3), "key-a")
        self.assertEqual(c.l1_openrouter_api_key(4), "key-b")


if __name__ == "__main__":
    unittest.main()
