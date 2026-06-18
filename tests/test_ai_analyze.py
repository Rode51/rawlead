"""O220-L1-PROMPT-R2: L1 few-shot anchors + thin-tag retry."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from ai_analyze import (  # noqa: E402
    AiLiteAnalysis,
    _LITE_FEWSHOT_BLOCK,
    _LITE_RETRY_MIN_TAGS_HINT,
    _LITE_SYSTEM,
    analyze_lite,
)
from config import Config  # noqa: E402


def _cfg() -> Config:
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
        ai_api_key_l1_b="",
        ai_model="m",
        ai_model_summary="m",
        ai_model_premium="m",
        ai_model_shared_draft="m",
        ai_model_judge="m",
        ai_model_l3_uniquify="m",
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


class TestO220L1FewShot(unittest.TestCase):
    def test_fewshot_tg_leadgen_marketing_not_dev(self) -> None:
        self.assertIn("лидgen в Telegram", _LITE_FEWSHOT_BLOCK)
        self.assertIn("chatbot_marketing", _LITE_FEWSHOT_BLOCK)

    def test_fewshot_marketplace_cards_design_not_marketing(self) -> None:
        self.assertIn("инфографика для карточек товаров", _LITE_FEWSHOT_BLOCK.lower())
        self.assertIn("infographic_design", _LITE_FEWSHOT_BLOCK)

    def test_fewshot_furniture_cards_not_ui_ux(self) -> None:
        self.assertIn("мебели на маркетплейсе", _LITE_FEWSHOT_BLOCK)
        self.assertIn("не ui_ux", _LITE_FEWSHOT_BLOCK)

    def test_fewshot_xmind_text_not_dev(self) -> None:
        self.assertIn("XMind", _LITE_FEWSHOT_BLOCK)
        self.assertIn("technical_writing", _LITE_FEWSHOT_BLOCK)

    def test_system_anti_errors_o220_r2(self) -> None:
        self.assertIn("холодная рассылка", _LITE_SYSTEM)
        self.assertIn("infographic_design", _LITE_SYSTEM)
        self.assertIn("ui_ux/landing_page_design", _LITE_SYSTEM)


class TestO220L1ThinTagRetry(unittest.TestCase):
    @patch("ai_analyze._call_lite_once")
    @patch("ai_analyze.note_ai_l1_call")
    def test_retry_when_feed_visible_and_one_tag(
        self, _note: MagicMock, mock_lite: MagicMock
    ) -> None:
        mock_lite.side_effect = [
            AiLiteAnalysis(
                feed_visible=True,
                task_summary="WP plugin fix",
                lead_tags=("wordpress_dev",),
                ai_reasons=("WP", "scope"),
                complexity=2,
                primary_category="dev",
            ),
            AiLiteAnalysis(
                feed_visible=True,
                task_summary="WP plugin fix",
                lead_tags=("wordpress_dev", "php"),
                ai_reasons=("WP", "scope"),
                complexity=2,
                primary_category="dev",
            ),
        ]
        result = analyze_lite(
            _cfg(),
            title="Fix WP plugin",
            budget_text="5000",
            snippet="Need WP theme hooks fix",
            url="https://fl.ru/1",
        )
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(len(result.lead_tags), 2)
        self.assertEqual(mock_lite.call_count, 2)
        second_user = mock_lite.call_args_list[1][0][2]
        self.assertIn(_LITE_RETRY_MIN_TAGS_HINT, second_user)

    @patch("ai_analyze._call_lite_once")
    @patch("ai_analyze.note_ai_l1_call")
    def test_no_retry_when_two_tags(
        self, _note: MagicMock, mock_lite: MagicMock
    ) -> None:
        mock_lite.return_value = AiLiteAnalysis(
            feed_visible=True,
            task_summary="Landing",
            lead_tags=("wordpress_dev", "php"),
            ai_reasons=("WP", "scope"),
            complexity=2,
            primary_category="dev",
        )
        analyze_lite(
            _cfg(),
            title="WP landing",
            budget_text="10000",
            snippet="WordPress landing with forms",
            url="https://fl.ru/2",
        )
        self.assertEqual(mock_lite.call_count, 1)


if __name__ == "__main__":
    unittest.main()
