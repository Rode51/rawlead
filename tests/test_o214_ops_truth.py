"""O214: ops panel cycle_age log fallback + FL residential tier display."""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from ops_funnel import (  # noqa: E402
    SourceInput,
    _cycle_age_min,
    _cycle_ts_from_log,
    build_funnel_payload,
    build_source_funnel,
)
from radar_cycle_log import CycleSummary  # noqa: E402
from storage import ProjectStorage  # noqa: E402


def _empty_health() -> dict:
    return {
        "last_fetch_at": "",
        "last_ok_at": "",
        "last_error_at": "",
        "last_error_kind": "ok",
        "last_parsed_cards": -1,
        "last_downloaded": 0,
        "last_new_ids": 0,
    }


def test_cycle_age_from_log_when_summary_none(tmp_path: Path) -> None:
    log = tmp_path / "radar.log"
    ts = "2026-06-14 14:23:21"
    log.write_text(f"noise\n── Цикл {ts} ──\n", encoding="utf-8")
    epoch = _cycle_ts_from_log(log)
    assert epoch is not None
    ref = epoch + 7 * 60
    age = _cycle_age_min(None, now=ref, log_path=log)
    assert age == 7


def test_cycle_age_prefers_log_when_sqlite_stale(tmp_path: Path) -> None:
    log = tmp_path / "radar.log"
    fresh_ts = "2026-06-14 14:23:21"
    log.write_text(f"── Цикл {fresh_ts} ──\n", encoding="utf-8")
    stale_epoch = time.time() - 154 * 60
    stale_dt = datetime.fromtimestamp(stale_epoch).strftime("%Y-%m-%d %H:%M:%S")
    summary = CycleSummary(ts=stale_dt)
    ref = _cycle_ts_from_log(log)
    assert ref is not None
    age = _cycle_age_min(summary, now=ref + 5 * 60, log_path=log)
    assert age == 5


def test_fl_parsed_zero_pool_exhausted_lamp_bad(tmp_path: Path) -> None:
    log = tmp_path / "radar.log"
    log.write_text(
        "fetch:fl proxy=pool_exhausted slot=1/25 alive=0/25\n"
        "listing:fl parsed=0 fresh=0\n",
        encoding="utf-8",
    )
    db_path = tmp_path / "radar.db"
    storage = ProjectStorage(str(db_path))
    with patch("ops_funnel.load_cycle_summary", return_value=None), patch(
        "ops_funnel.load_all_health",
        return_value={
            "fl": {
                **_empty_health(),
                "last_parsed_cards": 0,
                "last_fetch_at": "t",
                "last_ok_at": "t",
            },
            "kwork": _empty_health(),
            "youdo": _empty_health(),
            "tg": _empty_health(),
        },
    ), patch("ops_funnel._lead_counts_by_source", return_value={}), patch(
        "ops_funnel._ingest_metrics_snapshot", return_value={}
    ), patch("ops_funnel._l1_backlog_total", return_value=0), patch(
        "ops_funnel._l1_backlog_by_source", return_value={"fl": 0, "kwork": 0, "tg": 0}
    ), patch("ops_funnel._resolve_log_path", return_value=log):
        payload = build_funnel_payload(storage, database_url="", now=time.time())
    fl = next(s for s in payload["sources"] if s["source_id"] == "fl")
    assert fl["lamp"] == "bad"
    assert fl["meta"].get("fl_pool_exhausted") is True
    parsed_step = next(s for s in fl["steps"] if s["id"] == "parsed")
    assert parsed_step["status"] == "bad"


def test_build_funnel_fl_residential_meta_and_warn_lamp(tmp_path: Path) -> None:
    db_path = tmp_path / "radar.db"
    storage = ProjectStorage(str(db_path))
    with patch("ops_funnel.load_cycle_summary", return_value=None), patch(
        "ops_funnel.load_all_health",
        return_value={
            "fl": {
                **_empty_health(),
                "last_parsed_cards": 30,
                "last_fetch_at": "t",
                "last_ok_at": "t",
            },
            "kwork": _empty_health(),
            "youdo": _empty_health(),
            "tg": _empty_health(),
        },
    ), patch("ops_funnel._lead_counts_by_source", return_value={}), patch(
        "ops_funnel._ingest_metrics_snapshot", return_value={}
    ), patch("ops_funnel._l1_backlog_total", return_value=0), patch(
        "ops_funnel._l1_backlog_by_source", return_value={"fl": 0, "kwork": 0, "tg": 0}
    ), patch("exchange_proxy.fl_on_residential_tier", return_value=True), patch(
        "exchange_proxy.fl_residential_counts", return_value=(23, 25)
    ):
        payload = build_funnel_payload(storage, database_url="", now=time.time())
    fl = next(s for s in payload["sources"] if s["source_id"] == "fl")
    assert fl["meta"].get("fl_tier") == "residential"
    assert fl["meta"].get("fl_res_alive") == "23/25"
    assert fl["lamp"] == "warn"
    assert fl["lamp"] != "bad"


def test_soften_fl_residential_lamp_helper() -> None:
    from ops_funnel import _soften_fl_residential_lamp

    row = {
        "lamp": "bad",
        "meta": {"parsed": 30},
        "steps": [{"id": "fetch", "status": "bad", "is_break": True}],
    }
    _soften_fl_residential_lamp(row)
    assert row["lamp"] == "warn"
    assert row["steps"][0]["status"] == "warn"
    assert row["steps"][0]["is_break"] is False
