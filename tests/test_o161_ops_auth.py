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


def test_ops_logout_clears_cookie(ops_client: TestClient) -> None:
    ops_client.cookies.set("rl_ops_key", _TEST_KEY)
    resp = ops_client.get("/ops/logout", follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers.get("location", "").rstrip("/") == "/ops"


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
