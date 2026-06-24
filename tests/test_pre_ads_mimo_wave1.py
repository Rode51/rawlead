"""PRE-ADS-MIMO Wave 1: pool, webhook digest, draft feed-membership."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from src import api_server  # noqa: E402
from src.api_server import (  # noqa: E402
    _lead_in_user_feed,
    _passes_min_match,
    app,
)
from src.config import Config  # noqa: E402
from src.pg_storage import NeonLeadStorage, bind_pg_connection_pool  # noqa: E402

_USER = "00000000-0000-0000-0000-000000000201"
_LEAD_ID = 9001

_LEAD_ROW = (
    _LEAD_ID,
    "kwork",
    "Test lead",
    "body",
    "https://kwork.ru/1",
    "5000",
    80,
    "Брать",
    '["design"]',
    "[]",
    None,
    "design",
    "Need design",
    "[]",
    "",
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
        ai_enabled=True,
        ai_api_key="test-key",
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
        yookassa_webhook_secret="wh_secret_32_chars_long_enough",
        yookassa_save_payment_method=False,
    )
    base.update(overrides)
    return Config(**base)  # type: ignore[arg-type]


class TestYookassaWebhookDigest(unittest.TestCase):
    @patch("src.api_server.handle_webhook_notification", return_value=True)
    @patch("src.api_server.yookassa_available", return_value=True)
    @patch("src.api_server.load_config")
    def test_bad_secret_forbidden(
        self,
        mock_cfg: MagicMock,
        _avail: MagicMock,
        mock_handle: MagicMock,
    ) -> None:
        mock_cfg.return_value = _cfg()
        client = TestClient(app)
        resp = client.post(
            "/v1/webhooks/yookassa",
            json={"event": "payment.succeeded", "object": {"id": "pay-1"}},
            headers={"X-Yookassa-Webhook-Secret": "wrong"},
        )
        self.assertEqual(resp.status_code, 403)
        mock_handle.assert_not_called()

    @patch("src.api_server.handle_webhook_notification", return_value=True)
    @patch("src.api_server.yookassa_available", return_value=True)
    @patch("src.api_server.load_config")
    def test_good_secret_unchanged(
        self,
        mock_cfg: MagicMock,
        _avail: MagicMock,
        mock_handle: MagicMock,
    ) -> None:
        secret = "wh_secret_32_chars_long_enough"
        mock_cfg.return_value = _cfg(yookassa_webhook_secret=secret)
        client = TestClient(app)
        body = {"event": "payment.succeeded", "object": {"id": "pay-1"}}
        resp = client.post(
            "/v1/webhooks/yookassa",
            json=body,
            headers={"X-Yookassa-Webhook-Secret": secret},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok"})
        mock_handle.assert_called_once()
        self.assertEqual(mock_handle.call_args[0][1], body)


class TestMeAuthRequired(unittest.TestCase):
    def test_me_feed_without_bearer_401(self) -> None:
        client = TestClient(app)
        resp = client.get("/v1/me/feed")
        self.assertEqual(resp.status_code, 401)

    def test_me_feed_owner_header_without_bearer_401(self) -> None:
        client = TestClient(app)
        resp = client.get(
            "/v1/me/feed",
            headers={"X-RawLead-User-Id": "00000000-0000-0000-0000-000000000001"},
        )
        self.assertEqual(resp.status_code, 401)


class TestDraftFeedMembership(unittest.TestCase):
    def test_lead_not_in_feed_when_km_zero(self) -> None:
        cur = MagicMock()
        with (
            patch.object(api_server, "_fetch_visible_lead", return_value=_LEAD_ROW),
            patch.object(api_server, "_load_user_tags", return_value={"python": 1.0}),
            patch.object(api_server, "_keyword_match_for_user", return_value=0),
        ):
            self.assertFalse(_lead_in_user_feed(cur, _USER, _LEAD_ID))

    def test_lead_in_feed_when_km_positive(self) -> None:
        cur = MagicMock()
        with (
            patch.object(api_server, "_fetch_visible_lead", return_value=_LEAD_ROW),
            patch.object(api_server, "_load_user_tags", return_value={"python": 1.0}),
            patch.object(api_server, "_keyword_match_for_user", return_value=42),
            patch.object(api_server, "_passes_min_match", wraps=_passes_min_match),
        ):
            self.assertTrue(_lead_in_user_feed(cur, _USER, _LEAD_ID))

    @patch("src.api_server.submit_draft")
    @patch("src.api_server.draft_rate_limit_retry_after", return_value=None)
    @patch("src.api_server.load_config")
    @patch.object(api_server, "_db_conn")
    def test_draft_post_rejects_non_member(
        self,
        mock_db: MagicMock,
        mock_cfg: MagicMock,
        _rate: MagicMock,
        mock_submit: MagicMock,
    ) -> None:
        mock_cfg.return_value = _cfg()
        conn = MagicMock()
        cur = MagicMock()
        mock_db.return_value.__enter__.return_value = conn
        conn.cursor.return_value.__enter__.return_value = cur

        def _fake_user() -> str:
            return _USER

        app.dependency_overrides[api_server._resolve_user_id] = _fake_user
        try:
            with patch.object(api_server, "_lead_in_user_feed", return_value=False):
                client = TestClient(app)
                resp = client.post(f"/v1/me/leads/{_LEAD_ID}/draft")
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(resp.status_code, 404)
        mock_submit.assert_not_called()


class TestPgStoragePool(unittest.TestCase):
    def test_connection_uses_bound_pool(self) -> None:
        pool = MagicMock()
        conn = MagicMock()
        pool.connection.return_value.__enter__.return_value = conn
        bind_pg_connection_pool(pool)
        try:
            storage = NeonLeadStorage("postgresql://test")
            with (
                patch("src.pg_storage._ensure_leads_columns"),
                patch("src.pg_storage._ensure_user_tags_columns"),
                patch("src.pg_storage.psycopg.connect") as bare_connect,
            ):
                with storage.connection() as got:
                    self.assertIs(got, conn)
                bare_connect.assert_not_called()
                pool.connection.assert_called_once()
        finally:
            bind_pg_connection_pool(None)

    def test_api_server_has_no_bare_connect_except_fallback(self) -> None:
        text = Path(api_server.__file__).read_text(encoding="utf-8")
        hits = [
            line.strip()
            for line in text.splitlines()
            if "psycopg.connect(_db_url()" in line
        ]
        self.assertEqual(len(hits), 1)


if __name__ == "__main__":
    unittest.main()
