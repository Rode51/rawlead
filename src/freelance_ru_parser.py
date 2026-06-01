"""Парсинг листинга Freelance.ru: HTML `/project/search`."""

from __future__ import annotations

import logging
import os
import re
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from config import Config
from exchange_proxy import exchange_fetch_begin, exchange_fetch_end, exchange_get, proxy_log_hint
from listing import SOURCE_FREELANCE_RU, ListingProject
from radar_cycle_log import log_pipeline_line

logger = logging.getLogger(__name__)

_DEFAULT_LISTING_URL = "https://freelance.ru/project/search"
_PROJECT_ID_RE = re.compile(r"-(\d+)\.html(?:\?|$)")
_PAGE_PATH_RE = re.compile(r"/page-\d+/?")


class FreelanceRuListingError(RuntimeError):
    """Не удалось разобрать ленту Freelance.ru."""


def _listing_url() -> str:
    return (os.getenv("FREELANCE_RU_LISTING_URL", "") or _DEFAULT_LISTING_URL).strip()


def _listing_max_pages() -> int:
    raw = os.getenv("FREELANCE_RU_LISTING_MAX_PAGES", "1").strip()
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


def _project_id_from_href(href: str) -> int | None:
    m = _PROJECT_ID_RE.search(href or "")
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def parse_listing_html(html: str, page_url: str) -> list[ListingProject]:
    """Разбор сохранённого HTML листинга (отладка / тесты)."""
    if not html or not html.strip():
        raise FreelanceRuListingError("Пустой HTML листинга Freelance.ru.")
    soup = BeautifulSoup(html, "html.parser")
    nodes = soup.select(".project")
    if not nodes:
        raise FreelanceRuListingError(
            "На странице нет карточек `.project` — сменилась вёрстка или лента недоступна."
        )

    out: list[ListingProject] = []
    seen: set[int] = set()
    for node in nodes:
        title_a = node.select_one("h2.title a[href]")
        if not title_a or not title_a.get("href"):
            continue
        href = str(title_a["href"]).strip()
        pid = _project_id_from_href(href)
        if pid is None or pid in seen:
            continue
        seen.add(pid)

        title = title_a.get_text(strip=True)
        if not title:
            continue

        desc_a = node.select_one("a.description")
        listing_snippet = desc_a.get_text(" ", strip=True) if desc_a else ""

        cost_el = node.select_one(".cost")
        budget_text = cost_el.get_text(strip=True) if cost_el else ""
        if not budget_text:
            side = node.select_one(".col-md-3")
            if side:
                budget_text = side.get_text(" ", strip=True)

        full_url = urljoin(page_url, href)

        published_at = ""
        side_text = node.select_one(".col-md-3")
        if side_text:
            parts = [p.strip() for p in side_text.get_text("|", strip=True).split("|") if p.strip()]
            for part in parts:
                low = part.casefold()
                if "договор" in low or "₽" in part or "руб" in low:
                    continue
                if any(x in low for x in ("назад", "мин", "час", "день", "нед", "мес", "сегодня", "вчера")):
                    published_at = part
                    break

        out.append(
            ListingProject(
                project_id=pid,
                title=title,
                budget_text=budget_text,
                url=full_url,
                published_at=published_at,
                listing_snippet=listing_snippet or title,
                source=SOURCE_FREELANCE_RU,
            )
        )

    if not out:
        raise FreelanceRuListingError("Карточки `.project` без id — сменилась вёрстка.")
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
    hint = proxy_log_hint("freelance_ru")
    try:
        resp = exchange_get("freelance_ru", url, headers=headers, timeout_sec=timeout_sec)
    except requests.RequestException as exc:
        msg = f"Сетевой сбой при запросе ленты (стр. {page}, {hint}): {exc}"
        if page <= 1:
            raise FreelanceRuListingError(msg) from exc
        logger.warning("freelance_ru_listing: %s — partial listing", msg)
        return None

    if resp.status_code != 200:
        msg = f"HTTP {resp.status_code} для ленты ({url}, {hint})"
        if page <= 1:
            raise FreelanceRuListingError(msg)
        logger.warning("freelance_ru_listing: %s — stop pagination", msg)
        return None

    encoding = resp.encoding or "utf-8"
    return resp.content.decode(encoding, errors="replace")


def fetch_listing_projects(
    cfg: Config, *, timeout_sec: float = 30.0
) -> list[ListingProject]:
    """GET листинга Freelance.ru (до FREELANCE_RU_LISTING_MAX_PAGES страниц)."""
    base_url = _listing_url()
    merged: list[ListingProject] = []
    seen: set[int] = set()
    max_pages = _listing_max_pages()

    exchange_fetch_begin("freelance_ru")
    log_pipeline_line(
        cfg.radar_log_path, f"fetch:freelance_ru proxy={proxy_log_hint('freelance_ru')}"
    )
    try:
        for page in range(1, max_pages + 1):
            page_url = _listing_page_url(base_url, page)
            html = _fetch_listing_html(page_url, cfg, timeout_sec=timeout_sec, page=page)
            if html is None:
                break
            batch = parse_listing_html(html, page_url)
            if not batch and page == 1:
                raise FreelanceRuListingError(
                    "Пустой разбор первой страницы Freelance.ru."
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
        exchange_fetch_end("freelance_ru")
