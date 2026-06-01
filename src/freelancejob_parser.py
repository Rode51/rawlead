"""Парсинг листинга FreelanceJob.ru: HTML `/projects/` (карточки `/vacancy/{id}/`)."""

from __future__ import annotations

import logging
import os
import re
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from config import Config
from exchange_proxy import exchange_fetch_begin, exchange_fetch_end, exchange_get, proxy_log_hint
from listing import SOURCE_FREELANCEJOB, ListingProject
from radar_cycle_log import log_pipeline_line

logger = logging.getLogger(__name__)

_DEFAULT_LISTING_URL = "https://www.freelancejob.ru/projects/"
_VACANCY_ID_RE = re.compile(r"^/vacancy/(\d+)/?$")
_PAGE_PATH_RE = re.compile(r"/page-\d+/?")


class FreelancejobListingError(RuntimeError):
    """Не удалось разобрать ленту FreelanceJob.ru."""


def _listing_url() -> str:
    return (os.getenv("FREELANCEJOB_LISTING_URL", "") or _DEFAULT_LISTING_URL).strip()


def _listing_max_pages() -> int:
    raw = os.getenv("FREELANCEJOB_LISTING_MAX_PAGES", "1").strip()
    try:
        n = int(raw)
    except ValueError:
        n = 1
    return max(1, min(3, n))


def _listing_page_url(base_url: str, page: int) -> str:
    if page <= 1:
        return base_url
    parsed = urlparse(base_url)
    path = _PAGE_PATH_RE.sub("", parsed.path or "/")
    path = path.rstrip("/") + f"/page-{page}/"
    return urlunparse(
        (parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment)
    )


def _vacancy_id_from_href(href: str) -> int | None:
    m = _VACANCY_ID_RE.match((href or "").strip())
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def parse_listing_html(html: str, page_url: str) -> list[ListingProject]:
    """Разбор сохранённого HTML листинга (отладка / тесты)."""
    if not html or not html.strip():
        raise FreelancejobListingError("Пустой HTML листинга FreelanceJob.ru.")
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.x17")
    if not cards:
        raise FreelancejobListingError(
            "На странице нет карточек `div.x17` — сменилась вёрстка или лента недоступна."
        )

    out: list[ListingProject] = []
    seen: set[int] = set()
    for card in cards:
        title_a = card.select_one("a.big[href]")
        if not title_a or not title_a.get("href"):
            continue
        href = str(title_a["href"]).strip()
        pid = _vacancy_id_from_href(href)
        if pid is None or pid in seen:
            continue
        seen.add(pid)

        title = title_a.get_text(strip=True)
        if not title:
            continue

        desc_divs = [
            d
            for d in card.find_all("div", recursive=False)
            if d != title_a.parent and not d.get("class")
        ]
        listing_snippet = ""
        if desc_divs:
            listing_snippet = desc_divs[0].get_text(" ", strip=True)

        budget_el = card.select_one("div.x18")
        budget_text = budget_el.get_text(" ", strip=True) if budget_el else ""

        published_at = ""
        date_el = card.select_one("div.x20")
        if date_el:
            raw = date_el.get_text(" ", strip=True)
            if "Проект добавлен:" in raw:
                published_at = raw.split("Проект добавлен:", 1)[-1].strip().split("—")[0].strip()
            else:
                published_at = raw[:80]

        full_url = urljoin(page_url, href)
        out.append(
            ListingProject(
                project_id=pid,
                title=title,
                budget_text=budget_text,
                url=full_url,
                published_at=published_at,
                listing_snippet=listing_snippet or title,
                source=SOURCE_FREELANCEJOB,
            )
        )

    if not out:
        raise FreelancejobListingError("Карточки `div.x17` без id — сменилась вёрстка.")
    return out


def _fetch_listing_html(
    url: str,
    cfg: Config,
    *,
    timeout_sec: float,
    page: int,
) -> str | None:
    headers = {
        "User-Agent": cfg.http_user_agent,
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
    }
    hint = proxy_log_hint("freelancejob")
    try:
        resp = exchange_get("freelancejob", url, headers=headers, timeout_sec=timeout_sec)
    except requests.RequestException as exc:
        msg = f"Сетевой сбой при запросе ленты (стр. {page}, {hint}): {exc}"
        if page <= 1:
            raise FreelancejobListingError(msg) from exc
        logger.warning("freelancejob_listing: %s — partial listing", msg)
        return None

    if resp.status_code != 200:
        msg = f"HTTP {resp.status_code} для ленты ({url}, {hint})"
        if page <= 1:
            raise FreelancejobListingError(msg)
        logger.warning("freelancejob_listing: %s — stop pagination", msg)
        return None

    encoding = resp.encoding or "utf-8"
    return resp.content.decode(encoding, errors="replace")


def fetch_listing_projects(
    cfg: Config, *, timeout_sec: float = 30.0
) -> list[ListingProject]:
    """GET листинга FreelanceJob (до FREELANCEJOB_LISTING_MAX_PAGES страниц)."""
    base_url = _listing_url()
    merged: list[ListingProject] = []
    seen: set[int] = set()
    max_pages = _listing_max_pages()

    exchange_fetch_begin("freelancejob")
    log_pipeline_line(
        cfg.radar_log_path, f"fetch:freelancejob proxy={proxy_log_hint('freelancejob')}"
    )
    try:
        for page in range(1, max_pages + 1):
            page_url = _listing_page_url(base_url, page)
            html = _fetch_listing_html(page_url, cfg, timeout_sec=timeout_sec, page=page)
            if html is None:
                break
            batch = parse_listing_html(html, page_url)
            if not batch and page == 1:
                raise FreelancejobListingError(
                    "Пустой разбор первой страницы FreelanceJob.ru."
                )
            if not batch:
                break
            for project in batch:
                if project.project_id in seen:
                    continue
                seen.add(project.project_id)
                merged.append(project)
        return merged
    finally:
        exchange_fetch_end("freelancejob")
