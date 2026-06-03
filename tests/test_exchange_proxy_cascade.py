"""Sticky cascade: per-source ban, 3-strike, смена слота."""

from __future__ import annotations



import os

import sys

import unittest

from pathlib import Path

from unittest.mock import MagicMock, patch



_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(_ROOT / "src"))



from exchange_proxy import (

    ExchangeFetchSession,

    _ban_url,

    _is_banned,

    _record_failure,

    _record_success,

    _shared_exchange_pool,

    exchange_fetch_begin,

    exchange_pool_health,

    reset_cascade_state_for_tests,

)





class TestExchangeProxyCascade(unittest.TestCase):

    def setUp(self) -> None:

        reset_cascade_state_for_tests()

        self._env = os.environ.copy()

        os.environ["EXCHANGE_PROXY_URLS"] = (

            "http://185.0.0.1:8000:u1:p1,"

            "http://194.0.0.2:8000:u2:p2,"

            "http://212.0.0.3:8000:u3:p3"

        )

        os.environ["FL_PROXY_URLS"] = ""

        os.environ["KWORK_PROXY_URLS"] = ""

        os.environ["EXCHANGE_PROXY_URLS_SECONDARY"] = ""



    def tearDown(self) -> None:

        os.environ.clear()

        os.environ.update(self._env)

        reset_cascade_state_for_tests()



    def test_shared_pool_order(self) -> None:

        urls = _shared_exchange_pool()

        self.assertEqual(len(urls), 3)

        self.assertIn("185.0.0.1", urls[0])



    def test_sticky_same_slot_on_begin(self) -> None:

        s1 = exchange_fetch_begin("fl")

        s2 = exchange_fetch_begin("fl")

        self.assertEqual(s1.slot, s2.slot)



    def test_three_strikes_then_switch(self) -> None:

        url = _shared_exchange_pool()[0]

        self.assertFalse(_record_failure(url, source="fl"))

        self.assertFalse(_record_failure(url, source="fl"))

        self.assertTrue(_record_failure(url, source="fl"))



    def test_http_403_bans_after_two_strikes(self) -> None:

        url = _shared_exchange_pool()[1]

        self.assertFalse(_record_failure(url, source="kwork", http_code=403))

        self.assertTrue(_record_failure(url, source="kwork", http_code=403))



    def test_per_source_ban_isolated(self) -> None:

        url = _shared_exchange_pool()[0]

        _ban_url(url, source="pchyol", reason="http_403", slot_idx=0)

        self.assertTrue(_is_banned(url, "pchyol"))

        self.assertFalse(_is_banned(url, "fl"))



    def test_success_clears_strikes(self) -> None:

        url = _shared_exchange_pool()[0]

        _record_failure(url, source="fl")

        _record_failure(url, source="fl")

        _record_success(url, "fl")

        self.assertFalse(_record_failure(url, source="fl"))



    def test_advance_failover_moves_slot(self) -> None:

        urls = _shared_exchange_pool()

        session = ExchangeFetchSession(pool_key="fl", source="fl", urls=urls, slot=0)

        _ban_url(urls[0], source="fl", reason="test")

        ok = session.advance_failover(reason="test")

        self.assertTrue(ok)

        self.assertNotEqual(session.slot, 0)



    def test_pool_health_after_ban(self) -> None:

        urls = _shared_exchange_pool()

        n = len(urls)

        _ban_url(urls[0], source="fl", reason="test")

        alive, total = exchange_pool_health("fl")

        self.assertEqual(total, n)

        self.assertEqual(alive, n - 1)



    @patch("exchange_proxy._send_owner_proxy_alert")

    @patch("exchange_proxy.requests.get")

    def test_exchange_get_failover_on_403(

        self, mock_get: MagicMock, mock_alert: MagicMock

    ) -> None:

        from exchange_proxy import exchange_get, exchange_fetch_end



        resp_bad = MagicMock(status_code=403)

        resp_ok = MagicMock(status_code=200)

        mock_get.side_effect = [resp_bad, resp_ok]



        exchange_fetch_begin("kwork")

        out = exchange_get("kwork", "https://example.com", headers={})

        exchange_fetch_end("kwork")

        self.assertEqual(out.status_code, 200)

        self.assertEqual(mock_get.call_count, 2)

        mock_alert.assert_called()



    @patch("exchange_proxy._storage")

    def test_ban_persisted_to_storage(self, mock_storage: MagicMock) -> None:

        from exchange_proxy import _ban_url, _load_persistence, _persist_bans



        st = MagicMock()

        saved: dict[str, str] = {}



        def _set(key: str, val: str) -> None:

            saved[key] = val



        st.get_setting.side_effect = lambda k, d="": saved.get(k, d)

        st.set_setting.side_effect = _set

        mock_storage.return_value = st



        url = _shared_exchange_pool()[0]

        _ban_url(url, source="fl", reason="http_403", slot_idx=0)

        _persist_bans()

        self.assertIn("exchange_proxy_bans_v2", saved)



        reset_cascade_state_for_tests()

        _load_persistence()

        self.assertTrue(_is_banned(url, "fl"))

        self.assertFalse(_is_banned(url, "kwork"))





if __name__ == "__main__":

    unittest.main()

