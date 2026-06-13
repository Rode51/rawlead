"""Парсинг листинга YouDo: SSR Next.js `/tasks-all-opened-all`."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from config import Config
from exchange_browser_fetch import (
    fetch_listing_html_browser_slots,
    fetch_listing_html_browser_slots_wall_clock,
    fetch_youdo_detail_html,
    fetch_youdo_detail_snapshot,
    listing_browser_enabled,
    youdo_browser_only,
)
from exchange_proxy import (
    exchange_fetch_begin,
    exchange_fetch_end,
    exchange_get,
    exchange_primary_proxy_url,
    proxy_log_hint,
)
from html_fetch import HtmlFetchError, fetch_html_playwright
from listing import SOURCE_YOUDO, ListingProject
from radar_cycle_log import log_pipeline_line

logger = logging.getLogger(__name__)

_TRACE_SNIP_MAX = 120


def _fmt_youdo_trace_fields(fields: dict[str, object]) -> str:
    parts: list[str] = []
    for key in sorted(fields):
        val = fields[key]
        if val is None or val == "":
            continue
        if isinstance(val, bool):
            parts.append(f"{key}={'1' if val else '0'}")
        else:
            s = str(val).replace("\n", " ").strip()
            if key == "error_snip" and len(s) > _TRACE_SNIP_MAX:
                s = s[:_TRACE_SNIP_MAX]
            if s:
                parts.append(f"{key}={s}")
    return " ".join(parts)


def log_youdo_trace(cfg: Config, stage: str, **fields: object) -> None:
    """Structured YouDo funnel line in radar_site.log (prefix youdo:trace)."""
    extra = _fmt_youdo_trace_fields(fields)
    line = f"youdo:trace stage={stage}"
    if extra:
        line += f" {extra}"
    log_pipeline_line(cfg.radar_log_path, line)


def log_youdo_trace_path(log_path: os.PathLike[str] | str | None, stage: str, **fields: object) -> None:
    """Same as log_youdo_trace when Config is unavailable (Playwright thread)."""
    if log_path is None:
        try:
            from ops_log_stream import resolve_radar_log_path

            log_path = resolve_radar_log_path()
        except Exception:
            return
    extra = _fmt_youdo_trace_fields(fields)
    line = f"youdo:trace stage={stage}"
    if extra:
        line += f" {extra}"
    log_pipeline_line(log_path, line)


def _mark_youdo_cycle_skip(storage, reason: str) -> None:
    storage.set_setting(YOUDO_CYCLE_SKIP_KEY, reason)


def youdo_consume_cycle_skip(storage) -> str:
    reason = storage.get_setting(YOUDO_CYCLE_SKIP_KEY, "").strip()
    storage.set_setting(YOUDO_CYCLE_SKIP_KEY, "")
    return reason


def youdo_fail_kind(error_msg: str) -> str:
    """Map failure text to exchange_health reason tag."""
    from exchange_health import classify_error

    kind = classify_error(error_msg)
    if kind == "parse":
        return "parse_empty"
    return kind


def log_youdo_fetch_end(cfg: Config, stats, health: dict) -> None:
    kind = str(health.get("last_error_kind") or "ok")
    err = str(stats.fetch_error or health.get("last_error_short") or "").strip()
    log_youdo_trace(
        cfg,
        "fetch_end",
        parsed=stats.parsed_cards if stats.parsed_cards >= 0 else 0,
        fresh=stats.downloaded,
        new=stats.new_ids,
        kind=kind,
        error_class=kind if kind not in ("", "ok") else "",
        error_snip=err[:_TRACE_SNIP_MAX] if err else "",
    )

YOUDO_COOLDOWN_KEY = "youdo_cooldown_until"
YOUDO_FETCH_CYCLE_KEY = "youdo_fetch_cycle_n"
YOUDO_FAIL_STREAK_KEY = "youdo_fail_streak"
YOUDO_TRAFFIC_GUARD_UNTIL_KEY = "youdo_traffic_guard_until"
YOUDO_CYCLE_SKIP_KEY = "youdo_last_cycle_skip"

_DEFAULT_LISTING_URL = "https://youdo.com/tasks-all-opened-all"
_TASK_ID_RE = re.compile(r"/t(\d+)")
_ANTIBOT_MARKERS = ("noscript", "exhkqyad", "just a moment", "checking your browser")


class YoudoListingError(RuntimeError):
    """Не удалось разобрать ленту YouDo."""


def _youdo_slot_retry_max() -> int:
    raw = os.getenv("YOUDO_SLOT_RETRY_ON_TIMEOUT", "3").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 3


def _youdo_listing_wall_clock_sec() -> float:
    """Wall budget must cover goto × slot retries (O177b: 120s blocked retry after 90s goto)."""
    raw = os.getenv("YOUDO_LISTING_TIMEOUT_SEC", "").strip()
    if raw:
        try:
            return max(float(raw), 10.0)
        except ValueError:
            pass
    goto = _youdo_goto_timeout_sec()
    retries = _youdo_slot_retry_max()
    return max(goto * retries + 60.0, 120.0)


def youdo_source_fetch_wall_sec() -> float:
    """Radar outer wall for YouDo fetch — must match internal browser budget (O179)."""
    return _youdo_listing_wall_clock_sec()


def _youdo_traffic_guard_fails() -> int:
    raw = os.getenv("YOUDO_TRAFFIC_GUARD_FAILS", "3").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 3


def _youdo_traffic_guard_cooldown_sec() -> float:
    raw = os.getenv("YOUDO_TRAFFIC_GUARD_COOLDOWN_MIN", "90").strip()
    try:
        return max(300.0, float(raw) * 60.0)
    except ValueError:
        return 90.0 * 60.0


def _get_youdo_fail_streak(storage) -> int:
    raw = storage.get_setting(YOUDO_FAIL_STREAK_KEY, "0") or "0"
    try:
        return max(0, int(raw))
    except ValueError:
        return 0


def _bump_youdo_fail_streak(storage) -> int:
    streak = _get_youdo_fail_streak(storage) + 1
    storage.set_setting(YOUDO_FAIL_STREAK_KEY, str(streak))
    if streak >= _youdo_traffic_guard_fails():
        until = time.time() + _youdo_traffic_guard_cooldown_sec()
        storage.set_setting(YOUDO_TRAFFIC_GUARD_UNTIL_KEY, str(until))
    return streak


def _reset_youdo_fail_streak(storage) -> None:
    storage.set_setting(YOUDO_FAIL_STREAK_KEY, "0")
    storage.set_setting(YOUDO_TRAFFIC_GUARD_UNTIL_KEY, "0")


def youdo_traffic_guard_blocks_fetch(storage) -> tuple[bool, int, str]:
    """After N consecutive fails — skip browser fetch to save proxy traffic (O179)."""
    streak = _get_youdo_fail_streak(storage)
    if streak < _youdo_traffic_guard_fails():
        return False, streak, ""
    raw = storage.get_setting(YOUDO_TRAFFIC_GUARD_UNTIL_KEY, "0").strip()
    try:
        until = float(raw or 0)
    except ValueError:
        until = 0.0
    if until > time.time():
        return True, streak, time.strftime("%H:%M", time.localtime(until))
    return False, streak, ""


def _log_youdo_traffic_guard_skip(cfg: Config, streak: int, until_hhmm: str) -> None:
    log_pipeline_line(
        cfg.radar_log_path,
        f"youdo:skip traffic_guard streak={streak} until={until_hhmm}",
    )
    log_youdo_trace(
        cfg,
        "cycle_decision",
        fetch_allowed=0,
        traffic_guard=1,
        fail_streak=streak,
        guard_until=until_hhmm,
        fetch_every_n=_youdo_fetch_every_n(),
    )


def _youdo_goto_timeout_sec() -> float:
    raw = os.getenv("YOUDO_GOTO_TIMEOUT_SEC", "").strip()
    if raw:
        try:
            return max(float(raw), 15.0)
        except ValueError:
            pass
    from exchange_browser_fetch import _youdo_goto_wait_until

    return 150.0 if _youdo_goto_wait_until() in ("load", "networkidle") else 90.0


def _youdo_cooldown_min() -> int:
    return max(1, int(os.getenv("YOUDO_COOLDOWN_MIN", "30")))


def _youdo_fetch_every_n() -> int:
    return max(1, int(os.getenv("YOUDO_FETCH_EVERY_N_CYCLES", "4")))


def _youdo_detail_fetch_enabled() -> bool:
    return os.getenv("YOUDO_DETAIL_FETCH", "1").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _should_fetch_youdo_listing(storage) -> bool:
    every = _youdo_fetch_every_n()
    if every <= 1:
        return True
    raw = storage.get_setting(YOUDO_FETCH_CYCLE_KEY, "0") or "0"
    try:
        n = int(raw) + 1
    except ValueError:
        n = 1
    storage.set_setting(YOUDO_FETCH_CYCLE_KEY, str(n))
    return (n - 1) % every == 0


def _log_youdo_fetch_every_n_skip(cfg: Config) -> None:
    log_pipeline_line(cfg.radar_log_path, "youdo:skip fetch_every_n")
    log_youdo_trace(
        cfg,
        "cycle_decision",
        fetch_allowed=0,
        fetch_every_n=_youdo_fetch_every_n(),
        cycle_n="skip",
    )
    try:
        from exchange_trace import log_exchange_trace

        log_exchange_trace("youdo", stage="fetch_every_n_skip")
    except Exception:
        pass


def _storage_for_cfg(cfg: Config):
    from storage import ProjectStorage

    return ProjectStorage(cfg.sqlite_path)


def youdo_cooldown_active(storage) -> tuple[bool, str]:
    raw = storage.get_setting(YOUDO_COOLDOWN_KEY, "0").strip()
    try:
        until = float(raw or 0)
    except ValueError:
        until = 0.0
    now = time.time()
    if until > now:
        mins = max(1, int((until - now + 59) // 60))
        hhmm = time.strftime("%H:%M", time.localtime(until))
        return True, f"cooldown до {hhmm} ({mins} min)"
    return False, ""


def set_youdo_cooldown(storage) -> None:
    until = time.time() + _youdo_cooldown_min() * 60
    storage.set_setting(YOUDO_COOLDOWN_KEY, str(until))


def _log_youdo_cooldown_skip(cfg: Config, mins: int, *, cooldown_until: str = "") -> None:
    log_pipeline_line(cfg.radar_log_path, f"youdo:skip cooldown {mins} min")
    log_youdo_trace(
        cfg,
        "cycle_decision",
        fetch_allowed=0,
        cooldown_until=cooldown_until or f"{mins}min",
        fetch_every_n=_youdo_fetch_every_n(),
    )
    try:
        from exchange_trace import log_exchange_trace

        log_exchange_trace("youdo", stage="cooldown_skip", err=f"{mins}min")
    except Exception:
        pass


def _on_youdo_fetch_fail(cfg: Config, storage) -> None:
    streak = _bump_youdo_fail_streak(storage)
    set_youdo_cooldown(storage)
    if streak >= _youdo_traffic_guard_fails():
        until_raw = storage.get_setting(YOUDO_TRAFFIC_GUARD_UNTIL_KEY, "0").strip()
        try:
            until_hhmm = time.strftime("%H:%M", time.localtime(float(until_raw)))
        except ValueError:
            until_hhmm = until_raw
        log_youdo_trace(
            cfg,
            "traffic_guard",
            fail_streak=streak,
            guard_until=until_hhmm,
        )
    proxy = exchange_primary_proxy_url("youdo")
    if proxy:
        from exchange_browser_fetch import invalidate_browser_slot

        invalidate_browser_slot("youdo", proxy)


def _listing_url() -> str:
    return (os.getenv("YOUDO_LISTING_URL", "") or _DEFAULT_LISTING_URL).strip()


def _looks_like_antibot(html: str) -> bool:
    if not html or not html.strip():
        return True
    low = html.casefold()
    # Живая лента SSR — не антибот (на нормальной странице тоже есть <noscript>)
    if _TASK_ID_RE.search(html) or (
        'data-id' in low and 'href="/t' in low.replace("'", '"')
    ):
        return False
    if any(m in low for m in ("exhkqyad", "just a moment", "checking your browser")):
        return True
    if "403 forbidden" in low[:2500] and len(html.strip()) < 5000:
        return True
    if len(html.strip()) < 4000 and not _TASK_ID_RE.search(html):
        return True
    return False


def _task_id_from_link(link, href: str) -> int | None:
    data_id = getattr(link, "get", lambda _k, _d=None: None)("data-id")
    if data_id:
        try:
            return int(str(data_id).strip())
        except ValueError:
            pass
    m = _TASK_ID_RE.search(href or "")
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def _canonical_task_url(page_url: str, task_id: int) -> str:
    parsed = urlparse(page_url)
    host = parsed.netloc or "youdo.com"
    scheme = parsed.scheme or "https"
    return f"{scheme}://{host}/t{task_id}"


def _save_listing_html_debug(html: str, *, tag: str = "youdo") -> str:
    root = Path(__file__).resolve().parent.parent / "data" / "debug_listings"
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{tag}_{int(time.time())}.html"
    path.write_text(html[:500_000], encoding="utf-8", errors="replace")
    return str(path)


def parse_listing_html(html: str, page_url: str) -> list[ListingProject]:
    """Разбор сохранённого HTML листинга (отладка / тесты)."""
    if not html or not html.strip():
        raise YoudoListingError("Пустой HTML листинга YouDo.")
    if _looks_like_antibot(html):
        raise YoudoListingError(
            "Ответ похож на антибот — нужен YOUDO_PROXY_URLS или Playwright."
        )

    soup = BeautifulSoup(html, "html.parser")
    title_links = soup.select('a[data-id][href*="/t"]')
    if not title_links:
        title_links = [
            a
            for a in soup.find_all("a", href=True)
            if _TASK_ID_RE.search(str(a["href"]))
        ]

    out: list[ListingProject] = []
    seen: set[int] = set()

    for link in title_links:
        href = str(link.get("href") or "").strip()
        pid = _task_id_from_link(link, href)
        if pid is None or pid in seen:
            continue
        seen.add(pid)

        item = link.find_parent("li") or link.find_parent("div")
        title = link.get_text(" ", strip=True)
        if not title and item:
            title_el = item.select_one('[class*="TasksList_title"]')
            title = title_el.get_text(" ", strip=True) if title_el else ""
        if not title:
            continue

        listing_snippet = ""
        budget_text = ""
        published_at = ""
        if item:
            content_el = item.select_one('[class*="TasksList_contentBlock"]')
            if content_el:
                listing_snippet = content_el.get_text(" ", strip=True)
            price_el = item.select_one('[class*="TasksList_price"]')
            if price_el:
                budget_text = price_el.get_text(" ", strip=True)
            date_el = item.select_one('[class*="TasksList_date"]')
            if date_el:
                published_at = date_el.get_text(" ", strip=True)

        out.append(
            ListingProject(
                project_id=pid,
                title=title,
                budget_text=budget_text,
                url=_canonical_task_url(page_url, pid),
                published_at=published_at,
                listing_snippet=listing_snippet or title,
                source=SOURCE_YOUDO,
            )
        )

    if not out:
        saved = _save_listing_html_debug(html)
        raise YoudoListingError(
            "На странице нет карточек заданий (`a[data-id]` / `/t{id}`) — сменилась вёрстка."
            f" HTML saved: {saved}"
        )
    return out


def _fetch_listing_html_browser(
    url: str,
    cfg: Config,
    *,
    timeout_sec: float,
    storage,
) -> str:
    """Browser-only (O63/O156): primary slot, warm human path."""
    wall = _youdo_listing_wall_clock_sec()
    goto_timeout = min(_youdo_goto_timeout_sec(), wall)
    try:
        html = fetch_listing_html_browser_slots_wall_clock(
            "youdo",
            url,
            user_agent=cfg.http_user_agent,
            timeout_sec=goto_timeout,
            wall_clock_sec=wall,
        )
    except HtmlFetchError as exc:
        msg = f"browser_fail={exc}"
        log_pipeline_line(cfg.radar_log_path, f"youdo_listing: {msg}")
        logger.warning("youdo_listing: %s — no httpx fallback", msg)
        _on_youdo_fetch_fail(cfg, storage)
        raise YoudoListingError(f"browser failed ({exc})") from exc

    if _looks_like_antibot(html):
        saved = _save_listing_html_debug(html, tag="youdo_antibot")
        msg = f"browser_fail=antibot HTML saved={saved}"
        log_pipeline_line(cfg.radar_log_path, f"youdo_listing: {msg}")
        log_youdo_trace(
            cfg,
            "browser",
            status="antibot",
            html_len=len(html),
            antibot_hit=1,
            debug_path=saved,
        )
        _on_youdo_fetch_fail(cfg, storage)
        raise YoudoListingError(
            "Ответ похож на антибот после browser — cooldown."
            f" HTML saved: {saved}"
        )
    return html


def _fetch_listing_html(
    url: str,
    cfg: Config,
    *,
    timeout_sec: float,
    storage,
) -> str:
    """EXCHANGE_LISTING_BROWSER=1 → только Playwright; иначе httpx → legacy Playwright."""
    if listing_browser_enabled() or youdo_browser_only():
        return _fetch_listing_html_browser(url, cfg, timeout_sec=timeout_sec, storage=storage)

    hint = proxy_log_hint("youdo")
    html = _fetch_html_requests(url, cfg, timeout_sec=timeout_sec)
    if _looks_like_antibot(html):
        logger.info("youdo_listing: antibot HTML — legacy Playwright fallback (%s)", hint)
        html = _fetch_html_playwright(url, cfg, timeout_sec=timeout_sec)
    return html


def _fetch_html_requests(
    url: str,
    cfg: Config,
    *,
    timeout_sec: float,
) -> str:
    headers = {
        "User-Agent": cfg.http_user_agent,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Referer": "https://youdo.com/",
    }
    resp = exchange_get("youdo", url, headers=headers, timeout_sec=timeout_sec)
    if resp.status_code != 200:
        raise YoudoListingError(f"HTTP {resp.status_code} для ленты ({url})")
    encoding = resp.encoding or "utf-8"
    return resp.content.decode(encoding, errors="replace")


def _fetch_html_playwright(url: str, cfg: Config, *, timeout_sec: float) -> str:
    from exchange_proxy import exchange_primary_proxy_url

    proxy_url = exchange_primary_proxy_url("youdo")
    try:
        return fetch_html_playwright(
            url,
            user_agent=cfg.http_user_agent,
            timeout_sec=timeout_sec,
            proxy_url=proxy_url,
            wait_until="networkidle",
        )
    except HtmlFetchError as exc:
        raise YoudoListingError(str(exc)) from exc


def _parse_youdo_detail_html(html: str, *, fallback_snippet: str = "") -> str:
    """Полный текст ТЗ со страницы /t{id}."""
    if not html or not html.strip():
        return fallback_snippet
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if script and script.string:
        try:
            payload = json.loads(script.string)
            props = payload.get("props", {}).get("pageProps", {})
            for key in ("task", "taskData", "data"):
                block = props.get(key)
                if isinstance(block, dict):
                    for field in ("description", "text", "content", "body"):
                        val = block.get(field)
                        if isinstance(val, str) and len(val.strip()) > len(
                            (fallback_snippet or "").strip()
                        ):
                            return val.strip()
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass
    for sel in (
        '[class*="TaskDescription"]',
        '[class*="Description_text"]',
        '[class*="taskDescription"]',
        ".task-description",
        "article",
    ):
        node = soup.select_one(sel)
        if node:
            text = node.get_text(" ", strip=True)
            if len(text) > len((fallback_snippet or "").strip()):
                return text
    return fallback_snippet


def fetch_project_page_html(
    project_url: str,
    cfg: Config,
    *,
    timeout_sec: float = 45.0,
) -> tuple[str, bool]:
    url = (project_url or "").strip()
    if not url:
        return "", False
    if not _youdo_detail_fetch_enabled():
        return "", False
    if youdo_browser_only():
        try:
            html = fetch_youdo_detail_html(
                url,
                user_agent=cfg.http_user_agent,
                timeout_sec=timeout_sec,
            )
            if html and not _looks_like_antibot(html):
                return html, True
        except HtmlFetchError as exc:
            logger.warning("youdo_detail: browser failed: %s", exc)
        return "", False
    headers = {
        "User-Agent": cfg.http_user_agent,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Referer": "https://youdo.com/",
    }
    try:
        resp = exchange_get("youdo", url, headers=headers, timeout_sec=timeout_sec)
        if resp.status_code == 200:
            encoding = resp.encoding or "utf-8"
            html = resp.content.decode(encoding, errors="replace")
            if not _looks_like_antibot(html):
                return html, True
    except Exception:
        pass
    try:
        html = _fetch_html_playwright(url, cfg, timeout_sec=timeout_sec)
        if html and not _looks_like_antibot(html):
            return html, True
    except YoudoListingError:
        pass
    return "", False


def fetch_project_detail(
    project_url: str,
    cfg: Config,
    *,
    fallback_snippet: str = "",
    timeout_sec: float = 45.0,
) -> tuple[str, str, bool]:
    """(description, html, detail_ok)."""
    html, ok = fetch_project_page_html(project_url, cfg, timeout_sec=timeout_sec)
    if not ok:
        return fallback_snippet, "", False
    text = _parse_youdo_detail_html(html, fallback_snippet=fallback_snippet)
    detail_ok = bool(text and text != (fallback_snippet or "").strip())
    return text, html, detail_ok


def fetch_listing_projects(
    cfg: Config,
    *,
    timeout_sec: float = 45.0,
    storage=None,
) -> list[ListingProject]:
    """GET листинга YouDo; при антиботе — Playwright + прокси."""
    st = storage or _storage_for_cfg(cfg)
    every = _youdo_fetch_every_n()
    raw_cycle = st.get_setting(YOUDO_FETCH_CYCLE_KEY, "0") or "0"
    try:
        prev_cycle_n = int(raw_cycle)
    except ValueError:
        prev_cycle_n = 0

    active, msg = youdo_cooldown_active(st)
    cooldown_raw = st.get_setting(YOUDO_COOLDOWN_KEY, "0").strip()
    cooldown_until = ""
    if active and cooldown_raw:
        try:
            until = float(cooldown_raw)
            cooldown_until = time.strftime("%H:%M", time.localtime(until))
        except ValueError:
            cooldown_until = cooldown_raw

    fetch_on_cycle = prev_cycle_n % every == 0
    fetch_allowed = not active and fetch_on_cycle
    log_youdo_trace(
        cfg,
        "cycle_decision",
        fetch_allowed=1 if fetch_allowed else 0,
        cooldown_until=cooldown_until,
        fetch_every_n=every,
        cycle_n=prev_cycle_n + 1,
    )

    if active:
        raw = st.get_setting(YOUDO_COOLDOWN_KEY, "0").strip()
        try:
            until = float(raw or 0)
            mins = max(1, int((until - time.time() + 59) // 60))
        except ValueError:
            mins = _youdo_cooldown_min()
        _log_youdo_cooldown_skip(cfg, mins, cooldown_until=cooldown_until)
        st.set_setting("status_youdo_cooldown_msg", msg)
        raise YoudoListingError(f"antibot cooldown {msg}")
    st.set_setting("status_youdo_cooldown_msg", "")
    if not _should_fetch_youdo_listing(st):
        _log_youdo_fetch_every_n_skip(cfg)
        _mark_youdo_cycle_skip(st, "fetch_every_n")
        return []

    guard_blocks, fail_streak, guard_until = youdo_traffic_guard_blocks_fetch(st)
    if guard_blocks:
        _log_youdo_traffic_guard_skip(cfg, fail_streak, guard_until)
        raise YoudoListingError(
            f"traffic_guard antibot streak={fail_streak} until={guard_until}"
        )
    url = _listing_url()
    hint = proxy_log_hint("youdo")
    slot = ""
    if " slot=" in hint:
        slot = hint.split(" slot=", 1)[1].split()[0]
    proxy_hint = hint.split(" slot=", 1)[0] if " slot=" in hint else hint
    log_youdo_trace(
        cfg,
        "fetch_start",
        proxy_hint=proxy_hint,
        slot=slot,
        wall_clock_sec=int(_youdo_listing_wall_clock_sec()),
        browser_only=1 if (listing_browser_enabled() or youdo_browser_only()) else 0,
    )
    exchange_fetch_begin("youdo")
    log_pipeline_line(cfg.radar_log_path, f"fetch:youdo proxy={hint}")
    try:
        html = _fetch_listing_html(url, cfg, timeout_sec=timeout_sec, storage=st)
        projects = parse_listing_html(html, url)
        _reset_youdo_fail_streak(st)
        log_youdo_trace(
            cfg,
            "parse",
            cards_found=len(projects),
            new_ids=0,
            skipped_reason="",
        )
        return projects
    except YoudoListingError as exc:
        msg = str(exc)
        log_youdo_trace(
            cfg,
            "parse",
            cards_found=0,
            new_ids=0,
            skipped_reason=youdo_fail_kind(msg),
        )
        raise
    finally:
        exchange_fetch_end("youdo")


_YOUDO_GONE_MARKERS = (
    "закрыто для откликов",
    "закрыт для откликов",
    "задание закрыто",
    "заказ закрыт",
    "исполнитель выбран",
    "исполнитель уже выбран",
    "исполнитель найден",
    "задание не найдено",
    "задача не найдена",
    "страница не найдена",
    "страница была удалена",
    "удалена или доступ к ней ограничен",
    "page-deleted",
    "task not found",
    "task closed",
    "executor chosen",
    "executor selected",
)

# O182: in-progress / SBR — not bare «выполняется» (open tasks mention it in body).
_YOUDO_INPROGRESS_MARKERS = (
    "зарезервировано",
    "завершено",
    "задание завершено",
)
_YOUDO_STATUS_CHIP_RE = re.compile(r">\s*выполняется\s*<", re.IGNORECASE)
_YOUDO_GONE_STATUS_CODES = frozenset(
    {
        "PendingApprovement",
        "Finished",
        "Closed",
        "Completed",
        "InProgress",
        "Done",
    }
)
_YOUDO_GONE_STATUS_FLAGS = frozenset({"process", "finished", "closed", "done"})


def _youdo_next_data_payload(html: str) -> dict | None:
    if not html or "__next_data__" not in html.casefold():
        return None
    m = re.search(
        r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except (json.JSONDecodeError, TypeError):
        return None
    return data if isinstance(data, dict) else None


def _youdo_task_statuses_from_next_data(payload: dict) -> dict | None:
    props = payload.get("props")
    if not isinstance(props, dict):
        return None
    page_props = props.get("pageProps")
    if isinstance(page_props, dict):
        for key in ("task", "taskData", "data"):
            block = page_props.get(key)
            if not isinstance(block, dict):
                continue
            statuses = block.get("taskStatuses") or block.get("statuses")
            if isinstance(statuses, dict):
                return statuses
            if any(k in block for k in ("isOpen", "isInProcess", "isFinished", "isClosedForOffers")):
                return block
    init = props.get("initialState")
    if isinstance(init, dict):
        task_state = init.get("taskState")
        if isinstance(task_state, dict):
            statuses = task_state.get("taskStatuses")
            if isinstance(statuses, dict):
                return statuses
    return None


def _youdo_gone_from_task_statuses(statuses: dict) -> bool | None:
    if not isinstance(statuses, dict):
        return None
    if statuses.get("isOpen") is True and not statuses.get("isInProcess"):
        return False
    if any(
        statuses.get(k)
        for k in (
            "isInProcess",
            "isFinished",
            "isClosed",
            "isClosedForOffers",
            "isSbrHoldInProgress",
        )
    ):
        return True
    flag = str(statuses.get("flag") or "").casefold()
    if flag in _YOUDO_GONE_STATUS_FLAGS:
        return True
    code = str(statuses.get("code") or "")
    if code in _YOUDO_GONE_STATUS_CODES:
        return True
    return None


def _youdo_redirected_away(original: str, final: str) -> bool:
    orig = (original or "").strip()
    fin = final.strip() if isinstance(final, str) else ""
    if not orig or not fin or orig.casefold() == fin.casefold():
        return False
    m = _TASK_ID_RE.search(orig)
    if not m:
        return False
    tid = m.group(1)
    return f"/t{tid}" not in fin.casefold()


def _youdo_gone_from_html(original_url: str, final_url: str, html: str) -> bool | None:
    if _youdo_redirected_away(original_url, final_url):
        return True
    fin_low = (final_url or "").casefold()
    if "page-deleted" in fin_low:
        return True
    low = html.casefold()
    if any(m in low for m in _YOUDO_GONE_MARKERS):
        return True
    payload = _youdo_next_data_payload(html)
    if payload is not None:
        statuses = _youdo_task_statuses_from_next_data(payload)
        if statuses is not None:
            gone = _youdo_gone_from_task_statuses(statuses)
            if gone is not None:
                return gone
    if any(m in low for m in _YOUDO_INPROGRESS_MARKERS):
        return True
    if _YOUDO_STATUS_CHIP_RE.search(html):
        return True
    if "taskdescription" in low or "__next_data__" in low:
        return False
    m = _TASK_ID_RE.search(original_url or "")
    if m and f"/t{m.group(1)}" in low:
        return False
    return None


def _youdo_delist_html_usable(html: str) -> bool:
    """Delist recheck: allow short gone pages; block only hard antibot walls."""
    if not html or not html.strip():
        return False
    low = html.casefold()
    if any(m in low for m in ("exhkqyad", "just a moment", "checking your browser")):
        return False
    return True


def check_project_page_gone(
    project_url: str,
    cfg: Config,
    *,
    timeout_sec: float = 20.0,
) -> bool | None:
    """O180: True — заказ снят/404; False — жив; None — не удалось проверить."""
    url = (project_url or "").strip()
    if not url:
        return None
    browser_timeout = max(float(timeout_sec), 60.0)
    # Browser-first: HTTP detail burns youdo proxies (403) before Playwright can run.
    try:
        html, final_url = fetch_youdo_detail_snapshot(
            url,
            user_agent=cfg.http_user_agent,
            timeout_sec=browser_timeout,
        )
        if html and _youdo_delist_html_usable(html):
            gone = _youdo_gone_from_html(url, final_url, html)
            if gone is not None:
                return gone
    except (HtmlFetchError, Exception):
        pass
    # Single-slot HTTP fallback — exchange_get cycles all proxies (403 storm).
    from exchange_proxy import _proxies_dict, exchange_alive_proxy_urls

    headers = {
        "User-Agent": cfg.http_user_agent,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Referer": "https://youdo.com/",
    }
    alive = exchange_alive_proxy_urls("youdo")
    if not alive:
        return None
    proxy = alive[0]
    try:
        resp = requests.get(
            url,
            headers=headers,
            timeout=timeout_sec,
            proxies=_proxies_dict(proxy),
            allow_redirects=True,
        )
        if resp.status_code == 404:
            return True
        if resp.status_code == 200:
            raw_final = getattr(resp, "url", None)
            final_url = (
                raw_final.strip() if isinstance(raw_final, str) and raw_final.strip() else url
            )
            encoding = resp.encoding or "utf-8"
            html = resp.content.decode(encoding, errors="replace")
            if _youdo_delist_html_usable(html):
                return _youdo_gone_from_html(url, final_url, html)
    except requests.RequestException:
        pass
    return None
