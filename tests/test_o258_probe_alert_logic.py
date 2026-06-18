"""O258: parser probe alert — FL httpx fallback ok, sustained fail alert, cooldown."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from parser_probe_alert import (  # noqa: E402
    alert_cooldown_ok,
    evaluate_probe_alert,
    format_probe_alert_text,
    mark_alert_sent,
    maybe_send_probe_alert,
    parser_probe_alert_cooldown_sec,
)
from storage import ProjectStorage  # noqa: E402


def _lines(*rows: str) -> list[str]:
    return list(rows)


def test_fl_browser_fail_httpx_ok_no_alert() -> None:
    lines = _lines(
        "2026-06-16 06:10 fetch:fl outcome=fail reason=browser_error proxy_hint=dc err=Executable doesn't exist",
        "2026-06-16 06:10 fetch:fl stage=fallback httpx outcome=ok elapsed=1.2s",
        "2026-06-16 06:10 fetch:kwork outcome=ok reason=ok parsed=12",
        "2026-06-16 06:10 fetch:youdo outcome=ok reason=ok parsed=40",
    )
    result = evaluate_probe_alert(lines)
    assert result["status"] == "ok"
    assert result["should_alert"] is False
    assert result["sources"]["fl"]["effective_outcome"] == "ok"
    assert result["sources"]["fl"]["outcome"] == "fail"


def test_sustained_youdo_fail_should_alert() -> None:
    lines = _lines(
        "fetch:fl outcome=ok reason=ok parsed=30",
        "fetch:kwork outcome=ok reason=ok parsed=10",
        "fetch:youdo outcome=fail reason=antibot parsed=0",
    )
    result = evaluate_probe_alert(lines)
    assert result["status"] == "fail"
    assert result["should_alert"] is True
    assert "youdo" in result["failing_sources"]

    text = format_probe_alert_text(result)
    assert text.startswith("FLPARSING · парсеры")
    assert "status=fail" in text
    assert "youdo: outcome=fail" in text
    assert "reason=antibot" in text


def test_fl_browser_fail_without_httpx_ok_alerts() -> None:
    lines = _lines(
        "fetch:fl outcome=fail reason=browser_error parsed=0",
        "fetch:fl stage=fallback httpx outcome=fail reason=httpx_empty parsed=0",
        "fetch:kwork outcome=ok reason=ok parsed=10",
    )
    result = evaluate_probe_alert(lines)
    assert result["status"] == "fail"
    assert result["should_alert"] is True
    assert result["sources"]["fl"]["effective_outcome"] == "fail"


def test_maybe_send_respects_cooldown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    storage = ProjectStorage(tmp_path / "probe.db")
    lines = _lines("fetch:youdo outcome=fail reason=timeout parsed=0")
    result = evaluate_probe_alert(lines)
    sent_texts: list[str] = []

    def _fake_send(text: str) -> tuple[bool, str]:
        sent_texts.append(text)
        return True, "@flparsingbot"

    monkeypatch.setattr("health_check.send_flparsing_admin_text", _fake_send)
    assert maybe_send_probe_alert(storage, result)[0] is True
    assert len(sent_texts) == 1
    assert maybe_send_probe_alert(storage, result)[0] is False

    mark_alert_sent(storage)
    storage.set_setting(
        "parser_probe_last_alert_at",
        str(int(time.time()) - parser_probe_alert_cooldown_sec() - 5),
    )
    assert alert_cooldown_ok(storage) is True
    assert maybe_send_probe_alert(storage, result)[0] is True
    assert len(sent_texts) == 2


def test_probe_ok_never_sends(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    storage = ProjectStorage(tmp_path / "ok.db")
    result = evaluate_probe_alert(_lines("fetch:fl outcome=ok reason=ok parsed=25"))
    calls: list[str] = []

    monkeypatch.setattr(
        "health_check.send_flparsing_admin_text",
        lambda text: calls.append(text) or (True, "ok"),
    )
    sent, detail = maybe_send_probe_alert(storage, result)
    assert sent is False
    assert detail == "probe_ok"
    assert calls == []
