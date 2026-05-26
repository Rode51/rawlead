"""Freelancehunt: API v2 (канон) → HTML requests → Playwright fallback."""

from __future__ import annotations

import os
import re
from typing import Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import DIRECT_REQUESTS_PROXIES, Config
from html_fetch import HtmlFetchError, fetch_html_playwright
from listing import SOURCE_FREELANCEHUNT, ListingProject

_FREELANCEHUNT_PAGE_URL = "https://freelancehunt.com/projects"
_DEFAULT_API_URL = "https://api.freelancehunt.com/v2/projects"
_PROJECT_HREF_RE = re.compile(r"/project/([^/\"'?#]+)")


class FreelancehuntListingError(RuntimeError):
    pass


def _api_url() -> str:
    return (os.getenv("FREELANCEHUNT_API_URL", "") or _DEFAULT_API_URL).strip()


def _api_token() -> str:
    return os.getenv("FREELANCEHUNT_API_TOKEN", "").strip()


def _proxy_url() -> str:
    return os.getenv("FREELANCEHUNT_PROXY_URL", "").strip()


def _requests_proxies() -> dict[str, str] | dict[str, None]:
    raw = _proxy_url()
    if not raw:
        return DIRECT_REQUESTS_PROXIES
    from config import normalize_proxy_url

    url = normalize_proxy_url(raw)
    return {"http": url, "https": url}


def _browser_headers(cfg: Config) -> dict[str, str]:
    return {
        "User-Agent": cfg.http_user_agent,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Referer": "https://freelancehunt.com/",
    }


def _project_attrs(row: dict[str, Any]) -> dict[str, Any]:
    attrs = row.get("attributes")
    if isinstance(attrs, dict):
        merged = dict(attrs)
        if "id" not in merged and row.get("id") is not None:
            merged["id"] = row["id"]
        return merged
    return row


def _budget_text(attrs: dict[str, Any]) -> str:
    for key in ("budget", "budget_text", "amount"):
        val = attrs.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
        if isinstance(val, (int, float)):
            cur = str(attrs.get("currency") or attrs.get("budget_currency") or "").strip()
            return f"{int(val)} {cur}".strip()
    amount = attrs.get("budget_amount")
    if amount is not None:
        cur = str(attrs.get("budget_currency") or attrs.get("currency") or "").strip()
        return f"{amount} {cur}".strip()
    return ""


def _project_url(attrs: dict[str, Any], slug: str, pid: int) -> str:
    for key in ("url", "link", "public_url"):
        val = attrs.get(key)
        if isinstance(val, str) and val.startswith("http"):
            return val
    if slug:
        return f"https://freelancehunt.com/project/{slug}"
    return f"https://freelancehunt.com/project/{pid}"


def parse_api_payload(payload: dict[str, Any]) -> list[ListingProject]:
    rows = payload.get("data")
    if not isinstance(rows, list):
        raise FreelancehuntListingError("API: нет поля data[].")
    out: list[ListingProject] = []
    seen: set[int] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        attrs = _project_attrs(row)
        raw_id = attrs.get("id") or row.get("id")
        try:
            pid = int(raw_id)
        except (TypeError, ValueError):
            slug = str(attrs.get("slug") or attrs.get("seo_url") or "").strip()
            if not slug:
                continue
            pid = abs(hash(slug)) % (10**9)
        if pid in seen:
            continue
        seen.add(pid)
        title = str(
            attrs.get("name") or attrs.get("title") or attrs.get("subject") or ""
        ).strip()
        if not title:
            continue
        slug = str(attrs.get("slug") or attrs.get("seo_url") or "").strip()
        desc = str(attrs.get("description") or attrs.get("body") or "").strip()
        out.append(
            ListingProject(
                project_id=pid,
                title=title,
                budget_text=_budget_text(attrs),
                url=_project_url(attrs, slug, pid),
                published_at=str(attrs.get("published_at") or attrs.get("created_at") or ""),
                listing_snippet=(desc or title)[:2000],
                source=SOURCE_FREELANCEHUNT,
            )
        )
    if not out:
        raise FreelancehuntListingError("API: пустой список проектов.")
    return out


