"""O155: Healthchecks.io ping after site-cycle."""

from __future__ import annotations

import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

import healthchecks as hc  # noqa: E402
from public_feed import public_feed_sources  # noqa: E402
from radar_cycle_log import CycleSummary, SourceCycleStats  # noqa: E402


class TestHealthchecks(unittest.TestCase):
    def setUp(self) -> None:
        self._env = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)
        public_feed_sources.cache_clear()

    def test_noop_when_url_empty(self) -> None:
        os.environ.pop("HEALTHCHECKS_SITE_URL", None)
        summary = CycleSummary(ts="2026-06-08")
        with patch.object(hc, "_fire_get") as fire:
            hc.ping_after_site_cycle(summary)
        fire.assert_not_called()

    @patch("healthchecks._fire_get")
    def test_pings_success_after_ok_cycle(self, fire: MagicMock) -> None:
        os.environ["HEALTHCHECKS_SITE_URL"] = "https://hc-ping.com/test-uuid"
        summary = CycleSummary(ts="2026-06-08")
        summary.ensure("fl").downloaded = 3
        hc.ping_after_site_cycle(summary)
        fire.assert_called_once_with("https://hc-ping.com/test-uuid")

    @patch("healthchecks._fire_get")
    def test_pings_success_when_only_youdo_ok(self, fire: MagicMock) -> None:
        os.environ["HEALTHCHECKS_SITE_URL"] = "https://hc-ping.com/test-uuid"
        os.environ["PUBLIC_FEED_SOURCES"] = "fl,kwork,youdo"
        public_feed_sources.cache_clear()
        summary = CycleSummary(ts="2026-06-08")
        summary.ensure("fl").fetch_error = "HTTP 403"
        summary.ensure("kwork").fetch_error = "antibot"
        summary.ensure("youdo").downloaded = 2
        hc.ping_after_site_cycle(summary)
        fire.assert_called_once_with("https://hc-ping.com/test-uuid")

    @patch("healthchecks._fire_get")
    def test_skips_success_when_all_web_failed(self, fire: MagicMock) -> None:
        os.environ["HEALTHCHECKS_SITE_URL"] = "https://hc-ping.com/test-uuid"
        summary = CycleSummary(ts="2026-06-08")
        summary.ensure("fl").fetch_error = "HTTP 403"
        summary.ensure("youdo").fetch_error = "antibot"
        hc.ping_after_site_cycle(summary)
        fire.assert_not_called()

    @patch("healthchecks._fire_get")
    def test_fail_url_when_all_web_failed(self, fire: MagicMock) -> None:
        os.environ["HEALTHCHECKS_SITE_URL"] = "https://hc-ping.com/test-uuid"
        os.environ["HEALTHCHECKS_SITE_FAIL_URL"] = "https://hc-ping.com/test-uuid/fail"
        summary = CycleSummary(ts="2026-06-08")
        summary.ensure("fl").fetch_error = "HTTP 403"
        hc.ping_after_site_cycle(summary)
        fire.assert_called_once_with("https://hc-ping.com/test-uuid/fail")

    @patch("healthchecks._tg_monitor_alive", return_value=True)
    @patch("healthchecks._fire_get")
    def test_pings_success_when_tg_alive_despite_web_fail(
        self, fire: MagicMock, _tg: MagicMock
    ) -> None:
        os.environ["HEALTHCHECKS_SITE_URL"] = "https://hc-ping.com/test-uuid"
        os.environ["HEALTHCHECKS_SITE_FAIL_URL"] = "https://hc-ping.com/test-uuid/fail"
        summary = CycleSummary(ts="2026-06-08")
        summary.ensure("fl").fetch_error = "HTTP 403"
        summary.ensure("youdo").fetch_error = "pool_exhausted"
        storage = MagicMock()
        hc.ping_after_site_cycle(summary, storage)
        fire.assert_called_once_with("https://hc-ping.com/test-uuid")

    @patch("requests.get")
    def test_fire_get_background(self, mock_get: MagicMock) -> None:
        os.environ["HEALTHCHECKS_SITE_URL"] = "https://hc-ping.com/x"
        hc._fire_get("https://hc-ping.com/x")
        deadline = time.time() + 2.0
        while time.time() < deadline:
            if mock_get.called:
                break
            time.sleep(0.05)
        mock_get.assert_called_once_with(
            "https://hc-ping.com/x",
            timeout=10,
            headers={"User-Agent": "RawLead-Radar/1.0 (healthchecks-ping)"},
        )


if __name__ == "__main__":
    unittest.main()
