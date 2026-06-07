"""Парсинг листинга Kwork: один GET на URL ленты, JSON «wants» в HTML страницы."""

from __future__ import annotations

import json
import logging
import os
import re
from urllib.parse import urlparse

import requests

from config import Config
from exchange_browser_fetch import (
    fetch_listing_html_browser_wall_clock,
    listing_browser_enabled,
)
from exchange_proxy import exchange_fetch_begin, exchange_fetch_end, exchange_get, proxy_log_hint
from html_fetch import HtmlFetchError
from lead_category import category_from_kwork_listing_url, category_from_kwork_want
from listing import SOURCE_KWORK, ListingProject
from radar_cycle_log import log_pipeline_line

logger = logging.getLogger(__name__)


class KworkListingError(RuntimeError):
    """Не удалось разобрать ленту Kwork."""


_WANTS_MARKER = '"wants":['


def _extract_wants_array(html: str) -> list[dict]:
    idx = html.find(_WANTS_MARKER)
    if idx < 0:
        raise KworkListingError(
            'В HTML нет встроенного массива "wants" — сменилась вёрстка или страница недоступна.'
        )
    start = html.index("[", idx)
    depth = 0
    for i in range(start, len(html)):
        ch = html[i]
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                try:
                    data = json.loads(html[start : i + 1])
                except json.JSONDecodeError as exc:
                    raise KworkListingError(
                        "Не удалось разобрать JSON wants из страницы."
                    ) from exc
                if not isinstance(data, list):
                    raise KworkListingError("wants в HTML не является массивом.")
                return data
    raise KworkListingError("Обрезанный JSON wants в HTML.")


def _format_budget(price_limit: object, *, is_higher: bool) -> str:
    if price_limit is None or price_limit == "":
        return ""
    try:
        amount = int(float(str(price_limit).replace(" ", "").replace(",", ".")))
    except (TypeError, ValueError):
        return str(price_limit).strip()
    prefix = "до " if is_higher else ""
    return f"{prefix}{amount:,}".replace(",", " ") + " ₽"


def _published_at(want: dict) -> str:
    raw = want.get("date_create")
    if raw:
        return str(raw).strip()
    dates = want.get("wantDates")
    if isinstance(dates, dict):
        for key in ("dateCreate", "dateActive"):
            val = dates.get(key)
            if val:
                return str(val).strip()
    return ""


def _project_url(page_url: str, project_id: int) -> str:
    """Карточка заказа: /projects/{id}/view (не urljoin с ?c=all — давал kwork.ru/{id}/view)."""
    parsed = urlparse(page_url)
    host = parsed.netloc or "kwork.ru"
    scheme = parsed.scheme or "https"
    return f"{scheme}://{host}/projects/{project_id}/view"


def parse_listing_html(html: str, page_url: str) -> list[ListingProject]:
    """Разбор сохранённого HTML (отладка / тесты)."""
    if not html or not html.strip():
        raise KworkListingError("Пустой HTML листинга Kwork.")
    wants = _extract_wants_array(html)
    if not wants:
        raise KworkListingError("Массив wants пуст — лента без заказов или сменилась вёрстка.")
    return _wants_to_projects(wants, page_url)


def _wants_to_projects(wants: list[dict], page_url: str) -> list[ListingProject]:
    out: list[ListingProject] = []
    seen: set[int] = set()
    for want in wants:
        if not isinstance(want, dict):
            continue
        raw_id = want.get("id")
        if raw_id is None:
            continue
        try:
            pid = int(raw_id)
        except (TypeError, ValueError):
            continue
        if pid in seen:
            continue
        seen.add(pid)

        title = str(want.get("name") or "").strip()
        description = str(want.get("description") or "").strip()
        budget_text = _format_budget(
            want.get("priceLimit"),
            is_higher=bool(want.get("isHigherPrice")),
        )

        listing_cat = category_from_kwork_want(want) or ""
        out.append(
            ListingProject(
                project_id=pid,
                title=title,
                budget_text=budget_text,
                url=_project_url(page_url, pid),
                published_at=_published_at(want),
                listing_snippet=description,
                source=SOURCE_KWORK,
                listing_category=listing_cat,
            )
        )
    if not out:
        raise KworkListingError("В wants нет валидных карточек с id.")
    return out


def _guess_blocked_or_changed(html: str) -> str | None:
    low = html.lower()
    if "cloudflare" in low and "challenge" in low:
        return "challenge (Cloudflare и т.п.)"
    if "проверьте, что вы не робот" in low:
        return "антибот («не робот»)"
    return None


def _kwork_listing_wall_clock_sec() -> float:
    raw = os.getenv("KWORK_LISTING_TIMEOUT_SEC", "120").strip()
    try:
        return max(float(raw), 10.0)
    except ValueError:
        return 120.0


