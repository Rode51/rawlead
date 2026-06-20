"""O280 next E2E — prod runner skipped unless RAWLEAD_O280_E2E=1."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts" / "preprod_playwright"))


def test_next_e2e_module_imports() -> None:
    import next_e2e  # noqa: F401

    assert hasattr(next_e2e, "run_next_e2e")
    assert "n1" in next_e2e.SCENARIOS
    assert "n25" in next_e2e.SCENARIOS
    assert "n25" in next_e2e.DESKTOP_IDS


@pytest.mark.skipif(
    os.environ.get("RAWLEAD_O280_E2E") != "1",
    reason="prod next E2E — set RAWLEAD_O280_E2E=1",
)
def test_next_e2e_prod_runner() -> None:
    import next_e2e

    viewport = os.environ.get("RAWLEAD_O280_VIEWPORT", "desktop")
    ids = None
    if os.environ.get("RAWLEAD_O280_IDS"):
        ids = [x.strip() for x in os.environ["RAWLEAD_O280_IDS"].split(",") if x.strip()]

    report = next_e2e.run_next_e2e(
        base_url=os.environ.get("RAWLEAD_O280_BASE_URL", "https://rawlead.ru"),
        viewport_name=viewport,
        headless=os.environ.get("RAWLEAD_O280_HEADED") != "1",
        timeout_ms=int(os.environ.get("RAWLEAD_O280_TIMEOUT_MS", "60000")),
        ids=ids,
    )
    assert report["pass"], report.get("results")
