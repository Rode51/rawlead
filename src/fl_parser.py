"""Парсинг листинга проектов FL.ru: 2–3 страницы ленты за цикл."""

from __future__ import annotations

import logging
import os
import re
import time
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from config import Config
from exchange_browser_fetch import (
    fetch_listing_html_browser_slots_wall_clock,
    fl_listing_subprocess_enabled,
    fl_listing_user_agent,
    listing_browser_enabled,
)
from exchange_proxy import exchange_fetch_begin, exchange_fetch_end, exchange_get, proxy_log_hint
from html_fetch import HtmlFetchError
from ingest_published_at import parse_fl_published_at
from lead_category import category_from_fl_listing_url
from listing import SOURCE_FL, ListingProject
from listing_fresh import trim_listing_at_known
from radar_cycle_log import log_pipeline_line, stash_listing_metrics

logger = logging.getLogger(__name__)

_fl_last_listing_html: str = ""

# Сколько страниц ленты запрашивать за один цикл (см. docs/SOURCES.md).
def _fl_listing_max_pages() -> int:
    raw = os.environ.get("FL_LISTING_MAX_PAGES", "1").strip()
    try:
        n = int(raw)
    except ValueError:
        n = 1
    return max(1, min(5, n))

_PAGE_PATH_RE = re.compile(r"/page-\d+/?")


class FlListingError(RuntimeError):
    """Не удалось разобрать ленту (пустой ответ, смена вёрстки, блокировка бота)."""


def _fl_listing_wall_clock_sec() -> float:
    raw = os.getenv("FL_LISTING_TIMEOUT_SEC", "120").strip()
    try:
        return max(float(raw), 10.0)
    except ValueError:
        return 120.0


