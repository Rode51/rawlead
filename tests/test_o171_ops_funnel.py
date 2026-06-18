"""O171: truth ladder step classification."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from ops_funnel import (  # noqa: E402
    SourceInput,
    build_diagnosis,
    build_funnel_payload,
    build_source_funnel,
    classify_fetch_step,
    classify_new_step,
    classify_parsed_step,
)
from owner_admin import fetch_ops_funnel  # noqa: E402
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


def test_fetch_fail_x3_is_bad() -> None:
    assert classify_fetch_step(fetch_failed=True, retry_count=3) == "bad"
    assert classify_fetch_step(fetch_failed=True, retry_count=4) == "bad"


def test_fl_soft_dc_exhausted_fetch_is_warn_not_bad() -> None:
    assert (
        classify_fetch_step(
            fetch_failed=False,
            retry_count=0,
            soft_proxy_exhausted=True,
        )
        == "warn"
    )
    with patch("exchange_proxy.fl_dc_tier_exhausted", return_value=True):
        src = build_source_funnel(
            SourceInput(
                source_id="fl",
                health={
                    **_empty_health(),
                    "last_parsed_cards": 30,
                    "last_fetch_at": "t",
                    "last_ok_at": "t",
                },
                cycle=None,
                fetch_failed=False,
                fetch_retries=3,
                cycle_age_min=5,
            )
        )
    fetch_step = next(s for s in src["steps"] if s["id"] == "fetch")
    assert fetch_step["status"] == "warn"


def test_parsed_zero_fetch_ok_is_bad_or_warn() -> None:
    assert classify_parsed_step(parsed=0, fetch_ok=True, threshold=5) == "bad"
    assert classify_parsed_step(parsed=0, fetch_ok=True, empty_exchange=True) == "warn"


def test_empty_exchange_new_step_na() -> None:
    assert classify_new_step(new_1h=0, parsed=0, empty_exchange=True) == "na"
    assert classify_new_step(new_1h=0, new_today=5, parsed=0, empty_exchange=False) == "ok"
    src = build_source_funnel(
        SourceInput(
            source_id="youdo",
            health={**_empty_health(), "last_parsed_cards": 0, "last_fetch_at": "x", "last_ok_at": "x"},
            cycle=None,
            fetch_failed=False,
            fetch_retries=0,
            empty_exchange=True,
        )
    )
    new_step = next(s for s in src["steps"] if s["id"] == "new")
    assert new_step["status"] == "na"
    assert src.get("muted_note")


def test_process_break_diagnosis_restarts_radar() -> None:
    from ops_funnel import _action_for_break

    action = _action_for_break("fl", "process")
    assert action is not None
    assert action.get("target") == "radar"
    assert action.get("action") == "restart"
    assert action.get("label") == "Перезапустить радар"


def test_diagnosis_picks_first_bad_step() -> None:
    fl = build_source_funnel(
        SourceInput(
            source_id="fl",
            health=_empty_health(),
            cycle=None,
            fetch_failed=True,
            fetch_retries=3,
            cycle_age_min=5,
        )
    )
    kwork = build_source_funnel(
        SourceInput(
            source_id="kwork",
            health={**_empty_health(), "last_parsed_cards": 8},
            cycle=None,
            fetch_failed=False,
            fetch_retries=0,
            cycle_age_min=5,
        )
    )
    diag = build_diagnosis([fl, kwork])
    assert diag is not None
    assert diag["level"] == "bad"
    assert "fetch" in diag["text"].lower() or "загруз" in diag["text"].lower()
    assert diag["action"] is not None


def test_empty_exchange_no_red_diagnosis_spam() -> None:
    youdo = build_source_funnel(
        SourceInput(
            source_id="youdo",
            health={**_empty_health(), "last_parsed_cards": 0, "last_fetch_at": "t", "last_ok_at": "t"},
            cycle=None,
            fetch_failed=False,
            fetch_retries=0,
            empty_exchange=True,
            cycle_age_min=8,
        )
    )
    parsed = next(s for s in youdo["steps"] if s["id"] == "parsed")
    assert parsed["status"] in ("warn", "bad")
    diag = build_diagnosis([youdo])
    assert diag is None or "youdo" not in (diag.get("text") or "").lower() or parsed["status"] != "bad"


def test_build_funnel_payload_uses_load_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "projects.db"
    storage = ProjectStorage(db_path)
    called: list[str] = []

    class _Cfg:
        sqlite_path = db_path

    def _fake_load_config() -> _Cfg:
        called.append("load_config")
        return _Cfg()

    monkeypatch.setenv("FL_PROJECTS_URL", "https://example.com/fl")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "1:test")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    monkeypatch.setenv("TG_PROXY_URL", "http://127.0.0.1:8080")
    monkeypatch.setenv("POLL_INTERVAL_MINUTES", "15")

    with patch("config.load_config", side_effect=_fake_load_config):
        payload = build_funnel_payload(storage, database_url="")

    assert called == ["load_config"]
    assert "sources" in payload
    assert len(payload["sources"]) == 4


def test_fetch_ops_funnel_degraded_on_build_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "projects.db"
    ProjectStorage(db_path)
    monkeypatch.setenv("SQLITE_PATH", str(db_path))

    with patch("ops_funnel.build_funnel_payload", side_effect=RuntimeError("boom")):
        out = fetch_ops_funnel("postgresql://example")

    assert out["sources"] == []
    assert out.get("diagnosis", {}).get("text")


def test_tg_lamp_listening_strikes_not_red(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from ops_funnel import _tg_acc_row

    db_path = tmp_path / "projects.db"
    storage = ProjectStorage(db_path)
    storage.set_setting("status_tg_acc2_ready", "1")
    storage.set_setting("status_tg_acc2_chats_listen", "7")
    storage.set_setting("status_tg_acc2_chats_file", "25")
    storage.set_setting("status_tg_acc2_chats_filter", "25")

    join_state = {
        "acc2": {
            "recent": [
                {"status": "fail"},
                {"status": "fail"},
                {"status": "fail"},
            ]
        }
    }

    with patch("ops_funnel._tg_listen_file_counts", return_value=(25, 25)):
        row = _tg_acc_row(storage, "acc2", join_state, pending=0)

    assert row["state"] == "listening"
    assert row["lamp"] in ("ok", "warn")
    assert row["lamp"] != "bad"
    assert row.get("lamp_reason_ru")


def test_tg_auth_err_only_get_me_prefix(tmp_path: Path) -> None:
    from ops_funnel import _tg_acc_row, _tg_last_err_is_auth

    assert _tg_last_err_is_auth("get_me: session expired")
    assert not _tg_last_err_is_auth("skip: duplicate message")

    db_path = tmp_path / "projects.db"
    storage = ProjectStorage(db_path)
    storage.set_setting("status_tg_acc3_last_err", "skip: filtered out")
    storage.set_setting("status_tg_acc3_ready", "1")
    storage.set_setting("status_tg_acc3_chats_filter", "24")

    with patch("ops_funnel._tg_listen_file_counts", return_value=(24, 24)):
        row = _tg_acc_row(storage, "acc3", {}, pending=0)

    assert row["state"] == "listening"
    assert row["lamp"] != "bad"


def test_tg_msgs_total_survives_session_reset(tmp_path: Path) -> None:
    from radar_status import (
        _int_setting,
        _tg_key,
        record_tg_message,
        reset_tg_session_stats,
    )

    db_path = tmp_path / "projects.db"
    storage = ProjectStorage(db_path)
    record_tg_message(storage, "acc1", was_new=True, notified=False)
    record_tg_message(storage, "acc1", was_new=False, notified=True)

    assert _int_setting(storage, _tg_key("acc1", "msgs")) == 2
    assert _int_setting(storage, _tg_key("acc1", "msgs_total")) == 2

    reset_tg_session_stats(storage, ("acc1",))

    assert _int_setting(storage, _tg_key("acc1", "msgs")) == 0
    assert _int_setting(storage, _tg_key("acc1", "msgs_total")) == 2


def test_tg_msgs_line_shows_total_after_reset(tmp_path: Path) -> None:
    from ops_funnel import _tg_acc_row, tg_msgs_line_ru
    from radar_status import record_tg_message, reset_tg_session_stats

    db_path = tmp_path / "projects.db"
    storage = ProjectStorage(db_path)
    storage.set_setting("status_tg_acc2_ready", "1")
    storage.set_setting("status_tg_acc2_chats_filter", "24")
    record_tg_message(storage, "acc2", was_new=True, notified=False)
    reset_tg_session_stats(storage, ("acc2",))

    with patch("ops_funnel._tg_listen_file_counts", return_value=(24, 24)):
        row = _tg_acc_row(storage, "acc2", {}, pending=0)

    assert row["msgs_count"] == 0
    assert row["msgs_total"] == 1
    assert row["msgs_line"] == "+0 за сессию · всего 1"
    assert tg_msgs_line_ru(session=0, total=1) == "+0 за сессию · всего 1"


def test_o211_meta_shows_today_and_24h() -> None:
    src = build_source_funnel(
        SourceInput(
            source_id="fl",
            health={**_empty_health(), "last_parsed_cards": 30, "last_fetch_at": "t", "last_ok_at": "t"},
            cycle=None,
            fetch_failed=False,
            fetch_retries=0,
            new_1h=0,
            new_today=12,
            new_24h=45,
            visible_24h=40,
            cycle_age_min=5,
        )
    )
    meta = src["meta"]
    assert meta["new_today"] == 12
    assert meta["new_24h"] == 45
    assert meta["parsed"] == 30
    assert meta.get("parsed_title")

    parsed_step = next(s for s in src["steps"] if s["id"] == "parsed")
    new_step = next(s for s in src["steps"] if s["id"] == "new")
    assert "HTML→карточки" in parsed_step["tooltip"]
    assert "Neon" in new_step["tooltip"]
    assert "12" in new_step["tooltip"]
    assert "45" in new_step["tooltip"]


def test_o211_youdo_visible_softens_red_lamp() -> None:
    src = build_source_funnel(
        SourceInput(
            source_id="youdo",
            health={**_empty_health(), "last_parsed_cards": 0, "last_fetch_at": "t", "last_ok_at": "t"},
            cycle=None,
            fetch_failed=False,
            fetch_retries=0,
            new_1h=0,
            new_today=0,
            new_24h=0,
            visible_24h=15,
            l1_backlog=300,
            cycle_age_min=5,
            empty_exchange=False,
        )
    )
    assert src["lamp"] == "warn"
    assert src["lamp"] != "bad"
    bad_steps = [s for s in src["steps"] if s["status"] == "bad"]
    assert not bad_steps
