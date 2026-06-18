"""O218 quiz E2E — prod runner skipped unless RAWLEAD_O218_E2E=1."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts" / "preprod_playwright"))


def test_quiz_e2e_module_imports() -> None:
    import quiz_e2e  # noqa: F401

    assert hasattr(quiz_e2e, "run_quiz_e2e")
    assert "j1" in quiz_e2e.ALL_IDS
    assert "j7" in quiz_e2e.ALL_IDS


@pytest.mark.skipif(
    os.environ.get("RAWLEAD_O218_E2E") != "1",
    reason="prod quiz E2E — set RAWLEAD_O218_E2E=1",
)
def test_quiz_e2e_prod_runner() -> None:
    import quiz_e2e

    report = quiz_e2e.run_quiz_e2e(
        base_url=os.environ.get("RAWLEAD_O218_BASE_URL", "https://rawlead.ru"),
        viewport_name=os.environ.get("RAWLEAD_O218_VIEWPORT", "desktop"),
        headless=os.environ.get("RAWLEAD_O218_HEADED") != "1",
        timeout_ms=int(os.environ.get("RAWLEAD_O218_TIMEOUT_MS", "60000")),
    )
    assert report["pass"], report.get("results")
