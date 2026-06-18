"""O257: FL auto httpx fallback when browser/subprocess fails or returns empty."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from fl_parser import _fetch_listing_html, _fl_httpx_auto_fallback_enabled  # noqa: E402
from html_fetch import HtmlFetchError  # noqa: E402


def _cfg(tmp_path: Path) -> MagicMock:
    cfg = MagicMock()
    cfg.radar_log_path = tmp_path / "radar.log"
    cfg.http_user_agent = "test-agent"
    cfg.fl_projects_url = "https://www.fl.ru/projects/?kind=1"
    return cfg


# ---------------------------------------------------------------------------
# _fl_httpx_auto_fallback_enabled
# ---------------------------------------------------------------------------

def test_httpx_auto_fallback_default_on() -> None:
    with patch.dict("os.environ", {}, clear=False):
        # Remove FL_HTTPX_AUTO_FALLBACK if present
        import os
        os.environ.pop("FL_HTTPX_AUTO_FALLBACK", None)
        assert _fl_httpx_auto_fallback_enabled() is True


def test_httpx_auto_fallback_disabled_by_env() -> None:
    with patch.dict("os.environ", {"FL_HTTPX_AUTO_FALLBACK": "0"}):
        assert _fl_httpx_auto_fallback_enabled() is False


# ---------------------------------------------------------------------------
# Auto fallback: browser raises HtmlFetchError → httpx returns HTML → parsed>0
# ---------------------------------------------------------------------------

def test_auto_fallback_when_browser_raises(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    good_html = (
        '<div class="b-page__lenta_item">'
        '<a class="b-post__title" href="/projects/12345/"><h2>Test project</h2></a>'
        '</div>'
    )
    with patch("fl_parser.listing_browser_enabled", return_value=True), \
         patch("fl_parser.fl_listing_subprocess_enabled", return_value=True), \
         patch("fl_parser.fetch_listing_html_browser_slots_wall_clock",
               side_effect=HtmlFetchError("browser_error")), \
         patch("fl_parser._fl_httpx_auto_fallback_enabled", return_value=True), \
         patch("fl_parser._fetch_listing_html_requests", return_value=good_html), \
         patch("fl_parser.proxy_log_hint", return_value="212.102.x.x:8000"):
        html = _fetch_listing_html(
            "https://www.fl.ru/projects/?kind=1",
            cfg,
            timeout_sec=30.0,
            page=1,
        )
    assert html == good_html, "httpx fallback should return HTML when browser fails"
    log_text = cfg.radar_log_path.read_text(encoding="utf-8")
    assert "outcome=fail reason=browser_error" in log_text, "browser failure logged to pipeline"
    assert "stage=fallback httpx outcome=ok" in log_text, "httpx fallback success logged"


def test_auto_fallback_when_browser_returns_none(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    fallback_html = "<html><body>ok content</body></html>"
    with patch("fl_parser.listing_browser_enabled", return_value=True), \
         patch("fl_parser.fetch_listing_html_browser_slots_wall_clock", return_value=None), \
         patch("fl_parser._fl_httpx_auto_fallback_enabled", return_value=True), \
         patch("fl_parser._fetch_listing_html_requests", return_value=fallback_html), \
         patch("fl_parser.proxy_log_hint", return_value="proxy"):
        html = _fetch_listing_html(
            "https://www.fl.ru/projects/?kind=1",
            cfg,
            timeout_sec=30.0,
            page=1,
        )
    assert html == fallback_html


def test_no_fallback_when_disabled(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    with patch("fl_parser.listing_browser_enabled", return_value=True), \
         patch("fl_parser.fetch_listing_html_browser_slots_wall_clock",
               side_effect=HtmlFetchError("error")), \
         patch("fl_parser._fl_httpx_auto_fallback_enabled", return_value=False), \
         patch("fl_parser._fl_allow_httpx_fallback", return_value=False), \
         patch("fl_parser.proxy_log_hint", return_value="proxy"):
        html = _fetch_listing_html(
            "https://www.fl.ru/projects/?kind=1",
            cfg,
            timeout_sec=30.0,
            page=1,
        )
    assert html is None, "no fallback when both auto and legacy fallback disabled"


def test_fallback_logs_failure_when_httpx_also_fails(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    with patch("fl_parser.listing_browser_enabled", return_value=True), \
         patch("fl_parser.fetch_listing_html_browser_slots_wall_clock",
               side_effect=HtmlFetchError("browser_error")), \
         patch("fl_parser._fl_httpx_auto_fallback_enabled", return_value=True), \
         patch("fl_parser._fetch_listing_html_requests",
               side_effect=Exception("httpx network error")), \
         patch("fl_parser.proxy_log_hint", return_value="proxy"):
        html = _fetch_listing_html(
            "https://www.fl.ru/projects/?kind=1",
            cfg,
            timeout_sec=30.0,
            page=1,
        )
    assert html is None
    log_text = cfg.radar_log_path.read_text(encoding="utf-8")
    assert "stage=fallback httpx outcome=fail" in log_text


# ---------------------------------------------------------------------------
# Integration: fetch_listing_projects — browser fail → httpx ok → parsed > 0
# ---------------------------------------------------------------------------

def test_fetch_listing_projects_browser_fail_httpx_ok(tmp_path: Path) -> None:
    """Full integration: browser subprocess fails, httpx fallback returns valid HTML → parsed > 0."""
    import fl_parser

    cfg = _cfg(tmp_path)
    cfg.fl_projects_url = "https://www.fl.ru/projects/?kind=1"

    good_html = (
        '<div class="b-page__lenta_item">'
        '<div class="b-post__title"><a href="/projects/99999/">Good project</a></div>'
        '</div>'
    )

    mock_storage = MagicMock()
    mock_storage.get_setting.return_value = "0"

    with patch("fl_parser.listing_browser_enabled", return_value=True), \
         patch("fl_parser.fl_listing_subprocess_enabled", return_value=True), \
         patch("fl_parser.fetch_listing_html_browser_slots_wall_clock",
               side_effect=HtmlFetchError("subprocess empty")), \
         patch("fl_parser._fl_httpx_auto_fallback_enabled", return_value=True), \
         patch("fl_parser._fetch_listing_html_requests", return_value=good_html), \
         patch("fl_parser.proxy_log_hint", return_value="212.x.x.x:8000"), \
         patch("fl_parser.exchange_fetch_begin"), \
         patch("fl_parser.exchange_fetch_end"), \
         patch("fl_parser.trim_listing_at_known", side_effect=lambda p, s, src: p), \
         patch("fl_parser.stash_listing_metrics"):
        projects = fl_parser.fetch_listing_projects(cfg, storage=mock_storage)

    assert len(projects) > 0, "Should have parsed projects via httpx fallback"
    log = cfg.radar_log_path.read_text(encoding="utf-8")
    assert "fetch:fl outcome=ok" in log
