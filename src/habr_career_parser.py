"""Парсинг ленты career.habr.com/vacancies (P1.3)."""

from __future__ import annotations

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import DIRECT_REQUESTS_PROXIES, Config
from listing import SOURCE_HABR_CAREER, ListingProject

_HABR_CAREER_URL = "https://career.habr.com/vacancies"
_VACANCY_ID_RE = re.compile(r"/vacancies/(\d+)")


class HabrCareerListingError(RuntimeError):
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
        raise HabrCareerListingError(f"Сетевой сбой: {exc}") from exc
    if resp.status_code != 200:
        raise HabrCareerListingError(f"HTTP {resp.status_code} ({url})")
    enc = resp.encoding or "utf-8"
    return resp.content.decode(enc, errors="replace")


def parse_listing_html(html: str, page_url: str) -> list[ListingProject]:
    if not html.strip():
        raise HabrCareerListingError("Пустой HTML.")
    soup = BeautifulSoup(html, "html.parser")
    out: list[ListingProject] = []
    seen: set[int] = set()
    for card in soup.select("div.vacancy-card"):
        link = card.select_one("a.vacancy-card__title-link")
        if not link or not link.get("href"):
            continue
        m = _VACANCY_ID_RE.search(str(link["href"]))
        if not m:
            continue
        vid = int(m.group(1))
        if vid in seen:
            continue
        seen.add(vid)
        title = link.get_text(strip=True) or "Вакансия"
        salary_el = card.select_one(".vacancy-card__salary")
        budget_text = salary_el.get_text(" ", strip=True) if salary_el else ""
        time_el = card.select_one("time.basic-date")
        published_at = time_el.get("datetime", "") if time_el else ""
        company_el = card.select_one(".vacancy-card__company a")
        company = company_el.get_text(strip=True) if company_el else ""
        snippet_parts = [p for p in (company, budget_text) if p]
        listing_snippet = " · ".join(snippet_parts)
        full_url = urljoin(page_url, str(link["href"]))
        out.append(
            ListingProject(
                project_id=vid,
                title=title,
                budget_text=budget_text,
                url=full_url,
                published_at=published_at,
                listing_snippet=listing_snippet,
                source=SOURCE_HABR_CAREER,
            )
        )
    if not out:
        raise HabrCareerListingError(
            "Нет карточек `.vacancy-card` — сменилась вёрстка или страница недоступна."
        )
    return out


def fetch_listing_projects(cfg: Config, *, timeout_sec: float = 30.0) -> list[ListingProject]:
    html = _fetch_html(_HABR_CAREER_URL, cfg, timeout_sec=timeout_sec)
    return parse_listing_html(html, _HABR_CAREER_URL)
