"""Ротация прокси для fetch FL/Kwork (не TG)."""

from __future__ import annotations

import os
from typing import Any

from config import DIRECT_REQUESTS_PROXIES, normalize_proxy_url

_indexes: dict[str, int] = {}


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


def _pick_url(key: str, urls: list[str]) -> str | None:
    if not urls:
        return None
    idx = _indexes.get(key, 0)
    url = urls[idx % len(urls)]
    _indexes[key] = idx + 1
    return url


def requests_proxies_for(source: str) -> dict[str, str | None]:
    """source: fl | kwork. Пустой env → DIRECT (домашний IP)."""
    if source == "fl":
        urls = _parse_proxy_list("FL_PROXY_URLS", "FL_PROXY_URL")
        key = "fl"
    elif source == "kwork":
        urls = _parse_proxy_list("KWORK_PROXY_URLS", "KWORK_PROXY_URL")
        key = "kwork"
    else:
        return DIRECT_REQUESTS_PROXIES
    url = _pick_url(key, urls)
    if not url:
        return DIRECT_REQUESTS_PROXIES
    return {"http": url, "https": url}


def proxy_log_hint(source: str) -> str:
    """Хост:порт для лога (без пароля)."""
    proxies = requests_proxies_for(source)
    url = proxies.get("https") or proxies.get("http") or ""
    if not url or url == DIRECT_REQUESTS_PROXIES.get("https"):
        return "direct"
    try:
        from urllib.parse import urlparse

        p = urlparse(url)
        return f"{p.hostname}:{p.port or ''}".rstrip(":")
    except Exception:
        return "proxy"
