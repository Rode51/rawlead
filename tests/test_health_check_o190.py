"""O190 t0f: Telethon health check must not asyncio.run on radar main thread."""

from __future__ import annotations

import asyncio
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from health_check import TelethonHealthResult, check_telethon_account_sync, run_health_check  # noqa: E402


class TestHealthCheckO190(unittest.TestCase):
    def test_check_telethon_account_sync_runs_off_caller_thread(self) -> None:
        caller_tid = threading.get_ident()
        run_tids: list[int] = []

        async def _fake_check() -> TelethonHealthResult:
            run_tids.append(threading.get_ident())
            return TelethonHealthResult(True, "acc1", "ok")

        with patch("health_check.check_telethon_account", _fake_check):
            result = check_telethon_account_sync()

        self.assertTrue(result.ok)
        self.assertEqual(len(run_tids), 1)
        self.assertNotEqual(run_tids[0], caller_tid)

    def test_run_health_check_no_asyncio_run_on_main(self) -> None:
        caller_tid = threading.get_ident()
        asyncio_run_tids: list[int] = []
        real_run = asyncio.run

        def _track_run(coro):
            asyncio_run_tids.append(threading.get_ident())
            return real_run(coro)

        cfg = MagicMock()
        cfg.radar_log_path = Path("/tmp/radar_test.log")
        storage = MagicMock()
        storage.get_setting.side_effect = lambda key, default="0": {
            "health_check_last_run": "0",
            "health_check_last_ok": "1",
            "health_check_last_alert_issue": "",
            "health_check_last_alert_at": "0",
        }.get(key, default)

        ok_result = TelethonHealthResult(True, "acc1", "ok")
        with patch("health_check.is_tg_monitor_active", return_value=False):
            with patch("health_check.asyncio.run", side_effect=_track_run):
                with patch(
                    "health_check.check_telethon_account_sync",
                    return_value=ok_result,
                ):
                    result = run_health_check(cfg, storage, log_path=cfg.radar_log_path, force=True)

        self.assertTrue(result.ok)
        self.assertEqual(asyncio_run_tids, [])
        self.assertEqual(threading.get_ident(), caller_tid)


if __name__ == "__main__":
    unittest.main()
