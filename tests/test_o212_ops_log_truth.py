"""O212: ops log trim + exchange card truth."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from owner_admin import (  # noqa: E402
    _exchange_ops_rows,
    _last_log_line_for_source,
    _tg_exchange_status_from_pult,
)
from storage import ProjectStorage  # noqa: E402


def test_last_log_line_for_source_prefers_handler_ok_over_bot_start_skip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log_path = tmp_path / "radar_site.log"
    log_path.write_text(
        "\n".join(
            [
                "2026-06-14 12:00:00 тг:бот_start:acc2:skip (флаг есть)",
                "2026-06-14 12:00:01 тг:монитор:acc1:handler_ok peers=70 test_group_peer=1 test_group_file=1",
                "2026-06-14 11:59:00 listing:fl parsed=30 fresh=0",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("RADAR_LOG_PATH", str(log_path))

    line = _last_log_line_for_source("tg")
    assert "handler_ok" in line
    assert "skip" not in line


def test_last_log_line_for_source_falls_back_when_only_non_skip_tg_lines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log_path = tmp_path / "radar_site.log"
    log_path.write_text(
        "2026-06-14 12:00:00 тг:пульс:acc1 peers=70\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("RADAR_LOG_PATH", str(log_path))

    assert "тг:пульс" in _last_log_line_for_source("tg")


def test_tg_exchange_status_from_pult_ok() -> None:
    lvl, icon, status = _tg_exchange_status_from_pult("ok", "слушает")
    assert lvl == "ok"
    assert icon == "🟢"
    assert status == "слушает"


def test_exchange_row_today_new_ids_from_neon_not_health_last_new_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "projects.db"
    storage = ProjectStorage(db_path)
    storage.set_setting(
        "exchange_health:fl",
        '{"last_ok_at":"2026-06-14T10:00:00+00:00","last_new_ids":0,'
        '"last_parsed_cards":30,"last_downloaded":0,"last_error_kind":"ok"}',
    )

    class _Cfg:
        database_url = "postgresql://example"
        sqlite_path = db_path

    neon_counts = {"fl": {"new_today": 7, "new_1h": 0, "new_24h": 12, "visible_24h": 10}}

    with (
        patch("config.load_config", return_value=_Cfg()),
        patch("ops_funnel._lead_counts_by_source", return_value=neon_counts),
        patch("owner_admin._ingest_metrics_snapshot", return_value={}),
        patch("owner_admin._resolve_sqlite_path", return_value=db_path),
        patch("owner_admin._resolve_log_path", return_value=None),
        patch("health_check.is_tg_monitor_active", return_value=False),
    ):
        rows = _exchange_ops_rows()

    fl = next(r for r in rows if r.get("source_id") == "fl")
    assert fl["today_new_ids"] == 7
    assert fl["cycle_hint"] == "за цикл: parsed=30 fresh=0"


def test_exchange_row_tg_lamp_from_pult_not_neon_gap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "projects.db"
    storage = ProjectStorage(db_path)
    storage.set_setting(
        "exchange_health:tg",
        '{"last_ok_at":"2026-06-13T00:00:00+00:00","last_new_ids":0,'
        '"last_parsed_cards":-1,"last_downloaded":0,"last_error_kind":"ok"}',
    )
    storage.set_setting("status_tg_acc1_ready", "1")
    storage.set_setting("tg_monitor_last_pulse", str(int(__import__("time").time())))

    class _Cfg:
        database_url = ""
        sqlite_path = db_path

    with (
        patch("config.load_config", return_value=_Cfg()),
        patch("ops_funnel._lead_counts_by_source", return_value={}),
        patch("owner_admin._ingest_metrics_snapshot", return_value={"tg": {"last_insert_gap_sec": 7200}}),
        patch("owner_admin._resolve_sqlite_path", return_value=db_path),
        patch("owner_admin._resolve_log_path", return_value=None),
        patch("health_check.is_tg_monitor_active", return_value=True),
        patch(
            "radar_status.tg_pult_lamp_state",
            return_value=("ok", "слушает"),
        ),
    ):
        rows = _exchange_ops_rows()

    tg = next(r for r in rows if r.get("source_id") == "tg")
    assert tg["exchange_level"] == "ok"
    assert tg["exchange_icon"] == "🟢"
    assert tg["exchange_status_ru"] == "слушает"
