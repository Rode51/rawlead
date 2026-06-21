"""O223: YouDo physical-service guard + short detail gate."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from ai_analyze import AiLiteAnalysis, _finalize_lite_analysis, analyze_lite  # noqa: E402
from lead_pipeline import (  # noqa: E402
    _apply_physical_pre_l1,
    _youdo_detail_short_skips_l1,
    plan_new_listing,
)
from listing import SOURCE_YOUDO, ListingProject  # noqa: E402
from vacancy_filter import (  # noqa: E402
    is_physical_service_job,
    physical_service_lite_analysis,
)

_T14857148_TITLE = "Гидроборт. Москва - Городец"
_T14857148_SNIPPET = (
    "Доставить паллету с грузом. Москва — Городец. Нужен гидроборт."
)[:100]


def test_physical_repro_t14857148() -> None:
    assert is_physical_service_job(_T14857148_TITLE, _T14857148_SNIPPET)


def test_dev_courier_api_not_physical() -> None:
    title = "Интеграция API курьерской службы в CRM"
    body = "Разработать REST API для подключения курьеров к сайту на Python."
    assert not is_physical_service_job(title, body)


def test_physical_courier_delivery_is_physical() -> None:
    assert is_physical_service_job("Курьерская доставка документов", "По Москве, срочно")


def test_physical_lite_hidden_no_tags() -> None:
    lite = physical_service_lite_analysis(
        title=_T14857148_TITLE,
        body=_T14857148_SNIPPET,
    )
    assert lite is not None
    assert lite.feed_visible is False
    assert lite.lead_tags == ()
    assert "физическая" in lite.task_summary.casefold()
    assert "wordpress" not in lite.task_summary.casefold()


def test_youdo_long_listing_snippet_still_fetches_detail() -> None:
    """O223+: long listing snippet must not skip detail fetch (t14878013 class)."""
    from unittest.mock import MagicMock, patch

    from lead_pipeline import _resolve_ingest_body

    project = ListingProject(
        project_id=14878013,
        title="Закрытый парсинг",
        budget_text="400",
        url="https://youdo.com/t14878013",
        published_at="",
        listing_snippet="x" * 350,
        source=SOURCE_YOUDO,
    )
    cfg = MagicMock()
    errors: list[str] = []
    with patch("lead_pipeline._youdo_detail_fetch_enabled", return_value=True):
        with patch(
            "lead_pipeline.fetch_project_detail",
            return_value=("detail text " * 20, "<html></html>", True),
        ) as mock_fetch:
            body, _, detail_ok = _resolve_ingest_body(project, cfg, errors)
            mock_fetch.assert_called_once()
            assert detail_ok is True
            assert "detail text" in body


def test_youdo_detail_short_skips_l1() -> None:
    project = ListingProject(
        project_id=14857148,
        title="Dev bot",
        budget_text="10 000",
        url="https://youdo.com/t14857148",
        published_at="",
        listing_snippet="short",
        source=SOURCE_YOUDO,
    )
    os.environ["YOUDO_DETAIL_MIN_CHARS"] = "300"
    assert _youdo_detail_short_skips_l1(project, "short", detail_ok=False)
    assert not _youdo_detail_short_skips_l1(project, "short", detail_ok=True)
    assert not _youdo_detail_short_skips_l1(project, "x" * 350, detail_ok=False)


def test_finalize_lite_overrides_dev_physical() -> None:
    bad = AiLiteAnalysis(
        feed_visible=True,
        task_summary="WordPress + API интеграция",
        lead_tags=("wordpress_dev", "api_integration"),
        ai_reasons=("галлюцинация",),
        complexity=2,
        primary_category="dev",
    )
    out = _finalize_lite_analysis(
        bad,
        title=_T14857148_TITLE,
        snippet=_T14857148_SNIPPET,
    )
    assert out.feed_visible is False
    assert out.lead_tags == ()
    assert "wordpress_dev" not in out.lead_tags


@patch("lead_pipeline._rollup_after_lite")
def test_apply_physical_pre_l1_updates_neon(mock_rollup: MagicMock) -> None:
    project = ListingProject(
        project_id=14857148,
        title=_T14857148_TITLE,
        budget_text="до 5 000 ₽",
        url="https://youdo.com/t14857148",
        published_at="",
        listing_snippet=_T14857148_SNIPPET,
        source=SOURCE_YOUDO,
    )
    pg = MagicMock()
    cfg = MagicMock()
    errors: list[str] = []
    handled = _apply_physical_pre_l1(
        project,
        ingest_body=_T14857148_SNIPPET,
        cfg=cfg,
        pg=pg,
        errors=errors,
        stats=None,
        tz_attachment_meta=None,
    )
    assert handled
    pg.update_after_lite.assert_called_once()
    lite = pg.update_after_lite.call_args.kwargs["lite"]
    assert lite.feed_visible is False
    assert "physical_service" in errors[0]


@patch("ai_analyze._call_lite_once")
def test_analyze_lite_physical_skips_openrouter(mock_lite: MagicMock) -> None:
    cfg = MagicMock()
    cfg.ai_active = True
    cfg.ai_provider = "openrouter"
    out = analyze_lite(
        cfg,
        title=_T14857148_TITLE,
        budget_text="5 000",
        snippet=_T14857148_SNIPPET,
        url="https://youdo.com/t14857148",
    )
    mock_lite.assert_not_called()
    assert out is not None
    assert out.feed_visible is False


@patch("lead_pipeline._rollup_after_lite")
@patch("lead_pipeline.fetch_project_detail", return_value=("stub", "", False))
@patch(
    "lead_pipeline._insert_neon_after_gates",
    return_value=(True, False, False, False),
)
def test_reingest_t14857148_not_visible(
    mock_neon: MagicMock,
    mock_detail: MagicMock,
    mock_rollup: MagicMock,
) -> None:
    os.environ["YOUDO_DETAIL_MIN_CHARS"] = "300"
    project = ListingProject(
        project_id=14857148,
        title=_T14857148_TITLE,
        budget_text="до 5 000 ₽",
        url="https://youdo.com/t14857148",
        published_at="",
        listing_snippet=_T14857148_SNIPPET,
        source=SOURCE_YOUDO,
    )
    storage = MagicMock()
    storage.try_record_new.return_value = True
    storage.try_record_content_fingerprint.return_value = True
    pg = MagicMock()
    pg.enabled = True
    pg.lead_exists.return_value = False
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
    pg.update_after_lite.assert_called_once()
    lite = pg.update_after_lite.call_args.kwargs["lite"]
    assert lite.feed_visible is False
    assert lite.lead_tags == ()
    assert not any("wordpress" in t for t in lite.lead_tags)
