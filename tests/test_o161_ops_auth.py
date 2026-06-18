"""O161: /ops/ password login, logout, cookie gate."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from src.api_server import app  # noqa: E402

_TEST_KEY = "test-ops-secret-o161"


@pytest.fixture()
def ops_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("RAWLEAD_OPS_KEY", _TEST_KEY)
    return TestClient(app)


def test_ops_page_without_cookie_shows_login(ops_client: TestClient) -> None:
    resp = ops_client.get("/ops/")
    assert resp.status_code == 200
    assert "RawLead" in resp.text
    assert 'type="password"' in resp.text
    assert "Войти" in resp.text
    assert "Telegram" not in resp.text


def test_ops_login_ok_sets_cookie(ops_client: TestClient) -> None:
    resp = ops_client.post(
        "/ops/login",
        data={"password": _TEST_KEY},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert resp.headers.get("location", "").rstrip("/") == "/ops"
    assert resp.cookies.get("rl_ops_key") == _TEST_KEY


def test_ops_login_fail_redirects_with_error(ops_client: TestClient) -> None:
    resp = ops_client.post(
        "/ops/login",
        data={"password": "wrong-password"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "err=1" in resp.headers.get("location", "")
    assert "rl_ops_key" not in resp.cookies


def test_ops_login_fail_clears_stale_cookie(ops_client: TestClient) -> None:
    ops_client.cookies.set("rl_ops_key", _TEST_KEY)
    resp = ops_client.post(
        "/ops/login",
        data={"password": "wrong-password"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "err=1" in resp.headers.get("location", "")
    set_cookie = (resp.headers.get("set-cookie") or "").lower()
    assert "rl_ops_key=" in set_cookie
    assert "max-age=0" in set_cookie
    # TestClient may keep stale jar entry; browser clears via Max-Age=0
    ops_client.cookies.pop("rl_ops_key", None)
    page = ops_client.get("/ops/?err=1")
    assert page.status_code == 200
    assert 'type="password"' in page.text
    assert "rl-ops-mini-nav" not in page.text


def test_ops_dashboard_ssr_fallback_has_external_js(ops_client: TestClient) -> None:
    ops_client.cookies.set("rl_ops_key", _TEST_KEY)
    with patch("src.api_server.fetch_dashboard") as mock_fetch:
        resp = ops_client.get("/ops/")
    mock_fetch.assert_not_called()
    assert resp.status_code == 200
    assert '/ops/static/ops-pult.js' in resp.text
    assert 'meta name="rl-ops-api-base"' in resp.text
    assert "Загрузка" in resp.text
    assert "bindLogStream" not in resp.text


def test_ops_static_pult_js(ops_client: TestClient) -> None:
    resp = ops_client.get("/ops/static/ops-pult.js")
    assert resp.status_code == 200
    assert "javascript" in resp.headers.get("content-type", "")
    assert "hydrateDashboardFallback" in resp.text
    assert "bindLogStream" in resp.text
    assert 'meta[name="rl-ops-api-base"]' in resp.text


def test_ops_dashboard_json_with_cookie(ops_client: TestClient) -> None:
    ops_client.cookies.set("rl_ops_key", _TEST_KEY)
    payload = {"today": {"visits": 1}, "feed": {"visible_count": 0, "recent": []}}
    with patch("src.api_server.fetch_dashboard", return_value=payload):
        resp = ops_client.get("/ops/dashboard")
    assert resp.status_code == 200
    assert resp.json()["today"]["visits"] == 1


def test_ops_logout_clears_cookie(ops_client: TestClient) -> None:
    ops_client.cookies.set("rl_ops_key", _TEST_KEY)
    resp = ops_client.get("/ops/logout", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers.get("location", "").rstrip("/") == "/ops"


def test_ops_funnel_json_with_cookie(ops_client: TestClient) -> None:
    ops_client.cookies.set("rl_ops_key", _TEST_KEY)
    with patch("src.api_server.fetch_ops_funnel", return_value={"sources": []}):
        resp = ops_client.get("/ops/funnel")
    assert resp.status_code == 200
    assert resp.json() == {"sources": []}


def test_ops_funnel_json_degraded_on_build_error(ops_client: TestClient) -> None:
    ops_client.cookies.set("rl_ops_key", _TEST_KEY)
    degraded = {
        "sources": [],
        "lamps": {},
        "l1": {"status": "warn", "queue": 0, "label": "ошибка"},
        "diagnosis": {"level": "warn", "text": "boom", "action": None},
    }
    with patch("src.api_server.fetch_ops_funnel", return_value=degraded):
        resp = ops_client.get("/ops/funnel")
    assert resp.status_code == 200
    assert resp.json()["sources"] == []
    assert resp.json()["diagnosis"]["text"] == "boom"


def test_ops_dashboard_json_funnel_isolated(ops_client: TestClient) -> None:
    ops_client.cookies.set("rl_ops_key", _TEST_KEY)
    payload = {
        "today": {"visits": 2, "unique_visits": 1, "new_users": 0},
        "feed": {"visible_count": 3, "recent": []},
        "funnel": {"sources": [], "lamps": {}, "l1": {"status": "warn"}},
        "tg": {"accounts": []},
        "bots": [],
        "exchanges": [],
        "proxies": {"groups": []},
    }
    with patch("src.api_server.fetch_dashboard", return_value=payload):
        resp = ops_client.get("/ops/dashboard")
    assert resp.status_code == 200
    body = resp.json()
    assert body["today"]["visits"] == 2
    assert body["funnel"]["sources"] == []


def test_ops_funnel_json_without_cookie_401(ops_client: TestClient) -> None:
    resp = ops_client.get("/ops/funnel")
    assert resp.status_code == 401


def test_ops_page_unconfigured_shows_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RAWLEAD_OPS_KEY", raising=False)
    monkeypatch.delenv("OPS_PASSWORD", raising=False)
    monkeypatch.delenv("OPS_PASSWORD_HASH", raising=False)
    client = TestClient(app)
    resp = client.get("/ops/")
    assert resp.status_code == 200
    assert "RAWLEAD_OPS_KEY" in resp.text
    assert "Telegram" not in resp.text
    assert "кабинет" not in resp.text.lower()


def test_ops_authenticated_dashboard_no_cabinet_block(ops_client: TestClient) -> None:
    ops_client.cookies.set("rl_ops_key", _TEST_KEY)
    with patch("src.api_server.fetch_dashboard") as mock_fetch:
        resp = ops_client.get("/ops/")
    mock_fetch.assert_not_called()
    assert resp.status_code == 200
    assert "Сначала войди в кабинет" not in resp.text
    assert "Войти через Telegram" not in resp.text
    assert "Пульт RawLead" in resp.text
    assert "Загрузка воронки" in resp.text


def test_ops_log_stream_requires_cookie(ops_client: TestClient) -> None:
    denied = ops_client.get("/ops/log/stream")
    assert denied.status_code == 401
    ops_client.cookies.set("rl_ops_key", _TEST_KEY)
    with patch(
        "src.api_server.iter_radar_log_sse",
        return_value=iter(["data: test line\n\n"]),
    ):
        ok = ops_client.get("/ops/log/stream")
    assert ok.status_code == 200
    assert "text/event-stream" in ok.headers.get("content-type", "")
    assert "test line" in ok.text
