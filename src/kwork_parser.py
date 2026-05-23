"""Парсинг листинга Kwork: один GET на URL ленты, JSON «wants» в HTML страницы."""

from __future__ import annotations

import json
from urllib.parse import urlparse

import requests

from config import DIRECT_REQUESTS_PROXIES, Config
from listing import SOURCE_KWORK, ListingProject


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

        out.append(
            ListingProject(
                project_id=pid,
                title=title,
                budget_text=budget_text,
                url=_project_url(page_url, pid),
                published_at=_published_at(want),
                listing_snippet=description,
                source=SOURCE_KWORK,
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


def fetch_listing_projects(cfg: Config, *, timeout_sec: float = 30.0) -> list[ListingProject]:
    """GET `cfg.kwork_projects_url`, первая страница (без пагинации в MVP)."""
    url = cfg.kwork_projects_url
    headers = {"User-Agent": cfg.http_user_agent}
    try:
        resp = requests.get(
            url,
            headers=headers,
            timeout=timeout_sec,
            proxies=DIRECT_REQUESTS_PROXIES,
        )
    except requests.RequestException as exc:
        raise KworkListingError(f"Сетевой сбой при запросе ленты: {exc}") from exc

    if resp.status_code != 200:
        raise KworkListingError(f"HTTP {resp.status_code} для ленты Kwork.")

    encoding = resp.encoding or "utf-8"
    html = resp.content.decode(encoding, errors="replace")

    try:
        return parse_listing_html(html, url)
    except KworkListingError:
        hint = _guess_blocked_or_changed(html)
        if hint:
            raise KworkListingError(
                f"Не удалось разобрать ленту Kwork; похоже на {hint}."
            ) from None
        raise
