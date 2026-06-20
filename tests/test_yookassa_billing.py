"""O174b: YooKassa billing — trial gate + webhook idempotency."""

from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import Config  # noqa: E402
from yookassa_billing import (  # noqa: E402
    CheckoutError,
    _claim_payment_row,
    apply_payment_succeeded,
    cancel_subscription,
    confirm_pending_payment,
    handle_webhook_notification,
    process_auto_renewals,
    validate_checkout,
    yookassa_available,
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
        yookassa_webhook_secret="",
        yookassa_save_payment_method=False,
    )
    base.update(overrides)
    return Config(**base)  # type: ignore[arg-type]


class TestYookassaAvailable(unittest.TestCase):
    def test_available_with_keys(self) -> None:
        self.assertTrue(yookassa_available(_cfg()))

    def test_unavailable_without_secret(self) -> None:
        self.assertFalse(yookassa_available(_cfg(yookassa_secret_key="")))


class TestCheckoutGate(unittest.TestCase):
    def test_subscription_rejects_active_premium(self) -> None:
        cur = MagicMock()
        with patch(
            "yookassa_billing.fetch_subscription_row",
            return_value=("agent", True, object(), None, None, None),
        ):
            with patch("yookassa_billing.has_active_premium", return_value=True):
                with self.assertRaises(CheckoutError) as ctx:
                    validate_checkout(cur, "00000000-0000-0000-0000-000000000099", "subscription")
        self.assertEqual(ctx.exception.code, "already_premium")

    def test_subscription_allows_active_trial(self) -> None:
        cur = MagicMock()
        until = datetime.now(timezone.utc) + timedelta(days=2)
        with patch(
            "yookassa_billing.fetch_subscription_row",
            return_value=("trial", True, until, None, datetime.now(timezone.utc), None),
        ):
            validate_checkout(cur, "00000000-0000-0000-0000-000000000099", "subscription")

    def test_subscription_rejects_prepaid_during_trial(self) -> None:
        cur = MagicMock()
        until = datetime.now(timezone.utc) + timedelta(days=2)
        prepaid = until + timedelta(days=30)
        with patch(
            "yookassa_billing.fetch_subscription_row",
            return_value=("trial", True, until, None, datetime.now(timezone.utc), prepaid),
        ):
            with self.assertRaises(CheckoutError) as ctx:
                validate_checkout(cur, "00000000-0000-0000-0000-000000000099", "subscription")
        self.assertEqual(ctx.exception.code, "already_prepaid")


class TestWebhookIdempotency(unittest.TestCase):
    def test_apply_skips_already_succeeded(self) -> None:
        cur = MagicMock()
        cur.fetchone.side_effect = [
            None,
            ("succeeded", "user-1", "trial"),
            ("succeeded",),
        ]
        cfg = _cfg()
        payment = {
            "id": "pay-1",
            "status": "succeeded",
            "metadata": {"user_id": "user-1", "kind": "trial"},
            "amount": {"value": "1.00"},
        }
        self.assertTrue(apply_payment_succeeded(cfg, cur, payment))

    def test_claim_returns_none_when_processing(self) -> None:
        cur = MagicMock()
        cur.fetchone.side_effect = [
            None,
            ("processing", "user-1", "trial"),
        ]
        claimed = _claim_payment_row(cur, "pay-1", {"metadata": {"user_id": "user-1", "kind": "trial"}})
        self.assertIsNone(claimed)

    def test_concurrent_apply_only_one_claims(self) -> None:
        cfg = _cfg()
        payment = {
            "id": "pay-race",
            "status": "succeeded",
            "metadata": {"user_id": "00000000-0000-0000-0000-000000000099", "kind": "trial"},
            "amount": {"value": "1.00"},
        }
        cur_winner = MagicMock()
        cur_winner.fetchone.side_effect = [
            ("00000000-0000-0000-0000-000000000099", "trial"),
        ]
        cur_winner.rowcount = 1
        with patch("yookassa_billing._activate_trial"):
            self.assertTrue(apply_payment_succeeded(cfg, cur_winner, payment))

        cur_loser = MagicMock()
        cur_loser.fetchone.side_effect = [
            None,
            ("processing", "00000000-0000-0000-0000-000000000099", "trial"),
            ("processing",),
        ]
        self.assertFalse(apply_payment_succeeded(cfg, cur_loser, payment))

    def test_webhook_ignores_non_success_event(self) -> None:
        cfg = _cfg()
        self.assertFalse(
            handle_webhook_notification(cfg, {"event": "payment.canceled", "object": {}})
        )


