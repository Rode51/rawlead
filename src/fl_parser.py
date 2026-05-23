"""Парсинг листинга проектов FL.ru: 2–3 страницы ленты за цикл."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from config import DIRECT_REQUESTS_PROXIES, Config
from listing import SOURCE_FL, ListingProject

# Сколько страниц ленты запрашивать за один цикл (см. docs/SOURCES.md).
FL_LISTING_MAX_PAGES = 3

_PAGE_PATH_RE = re.compile(r"/page-\d+/?")


class FlListingError(RuntimeError):
    """Не удалось разобрать ленту (пустой ответ, смена вёрстки, блокировка бота)."""


def _fl_listing_page_url(base_url: str, page: int) -> str:
    """Страница 1 — URL из конфига; далее `/projects/.../page-N/` + те же query."""
    if page <= 1:
        return base_url
    parsed = urlparse(base_url)
    path = _PAGE_PATH_RE.sub("", parsed.path or "/")
    path = path.rstrip("/") + f"/page-{page}/"
    return urlunparse(
        (parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment)
    )


def _parse_items(html: str, page_url: str) -> list[ListingProject]:
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".b-page__lenta_item")
    out: list[ListingProject] = []
    seen: set[int] = set()

    for node in items:
        link = node.select_one(".b-post__title a[href*='/projects/']")
        if not link or not link.get("href"):
            continue
        href = str(link["href"]).strip()
        m = re.search(r"/projects/(\d+)/", href)
        if not m:
            continue
        pid = int(m.group(1))
        if pid in seen:
            continue
        seen.add(pid)

        title = link.get_text(strip=True)
        price_el = node.select_one(".b-post__price")
        budget_text = price_el.get_text(strip=True) if price_el else ""

        full_url = urljoin(page_url, href)

        published_at = ""
        for sp in node.select("span.text-gray-opacity-4"):
            t = sp.get_text(strip=True)
            if t:
                published_at = t
                break

        body_el = node.select_one(".b-post__body .b-post__txt") or node.select_one(
            ".b-post__body"
        )
        listing_snippet = body_el.get_text(strip=True) if body_el else ""

        out.append(
            ListingProject(
                project_id=pid,
                title=title,
                budget_text=budget_text,
                url=full_url,
                published_at=published_at,
                listing_snippet=listing_snippet,
                source=SOURCE_FL,
            )
        )

    return out


def _guess_blocked_or_changed(html: str) -> str | None:
    low = html.lower()
    if "cloudflare" in low and "challenge" in low:
        return "challenge (Cloudflare и т.п.)"
    if "проверьте, что вы не робот" in low:
        return "антибот («не робот»)"
    return None


def parse_listing_html(html: str, page_url: str) -> list[ListingProject]:
    """Разбор сохранённого HTML листинга (удобно для отладки и тестов)."""
    if not html or not html.strip():
        raise FlListingError("Пустой HTML листинга.")
    projects = _parse_items(html, page_url)
    if not projects:
        hint = _guess_blocked_or_changed(html)
        extra = f" Дополнительно: похоже на {hint}." if hint else ""
        raise FlListingError(
            "На странице нет карточек `.b-page__lenta_item` — сменилась вёрстка или лента недоступна."
            f"{extra} См. docs/SOURCES.md / docs/STATUS.md (Playwright)."
        )
    return projects


def _fetch_listing_html(url: str, cfg: Config, *, timeout_sec: float) -> str:
    headers = {"User-Agent": cfg.http_user_agent}
    try:
        resp = requests.get(
            url,
            headers=headers,
            timeout=timeout_sec,
            proxies=DIRECT_REQUESTS_PROXIES,
        )
    except requests.RequestException as exc:
        raise FlListingError(f"Сетевой сбой при запросе ленты: {exc}") from exc

    if resp.status_code != 200:
        raise FlListingError(f"HTTP {resp.status_code} для ленты проектов ({url}).")

    encoding = resp.encoding or "utf-8"
    return resp.content.decode(encoding, errors="replace")


def fetch_listing_projects(cfg: Config, *, timeout_sec: float = 30.0) -> list[ListingProject]:
    """GET до `FL_LISTING_MAX_PAGES` страниц `cfg.fl_projects_url`, дедуп id внутри цикла.

    Без прокси: домашний IP, не TG_PROXY_URL и не системные HTTP_PROXY из ОС.
    """
    merged: list[ListingProject] = []
    seen: set[int] = set()

    for page in range(1, FL_LISTING_MAX_PAGES + 1):
        page_url = _fl_listing_page_url(cfg.fl_projects_url, page)
        html = _fetch_listing_html(page_url, cfg, timeout_sec=timeout_sec)
        batch = _parse_items(html, page_url)

        if not batch:
            if page == 1:
                hint = _guess_blocked_or_changed(html)
                extra = f" Дополнительно: похоже на {hint}." if hint else ""
                raise FlListingError(
                    "На странице нет карточек `.b-page__lenta_item` — сменилась вёрстка или лента недоступна."
                    f"{extra} См. docs/SOURCES.md / docs/STATUS.md (Playwright)."
                )
            break

        for project in batch:
            if project.project_id in seen:
                continue
            seen.add(project.project_id)
            merged.append(project)

    return merged


def fetch_project_description(
    project_url: str,
    cfg: Config,
    *,
    fallback_snippet: str = "",
    timeout_sec: float = 30.0,
) -> tuple[str, bool]:
    """
    GET страницы проекта FL → полный текст ТЗ.
    Возвращает (description, detail_ok). При ошибке — fallback_snippet, detail_ok=False.
    """
    url = (project_url or "").strip()
    if not url:
        return fallback_snippet, False

    headers = {"User-Agent": cfg.http_user_agent}
    try:
        resp = requests.get(
            url,
            headers=headers,
            timeout=timeout_sec,
            proxies=DIRECT_REQUESTS_PROXIES,
        )
    except requests.RequestException:
        return fallback_snippet, False

    if resp.status_code != 200:
        return fallback_snippet, False

    encoding = resp.encoding or "utf-8"
    html = resp.content.decode(encoding, errors="replace")
    soup = BeautifulSoup(html, "html.parser")

    desc_el = soup.select_one(".fl-project-content__description-text")
    if desc_el:
        text = desc_el.get_text(" ", strip=True)
        if text:
            return text, True

    blocks: list[str] = []
    for sel in (".fl-project-content .b-layout__txt", ".b-layout__txt"):
        for node in soup.select(sel):
            t = node.get_text(" ", strip=True)
            if len(t) > 40:
                blocks.append(t)
    if blocks:
        return max(blocks, key=len), True

    return fallback_snippet, False