def _fl_allow_httpx_fallback() -> bool:
    """O210: skip httpx cascade when browser subprocess handles listing."""
    if listing_browser_enabled() and fl_listing_subprocess_enabled():
        return os.getenv("FL_HTTPX_FALLBACK", "0").strip().lower() in (
            "1",
            "true",
            "yes",
        )
    return os.getenv("FL_HTTPX_FALLBACK", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _fl_httpx_auto_fallback_enabled() -> bool:
    """O257: auto httpx fallback when browser/subprocess fails or returns empty.

    Enabled by default regardless of FL_LISTING_SUBPROCESS.
    Disable with FL_HTTPX_AUTO_FALLBACK=0 if httpx is also blocked.
    """
    return os.getenv("FL_HTTPX_AUTO_FALLBACK", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def _fl_httpx_max_bans() -> int:
    raw = os.getenv("FL_HTTPX_MAX_BANS", "4").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 4


def _fl_parsed_zero_streak_threshold() -> int:
    raw = os.getenv("FL_PARSED_ZERO_STREAK", "3").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 3


def _fl_soft_antibot_streak_threshold() -> int:
    raw = os.getenv("FL_SOFT_ANTIBOT_STREAK", "5").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 5


def _fl_count_source_bans() -> int:
    try:
        from exchange_proxy import cascade_status_summary

        summary = cascade_status_summary()
        fl_ps = summary.get("primary") or summary
        return len(fl_ps.get("banned") or [])
    except Exception:
        return 0


def _fl_html_snip_for_log(html: str, *, limit: int = 300) -> str:
    text = (html or "")[:limit]
    return text.replace("\n", "\\n").replace("\r", "\\r").replace("\t", " ")


def _fl_auto_ban_clear_cooldown_sec() -> float:
    raw = os.getenv("FL_AUTO_BAN_CLEAR_COOLDOWN_SEC", "1800").strip()
    try:
        return max(60.0, float(raw))
    except ValueError:
        return 1800.0


def _fl_auto_ban_clear_enabled() -> bool:
    return os.getenv("FL_AUTO_BAN_CLEAR", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _fl_fetch_pool_ok() -> bool:
    hint = proxy_log_hint("fl").lower()
    return "pool_exhausted" not in hint and "alive=0/" not in hint


def _fl_streak_get(storage: object | None) -> int:
    if storage is None:
        return 0
    try:
        return int(getattr(storage, "get_setting")("fl_parsed_zero_streak", "0") or "0")
    except (TypeError, ValueError):
        return 0


def _fl_streak_set(storage: object | None, value: int) -> None:
    if storage is None:
        return
    try:
        storage.set_setting("fl_parsed_zero_streak", str(max(0, value)))
    except Exception:
        pass


def _fl_last_auto_clear_at(storage: object | None) -> float:
    if storage is None:
        return 0.0
    try:
        return float(getattr(storage, "get_setting")("fl_auto_ban_clear_at", "0") or "0")
    except (TypeError, ValueError):
        return 0.0


def _log_fl_parsed_zero_html_snip(cfg: Config) -> None:
    if not listing_browser_enabled():
        return
    snip = _fl_html_snip_for_log(_fl_last_listing_html)
    line = f"fl_listing:html_snip snip={snip}"
    logger.warning(line)
    log_pipeline_line(cfg.radar_log_path, line)


def _maybe_fl_soft_antibot_reset(
    cfg: Config,
    storage: object | None,
    streak: int,
) -> bool:
    """O256/O257: parsed=0 antibot HTML, proxy pool alive, no bans — hard reset.

    O257: set_restart_source=False when subprocess enabled — teardown is inline;
    deferred restart_source_fl flag only causes a no-op context close next cycle
    and prolongs the restart loop.
    """
    if storage is None or streak < _fl_soft_antibot_streak_threshold():
        return False
    if _fl_count_source_bans() > 0:
        return False
    from exchange_browser_fetch import fl_hard_reset

    fl_hard_reset(
        reason=f"soft_antibot streak={streak}",
        storage=storage,
        set_restart_source=not fl_listing_subprocess_enabled(),
    )
    log_pipeline_line(
        cfg.radar_log_path,
        f"fl_listing:soft_antibot_reset streak={streak} bans_cleared=0",
    )
    _fl_streak_set(storage, 0)
    return True


def _maybe_fl_parsed_zero_recovery(
    cfg: Config,
    storage: object | None,
    parsed_cards: int,
) -> None:
    """O233/O256: parsed=0 with alive pool → snip log + ban-clear or soft antibot reset."""
    global _fl_last_listing_html
    if parsed_cards > 0:
        _fl_streak_set(storage, 0)
        return
    if not _fl_fetch_pool_ok():
        return
    streak = _fl_streak_get(storage) + 1
    _fl_streak_set(storage, streak)
    _log_fl_parsed_zero_html_snip(cfg)
    sample = _fl_last_listing_html[:400].replace("\n", " ").replace("\r", " ")
    line = f"fl_listing:empty_html streak={streak}"
    if sample:
        line = f"{line} sample={sample}"
    logger.warning(line)
    log_pipeline_line(cfg.radar_log_path, line)
    if _maybe_fl_soft_antibot_reset(cfg, storage, streak):
        return
    threshold = _fl_parsed_zero_streak_threshold()
    if streak < threshold or not _fl_auto_ban_clear_enabled() or storage is None:
        return
    now = time.time()
    cooldown = _fl_auto_ban_clear_cooldown_sec()
    last = _fl_last_auto_clear_at(storage)
    if now - last < cooldown:
        logger.info(
            "fl_listing:auto_ban_clear skipped cooldown %ds left",
            int(cooldown - (now - last)),
        )
        return
    cleared = 0
    try:
        from exchange_proxy import clear_fl_source_bans

        cleared = clear_fl_source_bans()
    except Exception as exc:
        logger.warning("fl_listing:auto_ban_clear failed: %s", exc)
        return
    from exchange_browser_fetch import fl_hard_reset

    fl_hard_reset(
        reason=f"parsed_zero streak={streak}",
        storage=storage,
        set_restart_source=not fl_listing_subprocess_enabled(),
    )
    try:
        storage.set_setting("fl_auto_ban_clear_at", str(now))
    except Exception:
        pass
    _fl_streak_set(storage, 0)
    log_pipeline_line(
        cfg.radar_log_path,
        f"fl_listing:auto_ban_clear streak={streak} bans_cleared={cleared}",
    )


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
                published_at = parse_fl_published_at(t)
                break
        if not published_at:
            time_el = node.select_one("time[datetime]")
            if time_el and time_el.get("datetime"):
                published_at = parse_fl_published_at(str(time_el["datetime"]))

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


def _fetch_listing_html_requests(
    url: str,
    cfg: Config,
    *,
    timeout_sec: float,
    page: int,
) -> str | None:
    headers = {"User-Agent": fl_listing_user_agent(cfg.http_user_agent)}
    hint = proxy_log_hint("fl")
    try:
        resp = exchange_get(
            "fl",
            url,
            headers=headers,
            timeout_sec=timeout_sec,
            max_bans=_fl_httpx_max_bans(),
        )
    except requests.RequestException as exc:
        msg = f"Сетевой сбой при запросе ленты (стр. {page}, {hint}): {exc}"
        if page <= 1:
            raise FlListingError(msg) from exc
        logger.warning("fl_listing: %s — partial listing (%s)", msg, hint)
        return None

    if resp.status_code != 200:
        msg = f"HTTP {resp.status_code} для ленты ({url}, {hint})"
        if page <= 1:
            raise FlListingError(msg)
        logger.warning("fl_listing: %s — stop pagination", msg)
        return None

    encoding = resp.encoding or "utf-8"
    return resp.content.decode(encoding, errors="replace")


def _fetch_listing_html(
    url: str,
    cfg: Config,
    *,
    timeout_sec: float,
    page: int,
    storage: object | None = None,
) -> str | None:
    """O257: browser fetch with pipeline-logged failures + auto httpx fallback."""
    hint = proxy_log_hint("fl")
    ua = fl_listing_user_agent(cfg.http_user_agent)
    html: str | None = None
    browser_fail_reason: str = ""
    browser_fail_detail: str = ""

    if listing_browser_enabled():
        wall = _fl_listing_wall_clock_sec()
        try:
            html = fetch_listing_html_browser_slots_wall_clock(
                "fl",
                url,
                user_agent=ua,
                timeout_sec=min(timeout_sec, wall),
                wall_clock_sec=wall,
                storage=storage,
            )
        except HtmlFetchError as exc:
            exc_str = str(exc)
            if "timeout" in exc_str.lower() or "wall-clock" in exc_str.lower():
                browser_fail_reason = "browser_timeout"
                logger.warning(
                    "fl_listing: timeout after %ss — browser slots exhausted (%s)",
                    int(wall),
                    hint,
                )
            elif "ru_pool_dead" in exc_str.lower():
                browser_fail_reason = "ru_pool_dead"
                logger.warning("fl_listing: ru_pool_dead (%s)", hint)
            else:
                browser_fail_reason = "browser_error"
                logger.warning(
                    "fl_listing: Playwright failed (%s) — browser slots exhausted (%s)",
                    exc,
                    hint,
                )
            browser_fail_detail = exc_str[:200]
            # O257: log browser failure to pipeline so it appears in radar_site.log
            log_pipeline_line(
                cfg.radar_log_path,
                f"fetch:fl outcome=fail reason={browser_fail_reason}"
                f" proxy_hint={hint} err={browser_fail_detail}",
            )

    # O257: auto httpx fallback — fires when browser/subprocess returns None/empty,
    # regardless of FL_LISTING_SUBPROCESS env (which disabled fallback in O210).
    # Owner can disable with FL_HTTPX_AUTO_FALLBACK=0.
    use_auto_fallback = html is None and _fl_httpx_auto_fallback_enabled()
    use_legacy_fallback = html is None and not use_auto_fallback and _fl_allow_httpx_fallback()

    if use_auto_fallback or use_legacy_fallback:
        fb_t0 = time.monotonic()
        try:
            html = _fetch_listing_html_requests(url, cfg, timeout_sec=timeout_sec, page=page)
        except Exception as fb_exc:
            log_pipeline_line(
                cfg.radar_log_path,
                f"fetch:fl stage=fallback httpx outcome=fail"
                f" reason=httpx_fail proxy_hint={hint} err={str(fb_exc)[:200]}",
            )
            logger.warning("fl_listing: httpx fallback failed (%s): %s", hint, fb_exc)
            return None
        elapsed = time.monotonic() - fb_t0
        if html is not None:
            log_pipeline_line(
                cfg.radar_log_path,
                f"fetch:fl stage=fallback httpx outcome=ok elapsed={elapsed:.1f}s",
            )
            logger.info("fetch:fl stage=fallback httpx outcome=ok elapsed=%.1fs", elapsed)
        else:
            log_pipeline_line(
                cfg.radar_log_path,
                f"fetch:fl stage=fallback httpx outcome=fail reason=httpx_empty proxy_hint={hint}",
            )

    return html


def fetch_listing_projects(
    cfg: Config,
    *,
    timeout_sec: float = 30.0,
    storage: object | None = None,
) -> list[ListingProject]:
    """GET до `FL_LISTING_MAX_PAGES` страниц `cfg.fl_projects_url`, дедуп id внутри цикла.

    Без прокси: домашний IP, не TG_PROXY_URL и не системные HTTP_PROXY из ОС.
    O134/O139: `storage` → fresh-only (filter unseen; pinned known do not stop scan).
    """
    merged: list[ListingProject] = []
    seen: set[int] = set()

    max_pages = _fl_listing_max_pages()
    exchange_fetch_begin("fl")
    log_pipeline_line(cfg.radar_log_path, f"fetch:fl proxy={proxy_log_hint('fl')}")
    try:
        projects = _fetch_listing_pages(
            cfg, timeout_sec, max_pages, merged, seen, storage=storage
        )
        parsed_cards = len(projects)
        trimmed = trim_listing_at_known(projects, storage, SOURCE_FL)  # type: ignore[arg-type]
        fresh = len(trimmed)
        log_pipeline_line(
            cfg.radar_log_path,
            f"listing:fl parsed={parsed_cards} fresh={fresh}",
        )
        # O257: structured outcome line — owner can grep fetch:fl outcome= for daily triage.
        hint = proxy_log_hint("fl")
        if parsed_cards > 0:
            log_pipeline_line(
                cfg.radar_log_path,
                f"fetch:fl outcome=ok reason=ok tier=dc parsed={parsed_cards}",
            )
        else:
            reason = "browser_empty" if listing_browser_enabled() else "httpx_empty"
            log_pipeline_line(
                cfg.radar_log_path,
                f"fetch:fl outcome=fail reason={reason} tier=dc parsed=0 proxy_hint={hint}",
            )
        stash_listing_metrics("fl", parsed_cards, fresh)
        _maybe_fl_parsed_zero_recovery(cfg, storage, parsed_cards)
        return trimmed
    finally:
        exchange_fetch_end("fl")


def _fetch_listing_pages(
    cfg: Config,
    timeout_sec: float,
    max_pages: int,
    merged: list[ListingProject],
    seen: set[int],
    *,
    storage: object | None = None,
) -> list[ListingProject]:
    for page in range(1, max_pages + 1):
        page_url = _fl_listing_page_url(cfg.fl_projects_url, page)
        html = _fetch_listing_html(
            page_url, cfg, timeout_sec=timeout_sec, page=page, storage=storage
        )
        if html is None:
            break
        if page == 1:
            global _fl_last_listing_html
            _fl_last_listing_html = html
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

    feed_cat = category_from_fl_listing_url(cfg.fl_projects_url) or ""
    if not feed_cat:
        return merged
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
        for p in merged
    ]


def _parse_fl_detail_html(html: str, *, fallback_snippet: str = "") -> str:
    soup = BeautifulSoup(html, "html.parser")
    desc_el = soup.select_one(".fl-project-content__description-text")
    if desc_el:
        text = desc_el.get_text(" ", strip=True)
        if text:
            return text
    blocks: list[str] = []
    for sel in (".fl-project-content .b-layout__txt", ".b-layout__txt"):
        for node in soup.select(sel):
            t = node.get_text(" ", strip=True)
            if len(t) > 40:
                blocks.append(t)
    if blocks:
        return max(blocks, key=len)
    return fallback_snippet


def fetch_project_page_html(
    project_url: str,
    cfg: Config,
    *,
    timeout_sec: float = 30.0,
) -> tuple[str, bool]:
    """GET страницы проекта FL → HTML. (html, ok)."""
    url = (project_url or "").strip()
    if not url:
        return "", False
    headers = {"User-Agent": cfg.http_user_agent}
    try:
        resp = exchange_get("fl", url, headers=headers, timeout_sec=timeout_sec)
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
    """
    GET страницы проекта FL → (description, html, detail_ok).
    При ошибке — fallback_snippet, "", detail_ok=False.
    """
    html, ok = fetch_project_page_html(project_url, cfg, timeout_sec=timeout_sec)
    if not ok:
        return fallback_snippet, "", False
    text = _parse_fl_detail_html(html, fallback_snippet=fallback_snippet)
    detail_ok = bool(text and text != (fallback_snippet or "").strip())
    return text, html, detail_ok


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
    text, _, ok = fetch_project_detail(
        project_url,
        cfg,
        fallback_snippet=fallback_snippet,
        timeout_sec=timeout_sec,
    )
    return text, ok


_FL_GONE_MARKERS = (
    "проект закрыт",
    "заказ закрыт",
    "исполнитель уже выбран",
    "исполнитель найден",
    "страница не найдена",
    "проект не найден",
    "в архиве",
    "закрыт для откликов",
    "отклики не принимаются",
    "прием откликов закрыт",
    "приём откликов закрыт",
)

_FL_PROJECT_ID_RE = re.compile(r"/projects/(\d+)", re.I)


def _fl_redirected_away(original: str, final: str) -> bool:
    orig = (original or "").strip()
    fin = final.strip() if isinstance(final, str) else ""
    if not orig or not fin or orig.casefold() == fin.casefold():
        return False
    m = _FL_PROJECT_ID_RE.search(orig)
    if not m:
        return False
    pid = m.group(1)
    return f"/projects/{pid}" not in fin.casefold()


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
        resp = exchange_get("fl", url, headers=headers, timeout_sec=timeout_sec)
    except requests.RequestException:
        return None

    if resp.status_code == 404:
        return True
    if resp.status_code != 200:
        return None

    raw_final = getattr(resp, "url", None)
    final_url = raw_final.strip() if isinstance(raw_final, str) and raw_final.strip() else url
    if _fl_redirected_away(url, final_url):
        return True

    encoding = resp.encoding or "utf-8"
    html = resp.content.decode(encoding, errors="replace").casefold()
    if any(m in html for m in _FL_GONE_MARKERS):
        return True
    if ".fl-project-content__description-text" in html or "fl-project-content" in html:
        return False
    return None
