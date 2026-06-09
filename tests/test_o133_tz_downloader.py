"""O133: FL/Kwork authenticated session для скачивания ТЗ-вложений."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

import tz_session as _sess_mod
from tz_session import (
    _source_key,
    clear_all_sessions,
    download_with_auth_session,
    enforce_rate_limit,
    fetch_detail_html_with_auth,
    get_auth_session,
    invalidate_session,
)


@pytest.fixture(autouse=True)
def _reset_sessions():
    clear_all_sessions()
    yield
    clear_all_sessions()


# ---------------------------------------------------------------------------
# _source_key
# ---------------------------------------------------------------------------


def test_source_key_fl():
    assert _source_key("fl") == "fl"
    assert _source_key("FL") == "fl"


def test_source_key_kwork():
    assert _source_key("kwork") == "kwork"
    assert _source_key("KWORK") == "kwork"


def test_source_key_unknown():
    assert _source_key("youdo") == "youdo"
    assert _source_key("") == ""


# ---------------------------------------------------------------------------
# FL login
# ---------------------------------------------------------------------------


def test_fl_login_phpsessid_cookies(monkeypatch: pytest.MonkeyPatch):
    """O133-TZ-SMOKE: exported FL cookies with PHPSESSID → logged in without POST."""
    import json

    import requests

    monkeypatch.delenv("FL_TZ_EMAIL", raising=False)
    monkeypatch.delenv("FL_TZ_PASSWORD", raising=False)
    cookies_json = json.dumps(
        [{"name": "PHPSESSID", "value": "sess-abc", "domain": ".fl.ru", "path": "/"}]
    )
    monkeypatch.setenv("FL_TZ_SESSION", cookies_json)

    sess = requests.Session()
    assert _sess_mod._login_fl(sess) is True


def test_fl_login_legacy_id_pwd_cookies(monkeypatch: pytest.MonkeyPatch):
    import json

    import requests

    monkeypatch.delenv("FL_TZ_EMAIL", raising=False)
    monkeypatch.delenv("FL_TZ_PASSWORD", raising=False)
    cookies_json = json.dumps(
        [
            {"name": "id", "value": "12345", "domain": ".fl.ru", "path": "/"},
            {"name": "pwd", "value": "hash", "domain": ".fl.ru", "path": "/"},
        ]
    )
    monkeypatch.setenv("FL_TZ_SESSION", cookies_json)

    sess = requests.Session()
    assert _sess_mod._login_fl(sess) is True


def _mock_fl_response(*, cookies: dict | None = None, url: str = "https://www.fl.ru/") -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.url = url
    resp.text = ""
    if cookies:
        for k, v in cookies.items():
            resp.cookies = MagicMock()
    return resp


def test_fl_login_ok(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FL_TZ_EMAIL", "test@example.com")
    monkeypatch.setenv("FL_TZ_PASSWORD", "secret")

    mock_sess = MagicMock()
    mock_sess.cookies.keys.return_value = ["fl_user_id", "fl_uid"]
    mock_sess.headers = {}
    mock_sess.get.return_value = MagicMock(status_code=200, url="https://www.fl.ru/", text="")
    mock_sess.post.return_value = MagicMock(status_code=200, url="https://www.fl.ru/account/")

    with patch.object(_sess_mod, "_new_session", return_value=mock_sess):
        sess = get_auth_session("fl")

    assert sess is mock_sess


def test_fl_login_no_creds(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("FL_TZ_EMAIL", raising=False)
    monkeypatch.delenv("FL_TZ_PASSWORD", raising=False)

    mock_sess = MagicMock()
    mock_sess.cookies.keys.return_value = []
    mock_sess.headers = {}

    with patch.object(_sess_mod, "_new_session", return_value=mock_sess):
        sess = get_auth_session("fl")

    assert sess is None


def test_fl_login_fail_bad_response(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FL_TZ_EMAIL", "test@example.com")
    monkeypatch.setenv("FL_TZ_PASSWORD", "wrong")

    mock_sess = MagicMock()
    mock_sess.headers = {}
    mock_sess.cookies.keys.return_value = []
    mock_sess.cookies.get.return_value = None
    mock_sess.get.return_value = MagicMock(status_code=200, url=_sess_mod._FL_HOME_URL, text="")
    mock_sess.post.return_value = MagicMock(
        status_code=200, url=_sess_mod._FL_LOGIN_URL
    )

    with patch.object(_sess_mod, "_new_session", return_value=mock_sess):
        sess = get_auth_session("fl")

    assert sess is None


def test_fl_login_network_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FL_TZ_EMAIL", "test@example.com")
    monkeypatch.setenv("FL_TZ_PASSWORD", "secret")

    mock_sess = MagicMock()
    mock_sess.headers = {}
    mock_sess.get.side_effect = ConnectionError("network down")

    with patch.object(_sess_mod, "_new_session", return_value=mock_sess):
        sess = get_auth_session("fl")

    assert sess is None


# ---------------------------------------------------------------------------
# Kwork login
# ---------------------------------------------------------------------------


def test_kwork_login_ok(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KWORK_TZ_EMAIL", "kw@example.com")
    monkeypatch.setenv("KWORK_TZ_PASSWORD", "kwsecret")

    mock_sess = MagicMock()
    mock_sess.headers = {}
    mock_sess.cookies.get.side_effect = lambda k, d=None: (
        "token123" if k in ("kwtoken", "csrf_user_token") else d
    )
    mock_sess.cookies.keys.return_value = ["kwtoken", "csrf_user_token"]
    login_page = MagicMock(status_code=200, text="<html></html>")
    login_resp = MagicMock(
        status_code=200,
        headers={"content-type": "application/json"},
    )
    login_resp.json.return_value = {"success": True, "csrftoken": "csrf-abc"}
    mock_sess.get.return_value = login_page
    mock_sess.post.return_value = login_resp

    with patch.object(_sess_mod, "_new_session", return_value=mock_sess):
        sess = get_auth_session("kwork")

    assert sess is mock_sess
    mock_sess.post.assert_called_once()
    assert "/api/user/login" in mock_sess.post.call_args[0][0]


def test_kwork_login_no_creds(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("KWORK_TZ_EMAIL", raising=False)
    monkeypatch.delenv("KWORK_TZ_PASSWORD", raising=False)

    mock_sess = MagicMock()
    mock_sess.headers = {}

    with patch.object(_sess_mod, "_new_session", return_value=mock_sess):
        sess = get_auth_session("kwork")

    assert sess is None


def test_kwork_login_fail(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KWORK_TZ_EMAIL", "kw@example.com")
    monkeypatch.setenv("KWORK_TZ_PASSWORD", "wrong")

    mock_sess = MagicMock()
    mock_sess.headers = {}
    mock_sess.cookies.get.return_value = None
    mock_sess.get.return_value = MagicMock(status_code=200, text="")
    login_resp = MagicMock(
        status_code=200,
        headers={"content-type": "application/json"},
    )
    login_resp.json.return_value = {"status": "error", "message": "Invalid credentials"}
    mock_sess.post.return_value = login_resp

    with patch.object(_sess_mod, "_new_session", return_value=mock_sess):
        sess = get_auth_session("kwork")

    assert sess is None


# ---------------------------------------------------------------------------
# Session cache & TTL
# ---------------------------------------------------------------------------


def test_session_cached(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FL_TZ_EMAIL", "test@example.com")
    monkeypatch.setenv("FL_TZ_PASSWORD", "secret")

    mock_sess = MagicMock()
    mock_sess.headers = {}
    mock_sess.cookies.keys.return_value = ["fl_user_id"]
    mock_sess.get.return_value = MagicMock(status_code=200, url="https://www.fl.ru/", text="")
    mock_sess.post.return_value = MagicMock(status_code=200, url="https://www.fl.ru/account/")

    with patch.object(_sess_mod, "_new_session", return_value=mock_sess):
        s1 = get_auth_session("fl")
        s2 = get_auth_session("fl")  # second call should return cached

    assert s1 is s2
    assert mock_sess.get.call_count == 1  # home only called once


def test_invalidate_session(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FL_TZ_EMAIL", "test@example.com")
    monkeypatch.setenv("FL_TZ_PASSWORD", "secret")

    call_count = 0

    def _make_sess(*_args):
        nonlocal call_count
        call_count += 1
        m = MagicMock()
        m.headers = {}
        m.cookies.keys.return_value = ["fl_user_id"]
        m.get.return_value = MagicMock(status_code=200, url="https://www.fl.ru/", text="")
        m.post.return_value = MagicMock(status_code=200, url="https://www.fl.ru/account/")
        return m

    with patch.object(_sess_mod, "_new_session", side_effect=_make_sess):
        get_auth_session("fl")
        assert call_count == 1
        invalidate_session("fl")
        get_auth_session("fl")
        assert call_count == 2  # re-login after invalidation


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


def test_rate_limit_enforced(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TZ_SESSION_RATE_LIMIT_SEC", "0.05")
    clear_all_sessions()

    t0 = time.monotonic()
    enforce_rate_limit("fl")
    enforce_rate_limit("fl")  # should wait ~0.05s
    elapsed = time.monotonic() - t0

    assert elapsed >= 0.03, f"expected >=0.03s wait, got {elapsed:.3f}s"


def test_rate_limit_different_sources_independent(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("TZ_SESSION_RATE_LIMIT_SEC", "0.1")
    clear_all_sessions()

    t0 = time.monotonic()
    enforce_rate_limit("fl")
    enforce_rate_limit("kwork")  # different source — should not wait
    elapsed = time.monotonic() - t0

    assert elapsed < 0.08, f"different sources should not throttle, elapsed={elapsed:.3f}s"


# ---------------------------------------------------------------------------
# download_with_auth_session
# ---------------------------------------------------------------------------


def test_download_auth_no_session(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("FL_TZ_EMAIL", raising=False)
    monkeypatch.delenv("FL_TZ_PASSWORD", raising=False)
    monkeypatch.setenv("TZ_SESSION_RATE_LIMIT_SEC", "0")

    mock_sess = MagicMock()
    mock_sess.headers = {}
    with patch.object(_sess_mod, "_new_session", return_value=mock_sess):
        data, err = download_with_auth_session("https://www.fl.ru/attach/file.pdf", "fl")

    assert data is None
    assert err == "no_session"


def test_download_auth_success(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FL_TZ_EMAIL", "test@example.com")
    monkeypatch.setenv("FL_TZ_PASSWORD", "secret")
    monkeypatch.setenv("TZ_SESSION_RATE_LIMIT_SEC", "0")

    mock_sess = MagicMock()
    mock_sess.headers = {}
    mock_sess.cookies.keys.return_value = ["fl_user_id"]
    mock_sess.get.side_effect = [
        MagicMock(status_code=200, url="https://www.fl.ru/", text=""),  # home
        MagicMock(status_code=200, content=b"PDF content here"),  # file download
    ]
    mock_sess.post.return_value = MagicMock(status_code=200, url="https://www.fl.ru/account/")

    with patch.object(_sess_mod, "_new_session", return_value=mock_sess):
        data, err = download_with_auth_session(
            "https://www.fl.ru/attach/spec.pdf", "fl"
        )

    assert data == b"PDF content here"
    assert err is None


def test_download_auth_still_403_after_relogin(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FL_TZ_EMAIL", "test@example.com")
    monkeypatch.setenv("FL_TZ_PASSWORD", "secret")
    monkeypatch.setenv("TZ_SESSION_RATE_LIMIT_SEC", "0")

    call_n = [0]

    def _make_sess(*_args):
        m = MagicMock()
        m.headers = {}
        m.cookies.keys.return_value = ["fl_user_id"]
        resp_home = MagicMock(status_code=200, url="https://www.fl.ru/", text="")
        resp_403 = MagicMock(status_code=403, content=b"")
        m.get.side_effect = [resp_home, resp_403]
        m.post.return_value = MagicMock(status_code=200, url="https://www.fl.ru/account/")
        call_n[0] += 1
        return m

    with patch.object(_sess_mod, "_new_session", side_effect=_make_sess):
        data, err = download_with_auth_session(
            "https://www.fl.ru/attach/private.pdf", "fl"
        )

    assert data is None
    assert err == "auth"


def test_download_auth_network_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FL_TZ_EMAIL", "test@example.com")
    monkeypatch.setenv("FL_TZ_PASSWORD", "secret")
    monkeypatch.setenv("TZ_SESSION_RATE_LIMIT_SEC", "0")

    mock_sess = MagicMock()
    mock_sess.headers = {}
    mock_sess.cookies.keys.return_value = ["fl_user_id"]
    resp_home = MagicMock(status_code=200, url="https://www.fl.ru/", text="")
    mock_sess.get.side_effect = [resp_home, ConnectionError("timeout")]
    mock_sess.post.return_value = MagicMock(status_code=200, url="https://www.fl.ru/account/")

    with patch.object(_sess_mod, "_new_session", return_value=mock_sess):
        data, err = download_with_auth_session(
            "https://www.fl.ru/attach/spec.pdf", "fl"
        )

    assert data is None
    assert err is None  # network error, not auth error


def test_fetch_detail_html_with_auth(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KWORK_TZ_EMAIL", "kw@example.com")
    monkeypatch.setenv("KWORK_TZ_PASSWORD", "kwsecret")
    monkeypatch.setenv("TZ_SESSION_RATE_LIMIT_SEC", "0")

    mock_sess = MagicMock()
    mock_sess.headers = {}
    mock_sess.cookies.get.side_effect = lambda k, d=None: (
        "x" if k in ("kwtoken", "csrf_user_token") else d
    )
    mock_sess.cookies.keys.return_value = ["kwtoken"]
    mock_sess.get.side_effect = [
        MagicMock(status_code=200, text="<html></html>"),
        MagicMock(
            status_code=200,
            content=b'<a href="https://kwork.ru/files/tz.pdf">x</a>',
            encoding="utf-8",
        ),
    ]
    login_resp = MagicMock(
        status_code=200,
        headers={"content-type": "application/json"},
    )
    login_resp.json.return_value = {"success": True}
    mock_sess.post.return_value = login_resp

    with patch.object(_sess_mod, "_new_session", return_value=mock_sess):
        html = fetch_detail_html_with_auth(
            "https://kwork.ru/projects/3193806/view", "kwork"
        )

    assert "tz.pdf" in html


def test_download_rejects_html_login_wall(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("FL_TZ_EMAIL", "test@example.com")
    monkeypatch.setenv("FL_TZ_PASSWORD", "secret")
    monkeypatch.setenv("TZ_SESSION_RATE_LIMIT_SEC", "0")

    mock_sess = MagicMock()
    mock_sess.headers = {}
    mock_sess.cookies.keys.return_value = ["fl_user_id"]
    mock_sess.get.side_effect = [
        MagicMock(status_code=200, url="https://www.fl.ru/", text=""),
        MagicMock(status_code=200, content=b"<!DOCTYPE html><html>login</html>"),
    ]
    mock_sess.post.return_value = MagicMock(status_code=200, url="https://www.fl.ru/account/")

    with patch.object(_sess_mod, "_new_session", return_value=mock_sess):
        data, err = download_with_auth_session(
            "https://www.fl.ru/attach/spec.pdf", "fl"
        )

    assert data is None
    assert err == "auth"


# ---------------------------------------------------------------------------
# Integration: tz_attachments uses auth session on 401/403
# ---------------------------------------------------------------------------


def test_download_attachment_auth_fallback(monkeypatch: pytest.MonkeyPatch):
    """download_attachment: anon 401 → auth session called."""
    import tz_attachments as ta

    monkeypatch.setenv("TZ_SESSION_RATE_LIMIT_SEC", "0")

    anon_resp = MagicMock(status_code=401)

    with patch("tz_attachments.exchange_get", return_value=anon_resp):
        with patch(
            "tz_session.download_with_auth_session",
            return_value=(b"TZ content", None),
        ) as mock_auth:
            cfg = MagicMock()
            cfg.http_user_agent = "test-ua"
            data, err = ta.download_attachment(
                "https://www.fl.ru/attach/spec.docx", "fl", cfg
            )

    mock_auth.assert_called_once()
    assert data == b"TZ content"
    assert err is None


def test_download_attachment_auth_fallback_no_creds(monkeypatch: pytest.MonkeyPatch):
    """download_attachment: anon 401, no session → 'auth' error."""
    import tz_attachments as ta

    anon_resp = MagicMock(status_code=401)

    with patch("tz_attachments.exchange_get", return_value=anon_resp):
        with patch(
            "tz_session.download_with_auth_session",
            return_value=(None, "no_session"),
        ):
            cfg = MagicMock()
            cfg.http_user_agent = "test-ua"
            data, err = ta.download_attachment(
                "https://www.fl.ru/attach/spec.docx", "fl", cfg
            )

    assert data is None
    assert err == "auth"


def test_enrich_body_auth_success_on_probe_401(monkeypatch: pytest.MonkeyPatch):
    """enrich_body: probe returns -1 → auth session downloads → extracted."""
    import tz_attachments as ta

    monkeypatch.setenv("TZ_SESSION_RATE_LIMIT_SEC", "0")

    docx_content = b"PK\x03\x04"  # minimal fake docx header

    page_html = (
        '<html><body>'
        '<a href="https://www.fl.ru/attach/brief.docx">Скачать ТЗ</a>'
        '</body></html>'
    )

    with patch("tz_attachments.probe_content_length", return_value=-1):
        with patch(
            "tz_session.download_with_auth_session",
            return_value=(docx_content, None),
        ):
            with patch(
                "tz_attachments.extract_attachment_text",
                return_value=("Текст ТЗ из файла", ("brief.docx",)),
            ):
                cfg = MagicMock()
                cfg.http_user_agent = "test-ua"
                result = ta.enrich_body_with_attachments(
                    source="fl",
                    page_html=page_html,
                    base_text="Сделать лендинг",
                    cfg=cfg,
                    page_url="https://www.fl.ru/projects/12345/",
                )

    assert result.attachment_extracted is True
    assert "Текст ТЗ из файла" in result.body
    assert ta.ATTACHMENT_EXTRACTED_MARKER in result.body


def test_enrich_body_probe_401_no_session_marks_skipped_auth(monkeypatch: pytest.MonkeyPatch):
    """enrich_body: probe -1, no session → skipped_auth marker."""
    import tz_attachments as ta

    monkeypatch.setenv("TZ_SESSION_RATE_LIMIT_SEC", "0")

    page_html = (
        '<html><body>'
        '<a href="https://www.fl.ru/attach/brief.pdf">brief.pdf</a>'
        '</body></html>'
    )

    with patch("tz_attachments.probe_content_length", return_value=-1):
        with patch(
            "tz_session.download_with_auth_session",
            return_value=(None, "no_session"),
        ):
            cfg = MagicMock()
            cfg.http_user_agent = "test-ua"
            result = ta.enrich_body_with_attachments(
                source="fl",
                page_html=page_html,
                base_text="base",
                cfg=cfg,
                page_url="https://www.fl.ru/projects/12345/",
            )

    assert result.attachment_extracted is False
    assert ta.SKIPPED_MARKER_PREFIX in result.body
    assert "нужен вход на биржу" in result.body
