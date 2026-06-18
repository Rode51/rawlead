"""O205-t10: manual delist runs in background — no HTTP 504."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from owner_admin import run_ops_control  # noqa: E402


def test_delist_run_returns_immediately() -> None:
    def slow_delist() -> tuple[bool, str]:
        time.sleep(5)
        return True, "delist: checked=1 delisted=0 skipped=0"

    with patch("owner_admin._run_delist_batch_ops", side_effect=slow_delist):
        t0 = time.monotonic()
        result = run_ops_control(target="delist", action="run")
        elapsed = time.monotonic() - t0

    assert result["ok"] is True
    assert "фоне" in result["message"]
    assert elapsed < 2.0
