"""VC.ru: API jobs (канон) + fallback HTML __INITIAL_STATE__."""

from __future__ import annotations

import json
import os
import re
from html import unescape
from typing import Any

import requests

from config import DIRECT_REQUESTS_PROXIES, Config
from listing import SOURCE_VC_RU, ListingProject

_INITIAL_STATE_RE = re.compile(
    r"window\.__INITIAL_STATE__\s*=\s*(\{.+?\})\s*;</script>",
    re.S,
)
_DEFAULT_API_URL = "https://api.vc.ru/v2.8/timeline?subsitesIds=jobs"
_DEFAULT_LISTING_URL = "https://vc.ru/services"
_JOB_TITLE_HINTS = (
    "вакан",
    "ищем",
    "ищу ",
    "требуется",
    "нужен",
    "нужна",
    "hire",
    "hiring",
    "разработчик",
    "дизайнер",
    "монтаж",
    "копирайт",
)


class VcRuListingError(RuntimeError):
    pass


def _api_url() -> str:
    return (os.getenv("VC_RU_API_URL", "") or _DEFAULT_API_URL).strip()


def _listing_url() -> str:
    return (os.getenv("VC_RU_LISTING_URL", "") or _DEFAULT_LISTING_URL).strip()


def _fetch_json(url: str, cfg: Config, *, timeout_sec: float) -> dict[str, Any]:
    headers = {"User-Agent": cfg.http_user_agent, "Accept": "application/json"}
    try:
        resp = requests.get(
            url,
            headers=headers,
            timeout=timeout_sec,
            proxies=DIRECT_REQUESTS_PROXIES,
        )
    except requests.RequestException as exc:
        raise VcRuListingError(f"API сетевой сбой: {exc}") from exc
    if resp.status_code != 200:
        raise VcRuListingError(f"API HTTP {resp.status_code} ({url})")
    try:
        return resp.json()
    except json.JSONDecodeError as exc:
        raise VcRuListingError("API: не JSON.") from exc


def _fetch_html(url: str, cfg: Config, *, timeout_sec: float) -> str:
    headers = {"User-Agent": cfg.http_user_agent}
    try:
        resp = requests.get(
            url,
            headers=headers,
            timeout=timeout_sec,
            proxies=DIRECT_REQUESTS_PROXIES,
        )
    except requests.RequestException as exc:
        raise VcRuListingError(f"HTML сетевой сбой: {exc}") from exc
    if resp.status_code == 404:
        raise VcRuListingError(f"HTML HTTP 404 ({url}) — задайте VC_RU_LISTING_URL.")
    if resp.status_code != 200:
        raise VcRuListingError(f"HTML HTTP {resp.status_code} ({url})")
    enc = resp.encoding or "utf-8"
    return resp.content.decode(enc, errors="replace")


def _entry_snippet(data: dict[str, Any]) -> str:
    blocks = data.get("blocks") or []
    parts: list[str] = []
    for block in blocks[:6]:
        if not isinstance(block, dict):
            continue
        inner = block.get("data")
        if isinstance(inner, dict):
            text = inner.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(unescape(re.sub(r"<[^>]+>", " ", text)).strip())
                continue
        for key in ("text", "title", "data"):
            val = block.get(key)
            if isinstance(val, str) and val.strip():
                parts.append(val.strip())
                break
    og = str(data.get("ogDescription") or "").strip()
    if og:
        parts.append(og)
    return " ".join(parts)[:2000]


def _entry_url(data: dict[str, Any]) -> str:
    url = str(data.get("url") or "").strip()
    if url.startswith("http"):
        return url
    uri = str(data.get("customUri") or "").strip()
    if uri:
        return f"https://vc.ru/{uri.lstrip('/')}"
    raw_id = data.get("id")
    if raw_id is not None:
        return f"https://vc.ru/{raw_id}"
    return _listing_url()


