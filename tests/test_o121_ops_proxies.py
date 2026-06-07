"""O121-w1: /ops/ proxies API — mask, JSON shape, control validation."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

import proxy_ops as ops  # noqa: E402
import tg_proxy_pool as tg_pool  # noqa: E402
from exchange_proxy import reset_cascade_state_for_tests  # noqa: E402


@pytest.fixture(autouse=True)
def _reset(monkeypatch, tmp_path):
    tg_pool.reset_pool_for_tests()
    reset_cascade_state_for_tests()
    monkeypatch.setenv("TG_PROXY_URLS", "http://a.example.com:1:u:p,http://b.example.com:2:u:p")
    monkeypatch.delenv("TG_PROXY_URL", raising=False)
    monkeypatch.setenv("TG_PROXY_POOL_JSON", str(tmp_path / "tg_proxy_pool.json"))
    monkeypatch.setenv("EXCHANGE_PROXY_URLS", "http://x.example.com:3:u:p")
    monkeypatch.delenv("FL_PROXY_URLS", raising=False)
    monkeypatch.delenv("KWORK_PROXY_URLS", raising=False)
    yield
    tg_pool.reset_pool_for_tests()
    reset_cascade_state_for_tests()


def test_mask_hides_password() -> None:
    masked = ops.mask("http://host.example.com:8080:myuser:secretpass")
    assert "secretpass" not in masked
    assert "***" in masked
    assert "myuser" in masked


def test_proxies_json_shape() -> None:
    payload = ops.strip_internal_urls(ops.collect_proxies_payload())
    assert payload["auto_failover"] is True
    assert isinstance(payload["groups"], list)
    assert payload["groups"]
    first = payload["groups"][0]
    assert first["id"] == "tg-bot"
    assert "slots" in first
    slot = first["slots"][0]
    assert set(slot.keys()) == {
        "slot",
        "mask",
        "status",
        "status_label",
        "active",
        "banned_until",
        "reason",
        "strikes",
    }
    assert "_url" not in slot


def test_control_probe_requires_group_slot() -> None:
    bad = ops.run_proxy_control(action="probe", group="", slot=None)
    assert bad["ok"] is False
    assert "group" in bad["message"].lower() or "slot" in bad["message"].lower()


def test_control_switch_tg_bot(monkeypatch) -> None:
    tg_pool.reset_pool_for_tests()
    tg_pool._pool_urls = [
        "http://p1.example.com:8000:u:p",
        "http://p2.example.com:8000:u:p",
    ]
    tg_pool._active_slot = 0
    ok = ops.run_proxy_control(action="switch", group="tg-bot", slot=2)
    assert ok["ok"] is True
    assert tg_pool._active_slot == 1


def test_control_switch_rejects_telethon() -> None:
    bad = ops.run_proxy_control(action="switch", group="telethon", slot=1)
    assert bad["ok"] is False


@patch.object(ops, "tcp_ok", return_value=(True, "ok"))
@patch.object(ops, "https_probe", return_value=(True, "HTTP 200"))
def test_control_probe_single(_https, _tcp) -> None:
    result = ops.run_proxy_control(action="probe", group="tg-bot", slot=1)
    assert result["ok"] is True
    assert result["probe"]["ok"] is True
    assert result["probe"]["tcp"]["ok"] is True


def test_slot_status_label_mapping() -> None:
    assert ops.slot_status_label(status="ok", banned_until=None) == "Работает"
    assert ops.slot_status_label(status="warn", banned_until=None) == "Нестабильно — были ошибки"
    assert ops.slot_status_label(status="bad", banned_until="2026-01-01T00:00:00Z") == (
        "Временно отключён (бан)"
    )
    assert ops.slot_status_label(status="ok", banned_until=None, reason_raw="probe_fail") == (
        "Не открывает сайт через прокси"
    )
    assert ops.slot_status_label(status="warn", banned_until=None, reason_raw="strikes") == (
        "Много ошибок подряд"
    )


def test_control_clear_bans(monkeypatch, tmp_path) -> None:
    tg_pool.reset_pool_for_tests()
    reset_cascade_state_for_tests()
    monkeypatch.setenv("TG_PROXY_URLS", "http://a.example.com:1:u:p,http://b.example.com:2:u:p")
    monkeypatch.setenv("TG_PROXY_POOL_JSON", str(tmp_path / "tg_proxy_pool.json"))
    monkeypatch.setenv("EXCHANGE_PROXY_URLS", "http://x.example.com:3:u:p")

    tg_pool._pool_urls = ["http://p1.example.com:8000:u:p"]
    tg_pool._banned_until["p1.example.com:8000"] = 9999999999.0
    tg_pool._ban_meta["p1.example.com:8000"] = {"reason": "probe_fail"}
    tg_pool._strike_count["p1.example.com:8000"] = 2

    import exchange_proxy as ex  # noqa: E402

    ex._banned_until["fl:p2.example.com:8000"] = 9999999999.0
    ex._ban_meta["fl:p2.example.com:8000"] = {"reason": "strikes_3", "until": 9999999999.0}
    ex._persistence_loaded = True

    result = ops.run_proxy_control(action="clear-bans")
    assert result["ok"] is True
    assert "бан" in result["message"].lower()
    assert result.get("cleared", 0) >= 1
    assert not tg_pool._banned_until
    assert not tg_pool._strike_count
    assert not ex._banned_until
    slot = result["proxies"]["groups"][0]["slots"][0]
    assert slot["status_label"] == "Работает"


def test_control_switch_banned_shows_error() -> None:
    tg_pool.reset_pool_for_tests()
    tg_pool._pool_urls = ["http://p1.example.com:8000:u:p", "http://p2.example.com:8000:u:p"]
    tg_pool._active_slot = 0
    tg_pool._banned_until["p2.example.com:8000"] = 9999999999.0
    tg_pool._ban_meta["p2.example.com:8000"] = {"reason": "probe_fail"}
    bad = ops.run_proxy_control(action="switch", group="tg-bot", slot=2)
    assert bad["ok"] is False
    assert "забанен" in bad["message"].lower()
