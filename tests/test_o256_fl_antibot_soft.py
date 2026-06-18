"""O256: FL parsed=0 soft antibot — html_snip, hard reset, ops lamp."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from fl_parser import (  # noqa: E402
    _maybe_fl_parsed_zero_recovery,
    _maybe_fl_soft_antibot_reset,
)
from ops_funnel import build_funnel_payload  # noqa: E402
from radar_cycle_log import CycleSummary  # noqa: E402
from radar_status import apply_fl_antibot_soft_ops_row, fl_antibot_soft_active  # noqa: E402
from storage import ProjectStorage  # noqa: E402


def _cfg(tmp_path: Path) -> MagicMock:
    cfg = MagicMock()
    cfg.radar_log_path = tmp_path / "radar.log"
    return cfg


def test_soft_antibot_reset_at_streak_five_no_bans(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    storage = MagicMock()
    with patch("fl_parser._fl_count_source_bans", return_value=0):
        with patch("exchange_browser_fetch.fl_hard_reset") as mock_reset:
            ok = _maybe_fl_soft_antibot_reset(cfg, storage, 5)
    assert ok is True
    mock_reset.assert_called_once()
    assert "soft_antibot" in mock_reset.call_args.kwargs.get("reason", "")


def test_parsed_zero_recovery_logs_html_snip_and_soft_reset(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path)
    storage = MagicMock()
    storage.get_setting.return_value = "4"
    import fl_parser

    fl_parser._fl_last_listing_html = "<html>captcha проверьте что вы не робот</html>"
    with patch("fl_parser.listing_browser_enabled", return_value=True):
        with patch("fl_parser._fl_fetch_pool_ok", return_value=True):
            with patch("fl_parser._fl_count_source_bans", return_value=0):
                with patch("fl_parser._fl_streak_get", return_value=4):
                    with patch("exchange_browser_fetch.fl_hard_reset") as mock_reset:
                        _maybe_fl_parsed_zero_recovery(cfg, storage, 0)
    log_text = cfg.radar_log_path.read_text(encoding="utf-8")
    assert "fl_listing:html_snip snip=" in log_text
    assert "fl_listing:soft_antibot_reset streak=5" in log_text
    mock_reset.assert_called_once()


def test_fl_antibot_soft_active_when_streak_above_ten(tmp_path: Path) -> None:
    db_path = tmp_path / "radar.db"
    storage = ProjectStorage(str(db_path))
    storage.set_setting("fl_parsed_zero_streak", "11")
    log = tmp_path / "radar.log"
    log.write_text(
        "fetch:fl proxy=212.102.151.153:8000 slot=4/4 alive=4/4\n"
        "listing:fl parsed=0 fresh=0\n",
        encoding="utf-8",
    )
    with patch("radar_status._fl_proxy_ban_count", return_value=0):
        assert fl_antibot_soft_active(
            storage,
            log_path=log,
            parsed_cards=0,
        )


def test_ops_fl_antibot_soft_lamp_bad(tmp_path: Path) -> None:
    log = tmp_path / "radar.log"
    log.write_text(
        "fetch:fl proxy=212.102.151.153:8000 slot=4/4 alive=4/4\n"
        "listing:fl parsed=0 fresh=0\n",
        encoding="utf-8",
    )
    db_path = tmp_path / "radar.db"
    storage = ProjectStorage(str(db_path))
    storage.set_setting("fl_parsed_zero_streak", "11")

    row = {
        "lamp": "ok",
        "meta": {"parsed": 0},
        "steps": [
            {"id": "fetch", "status": "ok", "is_break": False},
            {"id": "parsed", "status": "ok", "is_break": False},
        ],
    }
    with patch("radar_status._fl_proxy_ban_count", return_value=0):
        apply_fl_antibot_soft_ops_row(row, storage, log)
    assert row["lamp"] == "bad"
    assert row["meta"].get("fl_antibot_soft") is True
    parsed_step = next(s for s in row["steps"] if s["id"] == "parsed")
    assert parsed_step["status"] == "bad"


def test_build_funnel_fl_antibot_soft_meta(tmp_path: Path) -> None:
    log = tmp_path / "radar.log"
    log.write_text(
        "fetch:fl proxy=212.102.151.153:8000 slot=4/4 alive=4/4\n"
        "listing:fl parsed=0 fresh=0\n",
        encoding="utf-8",
    )
    db_path = tmp_path / "radar.db"
    storage = ProjectStorage(str(db_path))
    storage.set_setting("fl_parsed_zero_streak", "11")

    empty_health = {
        "last_fetch_at": "t",
        "last_ok_at": "t",
        "last_error_at": "",
        "last_error_kind": "ok",
        "last_parsed_cards": 0,
        "last_downloaded": 0,
        "last_new_ids": 0,
    }
    with patch("ops_funnel.load_cycle_summary", return_value=None), patch(
        "ops_funnel.load_all_health",
        return_value={
            "fl": empty_health,
            "kwork": empty_health,
            "youdo": empty_health,
            "tg": empty_health,
        },
    ), patch("ops_funnel._lead_counts_by_source", return_value={}), patch(
        "ops_funnel._ingest_metrics_snapshot", return_value={}
    ), patch("ops_funnel._l1_backlog_total", return_value=0), patch(
        "ops_funnel._l1_backlog_by_source", return_value={"fl": 0, "kwork": 0, "tg": 0}
    ), patch("ops_funnel._resolve_log_path", return_value=log), patch(
        "radar_status._fl_proxy_ban_count", return_value=0
    ):
        payload = build_funnel_payload(storage, database_url="", now=time.time())
    fl = next(s for s in payload["sources"] if s["source_id"] == "fl")
    assert fl["lamp"] == "bad"
    assert fl["meta"].get("fl_antibot_soft") is True