def _looks_like_job(title: str) -> bool:
    low = (title or "").lower()
    return any(h in low for h in _JOB_TITLE_HINTS)


def _projects_from_api_items(items: list[dict[str, Any]]) -> list[ListingProject]:
    out: list[ListingProject] = []
    seen: set[int] = set()
    for item in items:
        data = item.get("data") if isinstance(item.get("data"), dict) else item
        if not isinstance(data, dict):
            continue
        raw_id = data.get("id")
        if raw_id is None:
            continue
        try:
            eid = int(raw_id)
        except (TypeError, ValueError):
            continue
        if eid in seen:
            continue
        title = str(data.get("title") or "").strip()
        if not title:
            continue
        seen.add(eid)
        snippet = _entry_snippet(data) or title
        out.append(
            ListingProject(
                project_id=eid,
                title=title,
                budget_text="",
                url=_entry_url(data),
                published_at="",
                listing_snippet=snippet,
                source=SOURCE_VC_RU,
            )
        )
    if not out:
        raise VcRuListingError(f"API {_api_url()}: пустой список постов.")
    return out


def fetch_from_api(cfg: Config, *, timeout_sec: float = 30.0) -> list[ListingProject]:
    url = _api_url()
    payload = _fetch_json(url, cfg, timeout_sec=timeout_sec)
    result = payload.get("result")
    if not isinstance(result, dict):
        raise VcRuListingError(f"API: нет result ({url}).")
    items = result.get("items")
    if not isinstance(items, list):
        raise VcRuListingError(f"API: нет items ({url}).")
    return _projects_from_api_items([it for it in items if isinstance(it, dict)])


def _items_from_state(state: dict[str, Any]) -> list[dict[str, Any]]:
    for key, val in state.items():
        if not key.startswith("feed@") or not isinstance(val, dict):
            continue
        items = val.get("items")
        if isinstance(items, list) and items:
            return [it for it in items if isinstance(it, dict)]
    return []


def parse_listing_html(html: str, page_url: str) -> list[ListingProject]:
    m = _INITIAL_STATE_RE.search(html)
    if not m:
        raise VcRuListingError("Нет window.__INITIAL_STATE__ — SPA без данных.")
    try:
        state = json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        raise VcRuListingError("Не разобрали __INITIAL_STATE__.") from exc

    out: list[ListingProject] = []
    seen: set[int] = set()
    for item in _items_from_state(state):
        data = item.get("data")
        if not isinstance(data, dict):
            continue
        raw_id = data.get("id")
        if raw_id is None:
            continue
        try:
            eid = int(raw_id)
        except (TypeError, ValueError):
            continue
        if eid in seen:
            continue
        title = str(data.get("title") or "").strip()
        if not title or not _looks_like_job(title):
            continue
        seen.add(eid)
        url = _entry_url(data)
        snippet = _entry_snippet(data)
        out.append(
            ListingProject(
                project_id=eid,
                title=title,
                budget_text="",
                url=url,
                published_at="",
                listing_snippet=snippet or title,
                source=SOURCE_VC_RU,
            )
        )

    if not out:
        raise VcRuListingError(
            f"HTML ({page_url}): нет постов с признаками вакансии. "
            "Задайте VC_RU_API_URL или ослабьте фильтр."
        )
    return out


def fetch_listing_projects(cfg: Config, *, timeout_sec: float = 30.0) -> list[ListingProject]:
    api_err = ""
    try:
        return fetch_from_api(cfg, timeout_sec=timeout_sec)
    except VcRuListingError as exc:
        api_err = str(exc)

    page_url = _listing_url()
    try:
        html = _fetch_html(page_url, cfg, timeout_sec=timeout_sec)
        return parse_listing_html(html, page_url)
    except VcRuListingError as exc:
        hint = f"fallback HTML {page_url}"
        if api_err:
            raise VcRuListingError(f"API ({_api_url()}): {api_err}; {hint}: {exc}") from exc
        raise
