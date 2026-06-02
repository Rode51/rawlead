"""Ротация прокси для fetch FL/Kwork (не TG)."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

from config import DIRECT_REQUESTS_PROXIES, normalize_proxy_url

logger = logging.getLogger(__name__)

_indexes: dict[str, int] = {}
_sessions: dict[str, "ExchangeFetchSession"] = {}
_dead_until: dict[str, float] = {}

_FAILOVER_HTTP = frozenset({403, 429})
_DEAD_TTL_SEC = 600.0


def _parse_proxy_list(env_plural: str, env_single: str) -> list[str]:
    raw = os.getenv(env_plural, "").strip()
    parts = [p.strip() for p in raw.split(",") if p.strip()] if raw else []
    if not parts:
        one = os.getenv(env_single, "").strip()
        if one:
            parts = [one]
    out: list[str] = []
    for p in parts:
        try:
            out.append(normalize_proxy_url(p))
        except ValueError:
            continue
    return out


def _shared_exchange_pool() -> list[str]:
    """Общий pool FL/Kwork — fallback для новых бирж O63."""
    return _parse_proxy_list("FL_PROXY_URLS", "FL_PROXY_URL")


def _urls_for_source(source: str) -> tuple[str, list[str]]:
    if source == "fl":
        return "fl", _parse_proxy_list("FL_PROXY_URLS", "FL_PROXY_URL")
    if source == "kwork":
        return "kwork", _parse_proxy_list("KWORK_PROXY_URLS", "KWORK_PROXY_URL")
    if source == "youdo":
        urls = _parse_proxy_list("YOUDO_PROXY_URLS", "YOUDO_PROXY_URL")
        return "youdo", urls or _shared_exchange_pool()
    if source == "freelance_ru":
        urls = _parse_proxy_list("FREELANCE_RU_PROXY_URLS", "FREELANCE_RU_PROXY_URL")
        return "freelance_ru", urls or _shared_exchange_pool()
    if source == "freelancejob":
        urls = _parse_proxy_list("FREELANCEJOB_PROXY_URLS", "FREELANCEJOB_PROXY_URL")
        return "freelancejob", urls or _shared_exchange_pool()
    if source == "pchyol":
        urls = _parse_proxy_list("PCHYOL_PROXY_URLS", "PCHYOL_PROXY_URL")
        return "pchyol", urls or _shared_exchange_pool()
    return source, []


def _hint_from_url(url: str | None) -> str:
    if not url:
        return "direct"
    try:
        p = urlparse(url)
        return f"{p.hostname}:{p.port or ''}".rstrip(":")
    except Exception:
        return "proxy"


def _proxies_dict(url: str | None) -> dict[str, str | None]:
    if not url:
        return DIRECT_REQUESTS_PROXIES
    return {"http": url, "https": url}


def _is_alive_proxy(url: str) -> bool:
    return time.time() >= _dead_until.get(url, 0.0)


def _mark_proxy_dead(url: str) -> None:
    if not url:
        return
    _dead_until[url] = time.time() + _DEAD_TTL_SEC


def exchange_pool_health(source: str) -> tuple[int, int]:
    _key, urls = _urls_for_source(source)
    if not urls:
        return (0, 0)
    alive = sum(1 for u in urls if _is_alive_proxy(u))
    return (alive, len(urls))


@dataclass
class ExchangeFetchSession:
    source: str
    urls: list[str]
    start_idx: int = 0
    try_offset: int = 0

    @property
    def current_url(self) -> str | None:
        urls = [u for u in self.urls if _is_alive_proxy(u)]
        if not urls:
            urls = self.urls
        if not urls:
            return None
        return urls[(self.start_idx + self.try_offset) % len(urls)]

    def current_proxies(self) -> dict[str, str | None]:
        return _proxies_dict(self.current_url)

    def log_hint(self) -> str:
        return _hint_from_url(self.current_url)

    def advance_failover(self) -> bool:
        urls = [u for u in self.urls if _is_alive_proxy(u)]
        if not urls:
            urls = self.urls
        if not urls:
            return False
        self.try_offset += 1
        return self.try_offset < len(urls)


def exchange_fetch_begin(source: str) -> ExchangeFetchSession:
    """Round-robin pick one proxy for the whole listing fetch."""
    key, urls = _urls_for_source(source)
    start = 0
    alive_urls = [u for u in urls if _is_alive_proxy(u)] or urls
    if alive_urls:
        start = _indexes.get(key, 0) % len(alive_urls)
        _indexes[key] = start + 1
    session = ExchangeFetchSession(source=source, urls=alive_urls, start_idx=start)
    alive, total = exchange_pool_health(source)
    logger.info("fetch:%s proxy_pool alive=%s/%s", source, alive, total)
    _sessions[source] = session
    return session


def exchange_fetch_end(source: str) -> None:
    _sessions.pop(source, None)


def _active_session(source: str) -> ExchangeFetchSession | None:
    return _sessions.get(source)


def _pick_url(key: str, urls: list[str]) -> str | None:
    if not urls:
        return None
    idx = _indexes.get(key, 0)
    url = urls[idx % len(urls)]
    _indexes[key] = idx + 1
    return url


def exchange_primary_proxy_url(source: str) -> str:
    """Первый URL из pool источника (для Playwright)."""
    _key, urls = _urls_for_source(source)
    if not urls:
        return ""
    idx = _indexes.get(_key, 0) % len(urls)
    return urls[idx]


def requests_proxies_for(source: str) -> dict[str, str | None]:
    """source: fl | kwork | youdo | freelance_ru. Пустой env → DIRECT (домашний IP)."""
    session = _active_session(source)
    if session:
        return session.current_proxies()
    key, urls = _urls_for_source(source)
    if not urls:
        return DIRECT_REQUESTS_PROXIES
    return _proxies_dict(_pick_url(key, urls))


def proxy_log_hint(source: str) -> str:
    """Хост:порт для лога (без пароля)."""
    session = _active_session(source)
    if session:
        alive, total = exchange_pool_health(source)
        return f"{session.log_hint()} alive={alive}/{total}"
    proxies = requests_proxies_for(source)
    url = proxies.get("https") or proxies.get("http") or ""
    if not url or url == DIRECT_REQUESTS_PROXIES.get("https"):
        return "direct"
    alive, total = exchange_pool_health(source)
    return f"{_hint_from_url(url)} alive={alive}/{total}"


def exchange_get(
    source: str,
    url: str,
    *,
    headers: dict[str, str],
    timeout_sec: float,
) -> requests.Response:
    """GET через пул прокси; 403/429/timeout → следующий URL до исчерпания."""
    session = _active_session(source)
    own_session = session is None
    if own_session:
        session = exchange_fetch_begin(source)
    assert session is not None
    try:
        while True:
            try:
                resp = requests.get(
                    url,
                    headers=headers,
                    timeout=timeout_sec,
                    proxies=session.current_proxies(),
                )
            except requests.RequestException as exc:
                _mark_proxy_dead(session.current_url or "")
                if session.advance_failover():
                    logger.warning(
                        "fetch:%s proxy=%s failover after timeout: %s",
                        source,
                        session.log_hint(),
                        exc,
                    )
                    continue
                raise
            if resp.status_code in _FAILOVER_HTTP and session.advance_failover():
                _mark_proxy_dead(session.current_url or "")
                logger.warning(
                    "fetch:%s proxy=%s failover after HTTP %s",
                    source,
                    session.log_hint(),
                    resp.status_code,
                )
                continue
            return resp
    finally:
        if own_session:
            exchange_fetch_end(source)
