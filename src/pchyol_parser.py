"""Парсинг листинга Пчёл.нет: HTML `/jobs/` (карточки `/jobs/{cat}/{slug}-{id}/`)."""

from __future__ import annotations

import logging
import os
import re
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from config import Config
from exchange_proxy import exchange_fetch_begin, exchange_fetch_end, exchange_get, proxy_log_hint
from listing import SOURCE_PCHYOL, ListingProject
from radar_cycle_log import log_pipeline_line

logger = logging.getLogger(__name__)

_DEFAULT_LISTING_URL = "https://pchel.net/jobs/?sort=date_desc"
_JOB_HREF_RE = re.compile(r"^/jobs/[^/]+/[^/]+-(\d+)/?$")
_SKIP_STATUS = frozenset({"закрыт", "в работе"})
_PAGE_PATH_RE = re.compile(r"/jobs/page-\d+/?")


class PchyolListingError(RuntimeError):
    """Не удалось разобрать ленту Пчёл.нет."""


def _listing_url() -> str:
    raw = (os.getenv("PCHYOL_LISTING_URL", "") or _DEFAULT_LISTING_URL).strip()
    parsed = urlparse(raw)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    if "sort" not in qs:
        qs["sort"] = ["date_desc"]
        raw = urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                urlencode([(k, v[0]) for k, v in qs.items()]),
                parsed.fragment,
            )
        )
    return raw


def _listing_max_pages() -> int:
    raw = os.getenv("PCHYOL_LISTING_MAX_PAGES", "1").strip()
    try:
        n = int(raw)
    except ValueError:
        n = 1
    return max(1, min(3, n))


def _listing_page_url(base_url: str, page: int) -> str:
    if page <= 1:
        return base_url
    parsed = urlparse(base_url)
    path = _PAGE_PATH_RE.sub("", parsed.path or "/jobs/")
    if not path.endswith("/"):
        path += "/"
    path = path.rstrip("/") + f"/page-{page}/"
    return urlunparse(
        (parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment)
    )


def _project_id_from_block(block) -> int | None:
    hid = block.select_one('input[name="project_id"]')
    if hid and hid.get("value"):
        try:
            return int(str(hid["value"]).strip())
        except ValueError:
            pass
    title_a = block.select_one("div.project-title a.b-link[href]")
    if not title_a or not title_a.get("href"):
        return None
    m = _JOB_HREF_RE.match(str(title_a["href"]).strip())
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def _block_status(block) -> str:
    date_el = block.select_one("div.project-block-right div.date")
    return date_el.get_text(strip=True) if date_el else ""


def _should_skip_block(block) -> bool:
    status = _block_status(block).casefold()
    return status in _SKIP_STATUS


def parse_listing_html(html: str, page_url: str) -> list[ListingProject]:
    """Разбор сохранённого HTML листинга (отладка / тесты)."""
    if not html or not html.strip():
        raise PchyolListingError("Пустой HTML листинга Пчёл.нет.")
    soup = BeautifulSoup(html, "html.parser")
    blocks = soup.select("div.project-block")
    if not blocks:
        raise PchyolListingError(
            "На странице нет карточек `div.project-block` — сменилась вёрстка."
        )

    out: list[ListingProject] = []
    seen: set[int] = set()
    for block in blocks:
        if _should_skip_block(block):
            continue

        pid = _project_id_from_block(block)
        if pid is None or pid in seen:
            continue

        title_a = block.select_one("div.project-title a.b-link[href]")
        if not title_a or not title_a.get("href"):
            continue
        href = str(title_a["href"]).strip()
        if not _JOB_HREF_RE.match(href):
            continue

        title = title_a.get_text(strip=True)
        if not title:
            continue
        seen.add(pid)

        text_el = block.select_one("div.project-text")
        listing_snippet = text_el.get_text(" ", strip=True) if text_el else ""

        price_el = block.select_one("div.project-block-cont div.price")
        budget_text = price_el.get_text(" ", strip=True) if price_el else ""

        published_at = _block_status(block)
        full_url = urljoin(page_url, href)

        out.append(
            ListingProject(
                project_id=pid,
                title=title,
                budget_text=budget_text,
                url=full_url,
                published_at=published_at,
                listing_snippet=listing_snippet or title,
                source=SOURCE_PCHYOL,
            )
        )

    if not out:
        raise PchyolListingError(
            "Нет открытых карточек на листинге (все «Закрыт»/«В работе» или сменилась вёрстка)."
        )
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
    hint = proxy_log_hint("pchyol")
    try:
        resp = exchange_get("pchyol", url, headers=headers, timeout_sec=timeout_sec)
    except requests.RequestException as exc:
        msg = f"Сетевой сбой при запросе ленты (стр. {page}, {hint}): {exc}"
        if page <= 1:
            raise PchyolListingError(msg) from exc
        logger.warning("pchyol_listing: %s — partial listing", msg)
        return None

    if resp.status_code != 200:
        msg = f"HTTP {resp.status_code} для ленты ({url}, {hint})"
        if page <= 1:
            raise PchyolListingError(msg)
        logger.warning("pchyol_listing: %s — stop pagination", msg)
        return None

    encoding = resp.encoding or "utf-8"
    return resp.content.decode(encoding, errors="replace")


def fetch_listing_projects(
    cfg: Config, *, timeout_sec: float = 45.0
) -> list[ListingProject]:
    """GET листинга Пчёл.нет (до PCHYOL_LISTING_MAX_PAGES; sort «Вначале новые»)."""
    base_url = _listing_url()
    merged: list[ListingProject] = []
    seen: set[int] = set()
    max_pages = _listing_max_pages()

    exchange_fetch_begin("pchyol")
    log_pipeline_line(cfg.radar_log_path, f"fetch:pchyol proxy={proxy_log_hint('pchyol')}")
    try:
        for page in range(1, max_pages + 1):
            page_url = _listing_page_url(base_url, page)
            html = _fetch_listing_html(page_url, cfg, timeout_sec=timeout_sec, page=page)
            if html is None:
                break
            batch = parse_listing_html(html, page_url)
            if not batch and page == 1:
                raise PchyolListingError("Пустой разбор первой страницы Пчёл.нет.")
            if not batch:
                break
            for project in batch:
                if project.project_id in seen:
                    continue
                seen.add(project.project_id)
                merged.append(project)
        return merged
    finally:
        exchange_fetch_end("pchyol")


def pchyol_ingest_floor(storage: object | None) -> int:
    """Минимальный project_id для ingest: max(env, уже виденные в SQLite)."""
    env_raw = os.getenv("PCHYOL_MIN_PROJECT_ID", "").strip()
    env_floor = int(env_raw) if env_raw.isdigit() else 0
    stored_max = 0
    if storage is not None and hasattr(storage, "max_project_id"):
        stored_max = int(storage.max_project_id(SOURCE_PCHYOL))
    return max(env_floor, stored_max)


def filter_new_pchyol_projects(
    projects: list[ListingProject],
    storage: object | None,
) -> list[ListingProject]:
    """Не тащить старые открытые карточки с листинга — только id выше floor."""
    if not projects:
        return projects
    floor = pchyol_ingest_floor(storage)
    listing_max = max(p.project_id for p in projects)
    if floor >= listing_max:
        logger.info(
            "pchyol: floor %d above listing max %d — allow newest on page",
            floor,
            listing_max,
        )
        floor = listing_max - 1
    kept = [p for p in projects if p.project_id > floor]
    skipped = len(projects) - len(kept)
    if skipped:
        logger.info("pchyol: skipped %d at/below floor %d", skipped, floor)
    return kept
