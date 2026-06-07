"""O120: TG Bot API proxy pool — failover, ban, probe."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

import tg_proxy_pool as pool  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_pool(monkeypatch, tmp_path):
    pool.reset_pool_for_tests()
    monkeypatch.setenv("TG_PROXY_URL", "http://p1.example.com:8000:user:pass")
    monkeypatch.setenv("TELETHON_PROXY_ACC1", "http://p2.example.com:8000:user:pass")
    monkeypatch.setenv("TELETHON_PROXY_ACC2", "http://p3.example.com:8000:user:pass")
    monkeypatch.delenv("TG_PROXY_URLS", raising=False)
    monkeypatch.delenv("TG_PROXY_DIRECT", raising=False)
    monkeypatch.setenv("TG_PROXY_STRIKES", "2")
    monkeypatch.setenv("TG_PROXY_POOL_JSON", str(tmp_path / "tg_proxy_pool.json"))
    monkeypatch.setattr(pool, "_STRIKES_TO_BAN", 2)
    yield
    pool.reset_pool_for_tests()


def test_build_pool_urls_dedupes_telethon():
    urls = pool.build_pool_urls()
    hosts = [pool._hint_from_url(u) for u in urls]
    assert "p1.example.com:8000" in hosts
    assert "p2.example.com:8000" in hosts
    assert "p3.example.com:8000" in hosts
    assert len(hosts) == len(set(hosts))


def test_build_pool_urls_explicit_list(monkeypatch):
    monkeypatch.setenv(
        "TG_PROXY_URLS",
        "http://a.example.com:1:u:p,http://b.example.com:2:u:p",
    )
    pool.reset_pool_for_tests()
    urls = pool.build_pool_urls()
    assert len(urls) == 2
    assert pool._hint_from_url(urls[0]) == "a.example.com:1"


def test_failover_switches_to_second_slot(monkeypatch):
    pool.reset_pool_for_tests()
    pool._pool_urls = [
        "http://p1.example.com:8000:u:p",
        "http://p2.example.com:8000:u:p",
    ]
    pool._active_slot = 0
    monkeypatch.setattr(pool, "_notify_proxy_switch", lambda **kw: None)
    monkeypatch.setattr(pool, "_send_owner_alert", lambda *a, **k: None)

    sess = requests.Session()
    sess.trust_env = False
    with patch.object(
        sess,
        "request",
        side_effect=[
            requests.ConnectTimeout("t1"),
            MagicMock(status_code=200),
        ],
    ) as mock_req:
        resp = pool.tg_http_request("GET", "https://api.telegram.org/", session=sess)

    assert resp.status_code == 200
    assert mock_req.call_count == 2
    assert pool._active_slot == 1


def test_ban_after_n_strikes(monkeypatch, tmp_path):
    pool.reset_pool_for_tests()
    pool._pool_urls = [
        "http://p1.example.com:8000:u:p",
        "http://p2.example.com:8000:u:p",
    ]
    pool._active_slot = 0
    url = pool._pool_urls[0]
    pool._record_strike(url, reason="connect_timeout", slot_idx=0)
    assert not pool._is_banned(url)
    pool._record_strike(url, reason="connect_timeout", slot_idx=0)
    assert pool._is_banned(url)
    data = json.loads((tmp_path / "tg_proxy_pool.json").read_text(encoding="utf-8"))
    assert "p1.example.com:8000" in data.get("banned", {})


def test_advance_failover_notifies(monkeypatch):
    pool.reset_pool_for_tests()
    pool._pool_urls = [
        "http://p1.example.com:8000:u:p",
        "http://p2.example.com:8000:u:p",
    ]
    pool._active_slot = 0
    pool._ban_url(pool._pool_urls[0], reason="probe_fail", slot_idx=0)
    alerts: list[str] = []
    monkeypatch.setattr(pool, "_send_owner_alert", lambda text, **kw: alerts.append(text))
    assert pool.advance_failover(reason="probe_fail") is True
    assert pool._active_slot == 1
    assert alerts and "TG Bot API" in alerts[0]


def test_probe_proxy_https_mock(monkeypatch):
    resp = MagicMock(status_code=200)
    monkeypatch.setattr(requests, "get", lambda *a, **k: resp)
    ok, detail = pool.probe_proxy_https("http://p1.example.com:8000:u:p")
    assert ok is True
    assert "200" in detail


def test_tg_proxy_direct_when_pool_exhausted(monkeypatch):
    pool.reset_pool_for_tests()
    pool._pool_urls = ["http://p1.example.com:8000:u:p"]
    pool._ban_url(pool._pool_urls[0], reason="x", slot_idx=0)
    monkeypatch.setenv("TG_PROXY_DIRECT", "1")
    proxies = pool.get_active_proxies_dict()
    assert proxies.get("https") is None
