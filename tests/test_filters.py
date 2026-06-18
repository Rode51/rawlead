"""O213: exchange-safe L2 stops for kwork/fl (TG path unchanged)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from filters import ListingWordFilter  # noqa: E402
from listing import ListingProject, SOURCE_FL, SOURCE_KWORK  # noqa: E402


@pytest.fixture
def wide_filter() -> ListingWordFilter:
    return ListingWordFilter(
        take=("лендинг", "сайт", "разработка"),
        stop=("логотип", "вебинар", "реклама"),
    )


def _project(
    *,
    source: str,
    title: str,
    snippet: str = "",
    project_id: int = 1,
) -> ListingProject:
    return ListingProject(
        project_id=project_id,
        title=title,
        budget_text="",
        url=f"https://example.test/projects/{project_id}/view",
        published_at="2026-06-14",
        listing_snippet=snippet,
        source=source,
    )


def test_kwork_passes_logo_stop(wide_filter: ListingWordFilter) -> None:
    project = _project(
        source=SOURCE_KWORK,
        title="Сделать логотип для стартапа",
        snippet="нужен логотип в figma",
    )
    assert wide_filter.accepts_listing(project, wide=True)


def test_fl_passes_webinar_stop(wide_filter: ListingWordFilter) -> None:
    project = _project(
        source=SOURCE_FL,
        title="Настроить вебинарную воронку",
        snippet="GetCourse + лендинг",
    )
    assert wide_filter.accepts_listing(project, wide=True)


def test_tg_logo_still_blocked_without_order_markers(
    wide_filter: ListingWordFilter,
) -> None:
    project = _project(
        source="tg:-1001234567890",
        title="Предлагаю услуги — логотип",
        snippet="портфолио в личке",
    )
    assert not wide_filter.accepts_listing(project, wide=True)


def test_tg_logo_passes_with_order_markers(wide_filter: ListingWordFilter) -> None:
    project = _project(
        source="tg:-1001234567890",
        title="Ищу дизайнера на логотип",
        snippet="Задача: сделать логотип для проекта. Откликнуться в личку.",
    )
    assert wide_filter.accepts_listing(project, wide=True)


def test_exchange_safe_logs_once(wide_filter: ListingWordFilter) -> None:
    project = _project(
        source=SOURCE_KWORK,
        title="Логотип и баннер",
        project_id=3196905,
    )
    with patch("filters._log_exchange_filter_safe") as mock_log:
        assert wide_filter.accepts_listing(project, wide=True)
        mock_log.assert_called_once()
        assert mock_log.call_args.args[1] == "логотип"
