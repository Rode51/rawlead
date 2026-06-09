"""O133: FL/Kwork authenticated session для скачивания ТЗ-вложений.

Только download + auth detail fetch — не для listing crawl.
Lazy login: сессия создаётся при первом 401/403, кешируется до TTL.
Rate limit: TZ_SESSION_RATE_LIMIT_SEC (default 2.0).
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

_TZ_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_FL_HOME_URL = "https://www.fl.ru/"
_FL_LOGIN_URL = "https://www.fl.ru/login.biz"
_KWORK_LOGIN_PAGE = "https://kwork.ru/login"
_KWORK_LOGIN_API = "https://kwork.ru/api/user/login"
# Legacy XHR endpoint (GET /user/login = профиль пользователя «login», не форма).
_KWORK_LOGIN_LEGACY = "https://kwork.ru/user/login"

# cache: source_key → (session | None, login_timestamp)
_sessions: dict[str, tuple[requests.Session | None, float]] = {}
# rate limit: source_key → last_request_monotonic
_last_request_at: dict[str, float] = {}


def _rate_limit_sec() -> float:
    try:
        return float(os.getenv("TZ_SESSION_RATE_LIMIT_SEC", "2.0"))
    except ValueError:
        return 2.0


def _session_ttl_sec() -> float:
    try:
        return float(os.getenv("TZ_SESSION_TTL_SEC", "3600.0"))
    except ValueError:
        return 3600.0


def _source_key(source: str) -> str:
    s = (source or "").lower()
    if "kwork" in s:
        return "kwork"
    if s.startswith("fl") or s == "fl":
        return "fl"
    return s


def _apply_exchange_proxy(sess: requests.Session, source: str) -> None:
    key = _source_key(source)
    if key not in ("fl", "kwork"):
        return
    try:
        from exchange_proxy import requests_proxies_for

        proxies = requests_proxies_for(key)
    except Exception:
        return
    if proxies.get("http") or proxies.get("https"):
        sess.proxies.update(proxies)


def _new_session(source: str = "") -> requests.Session:
    sess = requests.Session()
    sess.headers.update(
        {
            "User-Agent": _TZ_UA,
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        }
    )
    if source:
        _apply_exchange_proxy(sess, source)
    return sess


def _xhr_headers(*, referer: str) -> dict[str, str]:
    return {
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://kwork.ru",
        "Referer": referer,
    }


def _load_tz_session_cookies(sess: requests.Session, env_key: str) -> bool:
    """Load cookies from FL_TZ_SESSION / KWORK_TZ_SESSION (JSON list or file path)."""
    raw = (os.getenv(env_key) or "").strip()
    if not raw:
        return False
    path = Path(raw)
    if path.is_file():
        raw = path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("tz_session: %s is not valid JSON", env_key)
        return False
    items = data if isinstance(data, list) else data.get("cookies", [])
    if not isinstance(items, list):
        return False
    loaded = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        value = item.get("value")
        if not name or value is None:
            continue
        sess.cookies.set(
            str(name),
            str(value),
            domain=item.get("domain") or "",
            path=item.get("path") or "/",
        )
        loaded += 1
    if loaded:
        logger.info("tz_session: loaded %s cookies from %s", loaded, env_key)
    return loaded > 0


def _fl_session_ready(sess: requests.Session) -> bool:
    keys = set(sess.cookies.keys())
    if any(k.startswith("fl_") for k in keys):
        return True
    if "PHPSESSID" in keys:
        return True
    if "id" in keys and "pwd" in keys:
        return True
    return False


def _kwork_session_ready(sess: requests.Session) -> bool:
    return bool(sess.cookies.get("kwtoken") or sess.cookies.get("csrf_user_token"))


def _apply_kwork_csrf_from_body(sess: requests.Session, body: dict) -> None:
    token = body.get("csrftoken") or body.get("csrf_token")
    if token:
        sess.cookies.set("csrf_user_token", str(token), domain="kwork.ru", path="/")


def _extract_kwork_legacy_token(html: str) -> str:
    for pat in (
        r'name="_token"\s+value="([^"]+)"',
        r'"_token"\s*:\s*"([^"]+)"',
        r'csrf_user_token["\']?\s*[:=]\s*["\']([a-f0-9]+)',
    ):
        m = re.search(pat, html or "", re.I)
        if m:
            return m.group(1)
    return ""


def _login_fl(sess: requests.Session) -> bool:
    if _load_tz_session_cookies(sess, "FL_TZ_SESSION") and _fl_session_ready(sess):
        logger.info("tz_session: FL session cookies loaded")
        return True
    email = os.getenv("FL_TZ_EMAIL", "").strip()
    password = os.getenv("FL_TZ_PASSWORD", "").strip()
    if not email or not password:
        logger.debug("tz_session: FL_TZ_EMAIL/FL_TZ_PASSWORD not set — skip FL login")
        return False
    try:
        sess.get(_FL_HOME_URL, timeout=15, allow_redirects=True)
        resp = sess.post(
            _FL_LOGIN_URL,
            data={"login": email, "passwd": password},
            timeout=15,
            allow_redirects=True,
        )
        logged_in = _fl_session_ready(sess) or (resp.url or "").rstrip("/") not in (
            _FL_HOME_URL.rstrip("/"),
            _FL_LOGIN_URL.rstrip("/"),
        )
        if logged_in:
            logger.info("tz_session: FL login OK (%s)", email)
            return True
        logger.warning("tz_session: FL login failed — check FL_TZ_EMAIL/FL_TZ_PASSWORD")
        return False
    except Exception as exc:
        logger.warning("tz_session: FL login error: %s", exc)
        return False


def _login_kwork(sess: requests.Session) -> bool:
    cookies_loaded = _load_tz_session_cookies(sess, "KWORK_TZ_SESSION")
    if cookies_loaded and _kwork_session_ready(sess):
        logger.info("tz_session: Kwork session cookies loaded")
        return True
    if cookies_loaded and not _kwork_session_ready(sess):
        sess.cookies.clear()
        logger.info("tz_session: Kwork cookie file incomplete — trying password login")

    email = os.getenv("KWORK_TZ_EMAIL", "").strip()
    password = os.getenv("KWORK_TZ_PASSWORD", "").strip()
    if not email or not password:
        logger.debug("tz_session: KWORK_TZ_EMAIL/KWORK_TZ_PASSWORD not set — skip Kwork login")
        return False
    try:
        sess.get(_KWORK_LOGIN_PAGE, timeout=15, allow_redirects=True)
        resp = sess.post(
            _KWORK_LOGIN_API,
            json={"login": email, "password": password, "rememberMe": True},
            headers=_xhr_headers(referer=_KWORK_LOGIN_PAGE),
            timeout=15,
        )
        logged_in = False
        ct = resp.headers.get("content-type", "")
        if ct.startswith("application/json"):
            try:
                body = resp.json()
                if isinstance(body, dict):
                    logged_in = body.get("success") is True
                    if logged_in:
                        _apply_kwork_csrf_from_body(sess, body)
            except Exception:
                logged_in = False
        if not logged_in:
            logged_in = _kwork_session_ready(sess)
        if not logged_in:
            logged_in = _login_kwork_legacy(sess, email, password)
        if logged_in:
            logger.info("tz_session: Kwork login OK (%s)", email)
            return True
        logger.warning("tz_session: Kwork login failed — check KWORK_TZ_EMAIL/KWORK_TZ_PASSWORD")
        return False
    except Exception as exc:
        logger.warning("tz_session: Kwork login error: %s", exc)
        return False


def _login_kwork_legacy(sess: requests.Session, email: str, password: str) -> bool:
    """Fallback: старый form POST /user/login (если API недоступен)."""
    try:
        page = sess.get(_KWORK_LOGIN_PAGE, timeout=15, allow_redirects=True)
        token = sess.cookies.get("_token", "") or _extract_kwork_legacy_token(page.text or "")
        resp = sess.post(
            _KWORK_LOGIN_LEGACY,
            data={"l": email, "p": password, "rememberMe": "1", "_token": token},
            headers=_xhr_headers(referer=_KWORK_LOGIN_PAGE),
            timeout=15,
        )
        ct = resp.headers.get("content-type", "")
        if ct.startswith("application/json"):
            try:
                body = resp.json()
                if isinstance(body, dict) and (
                    body.get("success") is True or body.get("status") == "success"
                ):
                    _apply_kwork_csrf_from_body(sess, body)
                    return True
            except Exception:
                pass
        return _kwork_session_ready(sess)
    except Exception:
        return False


def get_auth_session(source: str) -> requests.Session | None:
    """Return cached authenticated session; creates/re-creates on cache miss or TTL expiry.

    Returns None when credentials are not configured or login fails.
    """
    key = _source_key(source)
    cached = _sessions.get(key)
    now = time.monotonic()

    if cached is not None:
        sess, login_at = cached
        if (now - login_at) < _session_ttl_sec():
            return sess  # may be None if previous login failed

    sess = _new_session(key)
    if key == "fl":
        ok = _login_fl(sess)
    elif key == "kwork":
        ok = _login_kwork(sess)
    else:
        return None

    result: requests.Session | None = sess if ok else None
    _sessions[key] = (result, now)
    return result


def invalidate_session(source: str) -> None:
    """Drop cached session to force re-login on next call."""
    _sessions.pop(_source_key(source), None)


def enforce_rate_limit(source: str) -> None:
    """Sleep if needed to honour per-source rate limit."""
    key = _source_key(source)
    rate = _rate_limit_sec()
    now = time.monotonic()
    elapsed = now - _last_request_at.get(key, 0.0)
    wait = rate - elapsed
    if wait > 0:
        time.sleep(wait)
    _last_request_at[key] = time.monotonic()


def fetch_detail_html_with_auth(
    page_url: str,
    source: str,
    *,
    timeout_sec: float = 30.0,
) -> str:
    """GET detail page HTML with authenticated session (O133-KW-AUTH-HTML)."""
    url = (page_url or "").strip()
    if not url:
        return ""
    enforce_rate_limit(source)
    sess = get_auth_session(source)
    if sess is None:
        return ""
    try:
        resp = sess.get(url, timeout=timeout_sec, allow_redirects=True)
    except Exception as exc:
        logger.debug("tz_session auth detail fail %s: %s", url[:80], exc)
        return ""
    if resp.status_code != 200:
        return ""
    encoding = resp.encoding or "utf-8"
    return resp.content.decode(encoding, errors="replace")


def download_with_auth_session(
    url: str,
    source: str,
    *,
    timeout_sec: float = 30.0,
) -> tuple[bytes | None, str | None]:
    """Download file with authenticated session.

    Returns (data, error_reason):
      - error_reason = None        → success
      - error_reason = 'no_session' → credentials not configured
      - error_reason = 'auth'      → login OK but server still 401/403
    """
    enforce_rate_limit(source)
    sess = get_auth_session(source)
    if sess is None:
        return None, "no_session"

    def _get(s: requests.Session) -> requests.Response:
        return s.get(url, timeout=timeout_sec, allow_redirects=True)

    try:
        resp = _get(sess)
    except Exception as exc:
        logger.debug("tz_session download fail %s: %s", url[:80], exc)
        return None, None

    if resp.status_code in (401, 403):
        invalidate_session(source)
        sess2 = get_auth_session(source)
        if sess2 is None:
            return None, "auth"
        try:
            resp = _get(sess2)
        except Exception:
            return None, "auth"
        if resp.status_code in (401, 403):
            return None, "auth"

    if resp.status_code != 200:
        return None, None
    data = resp.content or b""
    if data[:15].lstrip().startswith(b"<!DOCTYPE") or data[:5].lstrip().startswith(b"<html"):
        return None, "auth"
    return data, None


def clear_all_sessions() -> None:
    """Reset all cached sessions and rate-limit state (for tests)."""
    _sessions.clear()
    _last_request_at.clear()
