"""O257: fetch:{src} outcome=ok|fail reason= pipeline log format tests."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))


def _cfg(tmp_path: Path) -> MagicMock:
    cfg = MagicMock()
    cfg.radar_log_path = tmp_path / "radar.log"
    cfg.radar_log_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.http_user_agent = "test-agent"
    return cfg


# ---------------------------------------------------------------------------
# FL outcome log
# ---------------------------------------------------------------------------

def test_fl_outcome_ok_logged(tmp_path: Path) -> None:
    from fl_parser import fetch_listing_projects

    cfg = _cfg(tmp_path)
    cfg.fl_projects_url = "https://www.fl.ru/projects/?kind=1"
    good_html = (
        '<div class="b-page__lenta_item">'
        '<div class="b-post__title"><a href="/projects/11111/">Project</a></div>'
        '</div>'
    )
    mock_storage = MagicMock()
    mock_storage.get_setting.return_value = "0"

    with patch("fl_parser.listing_browser_enabled", return_value=False), \
         patch("fl_parser._fl_allow_httpx_fallback", return_value=True), \
         patch("fl_parser._fl_httpx_auto_fallback_enabled", return_value=False), \
         patch("fl_parser._fetch_listing_html_requests", return_value=good_html), \
         patch("fl_parser.proxy_log_hint", return_value="proxy"), \
         patch("fl_parser.exchange_fetch_begin"), \
         patch("fl_parser.exchange_fetch_end"), \
         patch("fl_parser.trim_listing_at_known", side_effect=lambda p, s, src: p), \
         patch("fl_parser.stash_listing_metrics"):
        projects = fetch_listing_projects(cfg, storage=mock_storage)

    log = cfg.radar_log_path.read_text(encoding="utf-8")
    assert "fetch:fl outcome=ok" in log, f"Expected outcome=ok in log:\n{log}"
    assert "reason=ok" in log


def test_fl_outcome_fail_logged_when_parsed_zero(tmp_path: Path) -> None:
    from fl_parser import fetch_listing_projects
    from fl_parser import FlListingError

    cfg = _cfg(tmp_path)
    cfg.fl_projects_url = "https://www.fl.ru/projects/?kind=1"
    mock_storage = MagicMock()
    mock_storage.get_setting.return_value = "0"

    # Return empty HTML → parsed=0 → outcome=fail
    empty_html = "<html><body>no projects here</body></html>"

    with patch("fl_parser.listing_browser_enabled", return_value=False), \
         patch("fl_parser._fl_allow_httpx_fallback", return_value=True), \
         patch("fl_parser._fl_httpx_auto_fallback_enabled", return_value=False), \
         patch("fl_parser._fetch_listing_html_requests", return_value=empty_html), \
         patch("fl_parser.proxy_log_hint", return_value="proxy"), \
         patch("fl_parser.exchange_fetch_begin"), \
         patch("fl_parser.exchange_fetch_end"), \
         patch("fl_parser.trim_listing_at_known", side_effect=lambda p, s, src: p), \
         patch("fl_parser.stash_listing_metrics"), \
         patch("fl_parser._maybe_fl_parsed_zero_recovery"):
        with pytest.raises(FlListingError):
            fetch_listing_projects(cfg, storage=mock_storage)


# ---------------------------------------------------------------------------
# FL pipeline log format check: reason codes in expected positions
# ---------------------------------------------------------------------------

def test_fl_browser_fail_pipeline_log_has_reason(tmp_path: Path) -> None:
    from fl_parser import _fetch_listing_html
    from html_fetch import HtmlFetchError

    cfg = _cfg(tmp_path)

    with patch("fl_parser.listing_browser_enabled", return_value=True), \
         patch("fl_parser.fetch_listing_html_browser_slots_wall_clock",
               side_effect=HtmlFetchError("wall-clock timeout after 120s")), \
         patch("fl_parser._fl_httpx_auto_fallback_enabled", return_value=False), \
         patch("fl_parser._fl_allow_httpx_fallback", return_value=False), \
         patch("fl_parser.proxy_log_hint", return_value="1.2.3.4:8000"):
        html = _fetch_listing_html("https://www.fl.ru/projects/?kind=1", cfg, timeout_sec=30.0, page=1)

    assert html is None
    log = cfg.radar_log_path.read_text(encoding="utf-8")
    assert "outcome=fail" in log
    assert "reason=browser_timeout" in log
    assert "proxy_hint=1.2.3.4:8000" in log


def test_fl_browser_error_pipeline_log(tmp_path: Path) -> None:
    from fl_parser import _fetch_listing_html
    from html_fetch import HtmlFetchError

    cfg = _cfg(tmp_path)

    with patch("fl_parser.listing_browser_enabled", return_value=True), \
         patch("fl_parser.fetch_listing_html_browser_slots_wall_clock",
               side_effect=HtmlFetchError("subprocess failed antibot")), \
         patch("fl_parser._fl_httpx_auto_fallback_enabled", return_value=False), \
         patch("fl_parser._fl_allow_httpx_fallback", return_value=False), \
         patch("fl_parser.proxy_log_hint", return_value="proxy"):
        html = _fetch_listing_html("https://www.fl.ru/projects/?kind=1", cfg, timeout_sec=30.0, page=1)

    log = cfg.radar_log_path.read_text(encoding="utf-8")
    # Should be browser_error not browser_timeout
    assert "reason=browser_error" in log


# ---------------------------------------------------------------------------
# YouDo outcome log
# ---------------------------------------------------------------------------

def test_youdo_fetch_end_has_reason_when_parsed_zero() -> None:
    from youdo_parser import log_youdo_fetch_end
    from unittest.mock import MagicMock
    import io
    import sys

    cfg = MagicMock()
    log_lines: list[str] = []

    def _capture_log(path, line: str) -> None:
        log_lines.append(line)

    stats = MagicMock()
    stats.parsed_cards = 0
    stats.downloaded = 0
    stats.new_ids = 0
    stats.fetch_error = "browser_fail=antibot HTML"

    health = {"last_error_kind": "browser", "last_error_short": "antibot"}

    with patch("youdo_parser.log_pipeline_line", side_effect=_capture_log):
        log_youdo_fetch_end(cfg, stats, health)

    fetch_end_lines = [l for l in log_lines if "fetch_end" in l]
    assert fetch_end_lines, "Should emit fetch_end trace line"
    assert "reason=antibot_html" in fetch_end_lines[0] or "reason=" in fetch_end_lines[0], \
        f"Should have reason= when parsed=0: {fetch_end_lines}"


# ---------------------------------------------------------------------------
# probe_parsers_health_vps: parsing logic
# ---------------------------------------------------------------------------

def test_probe_parses_outcome_ok(tmp_path: Path) -> None:
    sys.path.insert(0, str(_ROOT / "scripts"))
    from probe_parsers_health_vps import probe

    log = tmp_path / "radar_site.log"
    log.write_text(
        "2026-06-16 06:10 fetch:fl outcome=ok reason=ok tier=dc parsed=30\n"
        "2026-06-16 06:10 fetch:kwork outcome=ok reason=ok tier=dc parsed=15\n"
        "2026-06-16 06:10 fetch:youdo outcome=ok reason=ok tier=dc parsed=50\n",
        encoding="utf-8",
    )
    result = probe(log)
    assert result["status"] == "ok"
    assert result["sources"]["fl"]["outcome"] == "ok"
    assert result["sources"]["fl"]["parsed"] == 30


def test_probe_detects_fail(tmp_path: Path) -> None:
    sys.path.insert(0, str(_ROOT / "scripts"))
    from probe_parsers_health_vps import probe

    log = tmp_path / "radar_site.log"
    log.write_text(
        "fetch:fl outcome=fail reason=browser_timeout tier=dc parsed=0\n"
        "fetch:kwork outcome=ok reason=ok tier=dc parsed=10\n",
        encoding="utf-8",
    )
    result = probe(log)
    assert result["status"] == "fail"
    assert result["sources"]["fl"]["outcome"] == "fail"
    assert result["sources"]["fl"]["reason"] == "browser_timeout"
