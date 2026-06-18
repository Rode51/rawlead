"""O262g: YouDo stuck invisible leads — requeue + drain priority."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from lead_pipeline import (  # noqa: E402
    _youdo_detail_fetch_enabled,
    _youdo_detail_short_skips_l1,
    _youdo_stuck_l1_since,
    drain_l1_backlog,
)
from listing import SOURCE_YOUDO, ListingProject  # noqa: E402
from pg_storage import NeonLeadRow  # noqa: E402


def test_youdo_detail_fetch_disabled_skips_l1_gate() -> None:
    os.environ["YOUDO_DETAIL_FETCH"] = "0"
    assert not _youdo_detail_fetch_enabled()
    project = ListingProject(
        project_id=14868001,
        title="Dev task",
        budget_text="10 000",
        url="https://youdo.com/t14868001",
        published_at="",
        listing_snippet="short listing",
        source=SOURCE_YOUDO,
    )
    assert not _youdo_detail_short_skips_l1(project, "short listing", detail_ok=None)


def test_youdo_stuck_since_default() -> None:
    os.environ.pop("YOUDO_STUCK_L1_SINCE", None)
    assert _youdo_stuck_l1_since() == "2026-06-15"


@patch("ai_analyze.analyze_lite")
def test_drain_l1_backlog_prioritizes_youdo_invisible(mock_lite: MagicMock) -> None:
    mock_lite.return_value = None
    youdo_row = NeonLeadRow(
        lead_id=9001,
        source="youdo",
        external_id="14868001",
        title="YouDo stuck",
        body="listing snippet body",
        url="https://youdo.com/t14868001",
        budget_text="5000",
        category="",
    )
    fl_row = NeonLeadRow(
        lead_id=9000,
        source="fl",
        external_id="999",
        title="FL",
        body="body",
        url="https://fl.ru/999",
        budget_text="",
        category="",
    )
    pg = MagicMock()
    pg.enabled = True
    pg.fetch_youdo_invisible_missing_l1.return_value = [youdo_row]
    pg.fetch_leads_missing_l1.return_value = [fl_row, youdo_row]

    cfg = MagicMock()
    cfg.ai_active = True
    word_filter = MagicMock()
    word_filter.accepts_listing.return_value = True

    with patch.dict(os.environ, {"YOUDO_STUCK_L1_SINCE": "2026-06-15"}):
        n = drain_l1_backlog(cfg, pg, word_filter, errors=[], limit=5)

    pg.fetch_youdo_invisible_missing_l1.assert_called_once()
    assert pg.fetch_youdo_invisible_missing_l1.call_args.kwargs["since"] == "2026-06-15"
    assert mock_lite.call_count == 2
    first_call = mock_lite.call_args_list[0].kwargs
    assert first_call.get("title") == "YouDo stuck"
    assert n == 0


def test_requeue_youdo_stuck_dry_run_disabled() -> None:
    from pg_storage import NeonLeadStorage

    pg = NeonLeadStorage("")
    assert not pg.enabled
    stats = pg.requeue_youdo_stuck_l1(since="2026-06-15", dry_run=True)
    assert stats == {"candidates": 0, "requeued": 0}
