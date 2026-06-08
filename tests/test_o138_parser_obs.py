"""O138: parsed vs fresh — status_level, health log, /ops/ row."""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from exchange_health import (
    build_ops_exchange_row,
    format_health_log_line,
    load_health,
    record_fetch,
    status_level,
)
from storage import ProjectStorage


def _ok_fetch_health(
    *,
    parsed: int,
    fresh: int,
    new: int = 0,
    ts: str = "2026-06-08 12:00:00 UTC",
) -> dict:
    return {
        "last_fetch_at": ts,
        "last_ok_at": ts,
        "last_error_kind": "ok",
        "last_error_short": "",
        "last_parsed_cards": parsed,
        "last_downloaded": fresh,
        "last_new_ids": new,
    }


def test_status_level_parsed_zero_red() -> None:
    health = _ok_fetch_health(parsed=0, fresh=0)
    assert status_level(health, source_id="fl") == "red"


def test_status_level_parsed_thirty_fresh_zero_green() -> None:
    health = _ok_fetch_health(parsed=30, fresh=0)
    assert status_level(health, source_id="fl") == "green"


def test_status_level_parsed_fresh_yellow_on_neon_gap() -> None:
    health = _ok_fetch_health(parsed=30, fresh=0)
    assert status_level(health, source_id="fl", neon_gap_min=121) == "yellow"


def test_format_health_log_line_parsed_fresh() -> None:
    health = _ok_fetch_health(parsed=30, fresh=0, new=0)
    line = format_health_log_line("fl", health, fetch_ok=True)
    assert line == "health:fl status=ok parsed=30 fresh=0 new=0"


def test_record_fetch_persists_parsed_cards(tmp_path: Path) -> None:
    storage = ProjectStorage(tmp_path / "t.db")
    record_fetch(
        storage,
        "fl",
        ok=True,
        downloaded=0,
        new_ids=0,
        parsed_cards=30,
        ts="2026-06-08 12:00:00 UTC",
    )
    row = load_health(storage, "fl")
    assert row["last_parsed_cards"] == 30
    assert row["last_downloaded"] == 0


def test_build_ops_exchange_row_listing_line() -> None:
    health = _ok_fetch_health(parsed=30, fresh=0)
    row = build_ops_exchange_row(
        "fl",
        health,
        {"last_insert_gap_sec": 11 * 3600},
    )
    assert row["last_parsed_cards"] == 30
    assert row["last_fresh_cards"] == 0
    assert row["what_happened"] == "parsed=30 fresh=0 — догнали"
    assert "30 parsed" in row["listing_line"]
    assert row["level"] == "yellow"


def test_build_ops_exchange_row_parsed_zero_hint() -> None:
    health = _ok_fetch_health(parsed=0, fresh=0)
    row = build_ops_exchange_row("fl", health, None)
    assert row["what_happened"] == "parsed=0 — проверить parse"
    assert row["level"] == "red"