def fetch_listing_projects(cfg: Config, *, timeout_sec: float = 30.0) -> list[ListingProject]:
    """GET `cfg.kwork_projects_url`, первая страница (без пагинации в MVP)."""
    url = cfg.kwork_projects_url
    exchange_fetch_begin("kwork")
    log_pipeline_line(cfg.radar_log_path, f"fetch:kwork proxy={proxy_log_hint('kwork')}")
    try:
        html: str | None = None
        if listing_browser_enabled():
            wall = _kwork_listing_wall_clock_sec()
            try:
                html = fetch_listing_html_browser_wall_clock(
                    "kwork",
                    url,
                    user_agent=cfg.http_user_agent,
                    timeout_sec=min(timeout_sec, wall),
                    wall_clock_sec=wall,
                )
            except HtmlFetchError as exc:
                if "timeout" in str(exc).lower():
                    logger.warning(
                        "kwork_listing: timeout after %ss — httpx fallback",
                        int(wall),
                    )
                else:
                    logger.warning(
                        "kwork_listing: Playwright failed (%s) — httpx fallback",
                        exc,
                    )
        if html is None:
            headers = {"User-Agent": cfg.http_user_agent}
            try:
                resp = exchange_get("kwork", url, headers=headers, timeout_sec=timeout_sec)
            except requests.RequestException as exc:
                raise KworkListingError(f"Сетевой сбой при запросе ленты: {exc}") from exc
            if resp.status_code != 200:
                raise KworkListingError(f"HTTP {resp.status_code} для ленты Kwork.")
            encoding = resp.encoding or "utf-8"
            html = resp.content.decode(encoding, errors="replace")
    finally:
        exchange_fetch_end("kwork")

    try:
        projects = parse_listing_html(html, url)
    except KworkListingError:
        hint = _guess_blocked_or_changed(html)
        if hint:
            raise KworkListingError(
                f"Не удалось разобрать ленту Kwork; похоже на {hint}."
            ) from None
        raise
    feed_cat = category_from_kwork_listing_url(url) or ""
    if not feed_cat:
        return projects
    return [
        ListingProject(
            project_id=p.project_id,
            title=p.title,
            budget_text=p.budget_text,
            url=p.url,
            published_at=p.published_at,
            listing_snippet=p.listing_snippet,
            source=p.source,
            listing_category=p.listing_category or feed_cat,
            chat_invite_url=p.chat_invite_url,
            chat_title=p.chat_title,
        )
        for p in projects
    ]


_KWORK_GONE_MARKERS = (
    "заказ закрыт",
    "проект закрыт",
    "исполнитель выбран",
    "исполнитель уже выбран",
    "страница не найдена",
    "want not found",
    "в архиве",
    "закрыт для откликов",
    "отклики не принимаются",
    "прием откликов закрыт",
    "приём откликов закрыт",
)

_KWORK_PROJECT_ID_RE = re.compile(r"/projects/(\d+)", re.I)


def _kwork_redirected_away(original: str, final: str) -> bool:
    orig = (original or "").strip()
    fin = final.strip() if isinstance(final, str) else ""
    if not orig or not fin or orig.casefold() == fin.casefold():
        return False
    m = _KWORK_PROJECT_ID_RE.search(orig)
    if not m:
        return False
    pid = m.group(1)
    return f"/projects/{pid}" not in fin.casefold()


def _parse_kwork_detail_html(html: str, *, fallback_snippet: str = "") -> str:
    """Текст ТЗ со страницы /projects/{id}/view."""
    import re

    for pat in (
        r'"description"\s*:\s*"((?:\\.|[^"\\])*)"',
        r'"text"\s*:\s*"((?:\\.|[^"\\])*)"',
    ):
        m = re.search(pat, html)
        if m:
            try:
                text = json.loads(f'"{m.group(1)}"')
            except json.JSONDecodeError:
                text = m.group(1).replace("\\n", "\n").replace('\\"', '"')
            text = str(text).strip()
            if len(text) > len((fallback_snippet or "").strip()):
                return text

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for sel in (
        ".want-card__description",
        ".want-description",
        ".wants-card__text",
        ".breakwords",
    ):
        node = soup.select_one(sel)
        if node:
            text = node.get_text(" ", strip=True)
            if len(text) > 40:
                return text
    return fallback_snippet


def fetch_project_page_html(
    project_url: str,
    cfg: Config,
    *,
    timeout_sec: float = 30.0,
) -> tuple[str, bool]:
    url = (project_url or "").strip()
    if not url:
        return "", False
    headers = {"User-Agent": cfg.http_user_agent}
    try:
        resp = exchange_get("kwork", url, headers=headers, timeout_sec=timeout_sec)
    except requests.RequestException:
        return "", False
    if resp.status_code != 200:
        return "", False
    encoding = resp.encoding or "utf-8"
    return resp.content.decode(encoding, errors="replace"), True


def fetch_project_detail(
    project_url: str,
    cfg: Config,
    *,
    fallback_snippet: str = "",
    timeout_sec: float = 30.0,
) -> tuple[str, str, bool]:
    """(description, html, detail_ok)."""
    html, ok = fetch_project_page_html(project_url, cfg, timeout_sec=timeout_sec)
    if not ok:
        return fallback_snippet, "", False
    text = _parse_kwork_detail_html(html, fallback_snippet=fallback_snippet)
    detail_ok = bool(text and text != (fallback_snippet or "").strip())
    return text, html, detail_ok


def check_project_page_gone(
    project_url: str,
    cfg: Config,
    *,
    timeout_sec: float = 20.0,
) -> bool | None:
    """O65: True — заказ снят/404; False — жив; None — не удалось проверить."""
    url = (project_url or "").strip()
    if not url:
        return None
    headers = {"User-Agent": cfg.http_user_agent}
    try:
        resp = exchange_get("kwork", url, headers=headers, timeout_sec=timeout_sec)
    except requests.RequestException:
        return None

    if resp.status_code == 404:
        return True
    if resp.status_code != 200:
        return None

    raw_final = getattr(resp, "url", None)
    final_url = raw_final.strip() if isinstance(raw_final, str) and raw_final.strip() else url
    if _kwork_redirected_away(url, final_url):
        return True

    encoding = resp.encoding or "utf-8"
    html = resp.content.decode(encoding, errors="replace").casefold()
    if any(m in html for m in _KWORK_GONE_MARKERS):
        return True
    if '"want"' in html or "want-description" in html or "wants-page" in html:
        return False
    return None
