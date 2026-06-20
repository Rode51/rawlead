"""O220-FEED r2–r7: concurrent cap · pending restore · layout · checkout probe."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import Config  # noqa: E402
from yookassa_billing import CheckoutError, create_checkout, yookassa_available  # noqa: E402

_FEED_JS = _ROOT / "wordpress/rawlead-kadence-child/assets/js/rawlead-feed.js"
_FEED_CSS = _ROOT / "wordpress/rawlead-kadence-child/assets/css/rawlead.css"
_FUNCTIONS = _ROOT / "wordpress/rawlead-kadence-child/functions.php"


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
        filters_md_path=_ROOT / "docs/ops/FILTERS_SITE.md",
        site_notify_on_ai_unavailable=False,
        site_notify_owner=False,
        radar_conveyor=False,
        l1_batch_per_cycle=1,
        l1_max_workers=1,
        l1_backlog_drain=False,
        match_push_enabled=False,
        stars_enabled=False,
        stars_price_xtr=600,
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
        yookassa_shop_id="1380074",
        yookassa_secret_key="test_secret",
        yookassa_return_url="https://rawlead.ru/cabinet/",
        yookassa_webhook_secret="wh",
        yookassa_save_payment_method=True,
    )
    base.update(overrides)
    return Config(**base)


def _checkout_hosts_ok(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host.endswith("yookassa.ru") or host.endswith("yoomoney.ru")


class TestO220FeedDraftJs(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.js = _FEED_JS.read_text(encoding="utf-8")
        cls.css = _FEED_CSS.read_text(encoding="utf-8")

    def test_r2_concurrent_cap_five(self) -> None:
        self.assertIn("DRAFT_MAX_CONCURRENT = 5", self.js)
        self.assertIn("countDraftInflight() >= DRAFT_MAX_CONCURRENT", self.js)
        self.assertIn("Максимум 5 откликов одновременно", self.js)

    def test_r3_pending_restore(self) -> None:
        for needle in (
            "restorePendingDrafts",
            "resumePendingDraft",
            "removePendingDraft",
            "PENDING_DRAFTS_KEY",
            "pollDraftStatus(leadId, startedMs)",
        ):
            self.assertIn(needle, self.js)
        self.assertIn("restorePendingDrafts();", self.js)

    def test_r6_slot_counter_removed(self) -> None:
        self.assertRegex(
            self.js,
            r"function renderSlotLine\(item\)\s*\{[^}]*return\s+\"\";",
        )

    def test_r4_difficulty_spacing_css(self) -> None:
        self.assertIn(".rl-difficulty-row {\n  margin: 4px 0 12px;", self.css)
        self.assertIn(
            ".rl-feed-card__body-inner > .rl-difficulty-row + .rl-feed-card__section",
            self.css,
        )

    def test_r5_mobile_expanded_title_unclamped(self) -> None:
        self.assertIn(
            ".rl-feed-list .rl-lead-card.is-expanded .rl-lead-card__title span",
            self.css,
        )
        block = re.search(
            r"\.rl-feed-list \.rl-lead-card\.is-expanded \.rl-lead-card__title span\s*\{[^}]+\}",
            self.css,
        )
        self.assertIsNotNone(block)
        assert block is not None
        self.assertIn("-webkit-line-clamp: unset", block.group(0))

    def test_theme_bump(self) -> None:
        php = _FUNCTIONS.read_text(encoding="utf-8")
        self.assertIn("RAWLEAD_CHILD_VERSION', '1.19.21'", php)

    def test_o203_glow_preserved(self) -> None:
        self.assertIn("@keyframes rl-draft-glow", self.css)
        self.assertIn(".rl-lead-card--draft-pending", self.css)


class TestO220CheckoutProbe(unittest.TestCase):
    def test_yookassa_available_with_keys(self) -> None:
        cfg = _cfg()
        self.assertTrue(yookassa_available(cfg))

    @patch("yookassa_billing._api_request")
    def test_create_checkout_returns_https_yookassa_host(self, mock_api: MagicMock) -> None:
        mock_api.return_value = {
            "id": "pay-1",
            "confirmation": {
                "confirmation_url": "https://yoomoney.ru/checkout/payments/v2/contract?orderId=test",
            },
        }
        cfg = _cfg()
        cur = MagicMock()
        cur.fetchone.side_effect = [
            (None, None, None, None, None),
            None,
        ]
        result = create_checkout(cfg, cur, "00000000-0000-4000-8000-000000000001", "subscription")
        url = result["confirmation_url"]
        self.assertTrue(url.startswith("https://"))
        self.assertTrue(_checkout_hosts_ok(url), msg=url)

    @patch("yookassa_billing._api_request")
    def test_create_checkout_missing_url_raises(self, mock_api: MagicMock) -> None:
        mock_api.return_value = {"id": "pay-2", "confirmation": {}}
        cfg = _cfg()
        cur = MagicMock()
        cur.fetchone.side_effect = [
            (None, None, None, None, None),
            None,
        ]
        with self.assertRaises(CheckoutError) as ctx:
            create_checkout(cfg, cur, "00000000-0000-4000-8000-000000000001", "subscription")
        self.assertEqual(ctx.exception.code, "gateway_error")


if __name__ == "__main__":
    unittest.main()
