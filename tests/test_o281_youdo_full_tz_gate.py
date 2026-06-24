"""YOUDO-SOURCE-GATE rev2: detail_ok=True → pass, else → delist."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from lead_pipeline import (  # noqa: E402
    _youdo_detail_short_skips_l1,
    plan_new_listing,
)
from listing import SOURCE_YOUDO, ListingProject  # noqa: E402


def _youdo_project(**kwargs) -> ListingProject:
    defaults = dict(
        project_id=14868001,
        title="Dev task",
        budget_text="10 000",
        url="https://youdo.com/t14868001",
        published_at="",
        listing_snippet="short listing",
        source=SOURCE_YOUDO,
    )
    defaults.update(kwargs)
    return ListingProject(**defaults)


def test_gate_skips_when_detail_ok_false() -> None:
    project = _youdo_project()
    assert _youdo_detail_short_skips_l1(project, "short listing", detail_ok=False)


def test_gate_skips_when_detail_ok_none() -> None:
    """DETAIL_FETCH=0 → detail_ok=None must still skip."""
    project = _youdo_project()
    assert _youdo_detail_short_skips_l1(project, "short listing", detail_ok=None)


def test_gate_passes_when_detail_ok_true_any_length() -> None:
    """Rev2: detail_ok=True passes regardless of body length."""
    project = _youdo_project()
    assert not _youdo_detail_short_skips_l1(project, "x" * 50, detail_ok=True)
    assert not _youdo_detail_short_skips_l1(project, "x" * 300, detail_ok=True)
    assert not _youdo_detail_short_skips_l1(project, "full tz " * 50, detail_ok=True)


def test_gate_non_youdo_always_passes() -> None:
    from listing import SOURCE_FL

    project = _youdo_project(source=SOURCE_FL)
    assert not _youdo_detail_short_skips_l1(project, "short", detail_ok=False)


@patch("lead_pipeline._rollup_after_lite")
@patch("lead_pipeline.fetch_project_detail", return_value=("stub", "", False))
@patch(
    "lead_pipeline._insert_neon_after_gates",
    return_value=(True, False, False, False),
)
def test_ingest_detail_fail_not_visible_no_l1(
    mock_neon: MagicMock,
    mock_detail: MagicMock,
    mock_rollup: MagicMock,
) -> None:
    os.environ["YOUDO_DETAIL_MIN_CHARS"] = "300"
    os.environ["YOUDO_DETAIL_FETCH"] = "1"
    project = _youdo_project()
    storage = MagicMock()
    storage.try_record_new.return_value = True
    storage.try_record_content_fingerprint.return_value = True
    pg = MagicMock()
    pg.enabled = True
    pg.lead_exists.return_value = False
    pg.fetch_lead_id.return_value = 42
    word_filter = MagicMock()
    word_filter.accepts_listing.return_value = True
    cfg = MagicMock()
    cfg.ai_active = True
    cfg.ai_uses_l1_l2 = True
    cfg.radar_profile = "site"
    cfg.neon_ingest_wide = True
    cfg.min_budget_rub = 0
    cfg.filter_wide = False
    cfg.radar_log_path = Path("/tmp/radar.log")
    errors: list[str] = []

    with patch("lead_pipeline.is_public_feed_source", return_value=True):
        was_new, plan = plan_new_listing(
            project,
            storage,
            word_filter,
            cfg,
            errors=errors,
            pg=pg,
        )

    assert was_new
    assert plan is None
    assert any("pipeline:skip youdo:id=14868001 no_detail" in e for e in errors)
    pg.delist_lead.assert_called_once_with(
        42,
        reason="youdo_no_detail",
        errors=errors,
    )
    mock_rollup.assert_not_called()


@patch("lead_pipeline._rollup_after_lite")
@patch("lead_pipeline.fetch_project_detail")
@patch(
    "lead_pipeline._insert_neon_after_gates",
    return_value=(True, False, False, False),
)
def test_ingest_detail_fetch_disabled_skips_l1(
    mock_neon: MagicMock,
    mock_detail: MagicMock,
    mock_rollup: MagicMock,
) -> None:
    """YOUDO_DETAIL_FETCH=0 must not open L1 on listing snippet."""
    os.environ["YOUDO_DETAIL_MIN_CHARS"] = "300"
    os.environ["YOUDO_DETAIL_FETCH"] = "0"
    project = _youdo_project()
    storage = MagicMock()
    storage.try_record_new.return_value = True
    storage.try_record_content_fingerprint.return_value = True
    pg = MagicMock()
    pg.enabled = True
    pg.lead_exists.return_value = False
    pg.fetch_lead_id.return_value = 99
    word_filter = MagicMock()
    word_filter.accepts_listing.return_value = True
    cfg = MagicMock()
    cfg.ai_active = True
    cfg.ai_uses_l1_l2 = True
    cfg.radar_profile = "site"
    cfg.neon_ingest_wide = True
    cfg.min_budget_rub = 0
    cfg.filter_wide = False
    cfg.radar_log_path = Path("/tmp/radar.log")
    errors: list[str] = []

    with patch("lead_pipeline.is_public_feed_source", return_value=True):
        was_new, plan = plan_new_listing(
            project,
            storage,
            word_filter,
            cfg,
            errors=errors,
            pg=pg,
        )

    mock_detail.assert_not_called()
    assert was_new
    assert plan is None
    assert any("no_detail" in e for e in errors)
    pg.delist_lead.assert_called_once()
    mock_rollup.assert_not_called()
