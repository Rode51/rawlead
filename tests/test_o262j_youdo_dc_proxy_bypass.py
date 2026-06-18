"""O262j: YOUDO_DC_PROXY_URLS must not bypass YOUDO_O191_DC_SLOTS=0."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from exchange_proxy import (  # noqa: E402
    _youdo_dc_pool,
    reset_cascade_state_for_tests,
    youdo_dc_pool_size,
)


class TestO262jDcProxyBypass(unittest.TestCase):
    def setUp(self) -> None:
        self._env = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)
        reset_cascade_state_for_tests()

    def test_explicit_dc_urls_ignored_when_slots_zero(self) -> None:
        os.environ["YOUDO_O191_DC_SLOTS"] = "0"
        os.environ["YOUDO_DC_PROXY_URLS"] = (
            "http://185.147.131.15:8000:u1:p1,"
            "http://185.147.131.16:8000:u2:p2,"
            "http://185.147.131.17:8000:u3:p3,"
            "http://185.147.131.18:8000:u4:p4"
        )
        reset_cascade_state_for_tests()
        self.assertEqual(_youdo_dc_pool(), [])
        self.assertEqual(youdo_dc_pool_size(), 0)

    def test_explicit_dc_urls_used_when_slots_positive(self) -> None:
        os.environ["YOUDO_O191_DC_SLOTS"] = "4"
        dc_urls = (
            "http://185.147.131.15:8000:u1:p1,"
            "http://185.147.131.16:8000:u2:p2"
        )
        os.environ["YOUDO_DC_PROXY_URLS"] = dc_urls
        reset_cascade_state_for_tests()
        self.assertEqual(len(_youdo_dc_pool()), 2)


if __name__ == "__main__":
    unittest.main()
