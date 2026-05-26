"""Парсинг freelance.habr.com/tasks (P1.3). Сайт может отдавать 410."""

from __future__ import annotations

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import DIRECT_REQUESTS_PROXIES, Config
from listing import SOURCE_HABR_FREELANCE, ListingProject

_HABR_FREELANCE_URL = "https://freelance.habr.com/tasks"
_TASK_ID_RE = re.compile(r"/tasks/(\d+)")


class HabrFreelanceListingError(RuntimeError):
    pass


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
        raise HabrFreelanceListingError(f"Сетевой сбой: {exc}") from exc
    if resp.status_code == 410:
        raise HabrFreelanceListingError(
            "HTTP 410 — Habr Freelance закрыт; обновите URL в PUBLIC_FEED_WEB_SOURCES."
        )
    if resp.status_code != 200:
        raise HabrFreelanceListingError(f"HTTP {resp.status_code} ({url})")
    enc = resp.encoding or "utf-8"
    return resp.content.decode(enc, errors="replace")


def parse_listing_html(html: str, page_url: str) -> list[ListingProject]:
    if not html.strip():
        raise HabrFreelanceListingError("Пустой HTML.")
    soup = BeautifulSoup(html, "html.parser")
    out: list[ListingProject] = []
    seen: set[int] = set()
    for link in soup.select("a[href*='/tasks/']"):
        href = str(link.get("href") or "")
        m = _TASK_ID_RE.search(href)
        if not m:
            continue
        tid = int(m.group(1))
        if tid in seen:
            continue
        seen.add(tid)
        title = link.get_text(strip=True) or "Задача"
        full_url = urljoin(page_url, href)
        out.append(
            ListingProject(
                project_id=tid,
                title=title,
                budget_text="",
                url=full_url,
                published_at="",
                listing_snippet=title,
                source=SOURCE_HABR_FREELANCE,
            )
        )
    if not out:
        raise HabrFreelanceListingError(
            "Нет ссылок `/tasks/` — сменилась вёрстка или лента пуста."
        )
    return out


def fetch_listing_projects(cfg: Config, *, timeout_sec: float = 30.0) -> list[ListingProject]:
    html = _fetch_html(_HABR_FREELANCE_URL, cfg, timeout_sec=timeout_sec)
    return parse_listing_html(html, _HABR_FREELANCE_URL)
