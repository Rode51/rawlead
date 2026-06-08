"""O104: exchange health registry, status format, alert cooldown."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from exchange_health import (
    ALERT_COOLDOWN_SEC,
    classify_error,
    format_alert_text,
    format_exchange_status_line,
    format_health_log_line,
    kind_label,
    load_health,
    maybe_send_red_alert,
    record_fetch,
    silence_minutes,
    status_level,
)
from storage import ProjectStorage


def test_classify_error_kinds() -> None:
    assert classify_error("HTTP 403 Forbidden") == "403"
    assert classify_error("antibot challenge") == "antibot"
    assert classify_error("playwright timeout browser_fail") == "browser"
    assert classify_error("proxy pool exhausted ban") == "proxy"
    assert classify_error("read timed out") == "timeout"
    assert classify_error("parse selector empty") == "parse"
    assert classify_error("something weird") == "unknown"


def test_kind_label_ru() -> None:
    assert kind_label("antibot") == "Антибот / блок IP"
    assert kind_label("ok") == "Работает"


def test_record_fetch_and_load(tmp_path: Path) -> None:
    db = tmp_path / "t.db"
    storage = ProjectStorage(db)
    rec = record_fetch(
        storage,
        "youdo",
        ok=False,
        error_msg="antibot block",
        downloaded=0,
        new_ids=0,
        ts="2026-06-03 12:00:00 UTC",
    )
    assert rec["last_error_kind"] == "antibot"
    loaded = load_health(storage, "youdo")
    assert loaded["last_error_short"]
    assert json.loads(storage.get_setting("exchange_health:youdo"))["last_fetch_at"]

    record_fetch(
        storage,
        "youdo",
        ok=True,
        downloaded=50,
        new_ids=3,
        ts="2026-06-03 12:05:00 UTC",
    )
    ok_row = load_health(storage, "youdo")
    assert ok_row["last_error_kind"] == "ok"
    assert ok_row["last_downloaded"] == 50


def test_status_level_silence() -> None:
    now = time.time()
    recent = {
        "last_ok_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now - 5 * 60)),
        "last_fetch_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now - 5 * 60)),
        "last_error_kind": "ok",
    }
    assert status_level(recent, now=now) == "green"
    old = {
        "last_ok_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now - 120 * 60)),
        "last_fetch_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now - 120 * 60)),
        "last_error_kind": "ok",
    }
    assert status_level(old, now=now) == "red"
    mid = {
        "last_ok_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now - 30 * 60)),
        "last_fetch_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now - 30 * 60)),
        "last_error_kind": "ok",
    }
    assert status_level(mid, now=now) == "yellow"


def test_status_level_fetch_error() -> None:
    health = {
        "last_ok_at": "2026-06-03 12:00:00 UTC",
        "last_fetch_at": "2026-06-03 12:10:00 UTC",
        "last_error_at": "2026-06-03 12:10:00 UTC",
        "last_error_kind": "antibot",
    }
    assert status_level(health, fetch_failed=True) == "red"


def test_status_level_ok_after_error_not_red() -> None:
    """O152: FL ok-fetch after timeout — не 🔴 из-за stale cycle summary."""
    now = time.time()
    health = {
        "last_ok_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now - 3 * 60)),
        "last_fetch_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now - 3 * 60)),
        "last_error_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now - 60 * 60)),
        "last_error_kind": "timeout",
        "last_error_short": "Page.goto timeout 30s",
        "last_parsed_cards": 21,
        "last_downloaded": 21,
    }
    assert status_level(health, fetch_failed=True, now=now, source_id="fl") == "green"


def test_format_health_log_line() -> None:
    ok_health = {"last_downloaded": 50, "last_new_ids": 3, "last_error_kind": "ok"}
    assert "status=ok" in format_health_log_line("youdo", ok_health, fetch_ok=True, ingest_lag_p50_min=2)
    fail_health = {"last_error_kind": "antibot"}
    assert format_health_log_line("youdo", fail_health, fetch_ok=False) == "health:youdo status=fail kind=antibot"


def test_format_alert_text() -> None:
    health = {
        "last_ok_at": "2026-06-03 17:04:00 UTC",
        "last_error_kind": "antibot",
        "last_error_short": "Антибот / блок IP",
    }
    text = format_alert_text("youdo", health, now=time.time())
    assert "YouDo" in text
    assert "🔴" in text
    assert "17:04" in text


def test_alert_cooldown_mock_tg(tmp_path: Path, monkeypatch) -> None:
    db = tmp_path / "t.db"
    storage = ProjectStorage(db)
    record_fetch(
        storage,
        "fl",
        ok=False,
        error_msg="403 forbidden",
        ts="2020-01-01 00:00:00 UTC",
    )
    health = load_health(storage, "fl")
    calls: list[str] = []

    def _fake_send(text: str) -> tuple[bool, str]:
        calls.append(text)
        return True, "@flparsingbot"

    monkeypatch.setattr("health_check.send_flparsing_admin_text", _fake_send)
    assert maybe_send_red_alert(storage, "fl", health, fetch_failed=True) is True
    assert len(calls) == 1
    assert maybe_send_red_alert(storage, "fl", health, fetch_failed=True) is False
    storage.set_setting(
        "exchange_health_alert_at:fl",
        str(int(time.time()) - ALERT_COOLDOWN_SEC - 5),
    )
    assert maybe_send_red_alert(storage, "fl", health, fetch_failed=True) is True
    assert len(calls) == 2


def test_format_exchange_status_line() -> None:
    health = {
        "last_ok_at": "2026-06-03 12:00:00 UTC",
        "last_error_kind": "ok",
        "last_downloaded": 10,
        "last_new_ids": 0,
    }
    line = format_exchange_status_line("fl", health, now=time.time())
    assert "FL.ru" in line
    assert "🟢" in line or "🟡" in line or "🔴" in line