class TestConfirmPayment(unittest.TestCase):
    def test_confirm_no_pending(self) -> None:
        cur = MagicMock()
        cur.fetchone.return_value = None
        cfg = _cfg()
        result = confirm_pending_payment(cfg, cur, "00000000-0000-0000-0000-000000000099")
        self.assertEqual(result["status"], "no_pending")

    @patch("yookassa_billing.apply_payment_succeeded", return_value=True)
    @patch("yookassa_billing.fetch_payment")
    def test_confirm_trial_succeeded(
        self, fetch_payment: MagicMock, apply_mock: MagicMock
    ) -> None:
        cur = MagicMock()
        cur.fetchone.return_value = ("pay-trial-1", "pending")
        fetch_payment.return_value = {
            "id": "pay-trial-1",
            "status": "succeeded",
            "metadata": {"user_id": "user-1", "kind": "trial"},
            "amount": {"value": "1.00"},
        }
        cfg = _cfg()
        result = confirm_pending_payment(cfg, cur, "user-1")
        self.assertEqual(result["status"], "activated")
        apply_mock.assert_called_once()

    @patch("yookassa_billing.apply_payment_succeeded", return_value=True)
    @patch("yookassa_billing.fetch_payment")
    def test_confirm_subscription_succeeded(
        self, fetch_payment: MagicMock, apply_mock: MagicMock
    ) -> None:
        cur = MagicMock()
        cur.fetchone.return_value = ("pay-sub-1", "pending")
        fetch_payment.return_value = {
            "id": "pay-sub-1",
            "status": "succeeded",
            "metadata": {"user_id": "user-1", "kind": "subscription"},
            "amount": {"value": "790.00"},
        }
        cfg = _cfg()
        result = confirm_pending_payment(cfg, cur, "user-1")
        self.assertEqual(result["status"], "activated")
        apply_mock.assert_called_once()

    def test_confirm_other_users_payment_is_no_pending(self) -> None:
        cur = MagicMock()
        cur.fetchone.return_value = None
        cfg = _cfg()
        result = confirm_pending_payment(
            cfg,
            cur,
            "00000000-0000-0000-0000-000000000001",
            payment_id="pay-other-user",
        )
        self.assertEqual(result["status"], "no_pending")
        sql = cur.execute.call_args[0][0]
        self.assertIn("user_id", sql)
        self.assertIn("yookassa_payment_id", sql)


class TestCancelSubscription(unittest.TestCase):
    def test_cancel_clears_autorenew_and_pm(self) -> None:
        cur = MagicMock()
        cur.rowcount = 1
        self.assertTrue(cancel_subscription(cur, "user-1"))
        sql = cur.execute.call_args[0][0]
        self.assertIn("auto_renew = FALSE", sql)
        self.assertIn("yookassa_payment_method_id = NULL", sql)
        self.assertIn("plan NOT IN ('owner')", sql)

    def test_cancel_noop_when_already_off(self) -> None:
        cur = MagicMock()
        cur.rowcount = 0
        self.assertFalse(cancel_subscription(cur, "user-1"))


class TestAutoRenewSkip(unittest.TestCase):
    def test_process_auto_renewals_skips_auto_renew_false(self) -> None:
        cur = MagicMock()
        cur.fetchall.return_value = []
        cfg = _cfg()
        self.assertEqual(process_auto_renewals(cfg, cur), 0)
        sql = cur.execute.call_args[0][0]
        self.assertIn("auto_renew = TRUE", sql)


if __name__ == "__main__":
    unittest.main()