def fetch_from_api(cfg: Config, *, timeout_sec: float = 30.0) -> list[ListingProject]:
    token = _api_token()
    if not token:
        raise FreelancehuntListingError(
            "FREELANCEHUNT_API_TOKEN не задан (https://freelancehunt.com/my/api)."
        )
    url = _api_url()
    headers = {
        "User-Agent": cfg.http_user_agent,
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    try:
        resp = requests.get(
            url,
            headers=headers,
            timeout=timeout_sec,
            proxies=_requests_proxies(),
        )
    except requests.RequestException as exc:
        raise FreelancehuntListingError(f"API сетевой сбой: {exc}") from exc
    if resp.status_code == 401:
        raise FreelancehuntListingError("API HTTP 401 — неверный FREELANCEHUNT_API_TOKEN.")
    if resp.status_code != 200:
        raise FreelancehuntListingError(f"API HTTP {resp.status_code} ({url})")
    try:
        payload = resp.json()
    except ValueError as exc:
        raise FreelancehuntListingError("API: не JSON.") from exc
    if not isinstance(payload, dict):
        raise FreelancehuntListingError("API: ожидался объект JSON.")
    return parse_api_payload(payload)


def _fetch_html_requests(url: str, cfg: Config, *, timeout_sec: float) -> str:
    try:
        resp = requests.get(
            url,
            headers=_browser_headers(cfg),
            timeout=timeout_sec,
            proxies=_requests_proxies(),
        )
    except requests.RequestException as exc:
        raise FreelancehuntListingError(f"HTML сетевой сбой: {exc}") from exc
    if resp.status_code == 403:
        raise FreelancehuntListingError("HTML HTTP 403 — антибот.")
    if resp.status_code != 200:
        raise FreelancehuntListingError(f"HTML HTTP {resp.status_code} ({url})")
    enc = resp.encoding or "utf-8"
    return resp.content.decode(enc, errors="replace")


def _fetch_html(url: str, cfg: Config, *, timeout_sec: float) -> str:
    try:
        return _fetch_html_requests(url, cfg, timeout_sec=timeout_sec)
    except FreelancehuntListingError as exc:
        if "403" not in str(exc):
            raise
    try:
        return fetch_html_playwright(
            url,
            user_agent=cfg.http_user_agent,
            timeout_sec=timeout_sec,
            proxy_url=_proxy_url(),
        )
    except HtmlFetchError as pw_exc:
        raise FreelancehuntListingError(str(pw_exc)) from pw_exc


def parse_listing_html(html: str, page_url: str) -> list[ListingProject]:
    if not html.strip():
        raise FreelancehuntListingError("Пустой HTML.")
    soup = BeautifulSoup(html, "html.parser")
    out: list[ListingProject] = []
    seen: set[str] = set()

    for link in soup.select("a[href*='/project/']"):
        href = str(link.get("href") or "").strip()
        m = _PROJECT_HREF_RE.search(href)
        if not m:
            continue
        slug = m.group(1)
        if slug in seen:
            continue
        seen.add(slug)
        title = link.get_text(strip=True)
        if not title or len(title) < 3:
            continue
        full_url = urljoin(page_url, href)
        pid = abs(hash(slug)) % (10**9)
        out.append(
            ListingProject(
                project_id=pid,
                title=title,
                budget_text="",
                url=full_url,
                published_at="",
                listing_snippet=title,
                source=SOURCE_FREELANCEHUNT,
            )
        )

    if not out:
        raise FreelancehuntListingError(
            "Нет ссылок `/project/` — сменилась вёрстка или Cloudflare."
        )
    return out


def fetch_listing_projects(cfg: Config, *, timeout_sec: float = 30.0) -> list[ListingProject]:
    if _api_token():
        try:
            return fetch_from_api(cfg, timeout_sec=timeout_sec)
        except FreelancehuntListingError:
            pass

    html = _fetch_html(_FREELANCEHUNT_PAGE_URL, cfg, timeout_sec=timeout_sec)
    return parse_listing_html(html, _FREELANCEHUNT_PAGE_URL)
