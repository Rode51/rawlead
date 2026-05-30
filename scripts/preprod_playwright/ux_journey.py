"""§ O37-UX: Playwright user journeys J1–J11 на prod/staging.

  .venv\\Scripts\\python.exe scripts\\preprod_playwright\\ux_journey.py --base-url https://rawlead.ru
  .venv\\Scripts\\python.exe scripts\\preprod_playwright\\ux_journey.py --base-url https://rawlead.ru --headed
  .venv\\Scripts\\python.exe scripts\\preprod_playwright\\ux_journey.py --viewport mobile
  .venv\\Scripts\\python.exe scripts\\preprod_playwright\\ux_journey.py --browser yandex --headed
  .venv\\Scripts\\python.exe scripts\\preprod_playwright\\ux_journey.py --browser yandex-profile --headed

J5/J8: --storage-state · RAWLEAD_PREPROD_ACCESS_TOKEN · --browser cdp (Dolphin Anty / CDP)

Требует: pip install playwright (chromium — fallback; yandex — browser.exe с диска)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

for _stream in (sys.stdout, sys.stderr):
    enc = getattr(_stream, "encoding", None) or ""
    if enc.lower() != "utf-8":
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass

_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_STORAGE = _ROOT / "data" / "preprod_playwright" / "storage_state.json"
_ARTIFACT_DIR = _ROOT / "data" / "preprod_ux_journey"
_DRAFT_TIMEOUT_MS = 120_000
_YANDEX_EXE = Path(r"C:\Program Files\Yandex\YandexBrowser\Application\browser.exe")
_YANDEX_USER_DATA = (
    Path(os.environ.get("LOCALAPPDATA", "")) / "Yandex" / "YandexBrowser" / "User Data"
)


def _cdp_alive(cdp_url: str) -> bool:
    try:
        with urllib.request.urlopen(f"{cdp_url.rstrip('/')}/json/version", timeout=2) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _restart_yandex_with_cdp(exe: Path, port: int = 9222) -> str:
    """Закрыть Yandex и поднять с --remote-debugging-port (сессия restore)."""
    cdp_url = f"http://127.0.0.1:{port}"
    if _cdp_alive(cdp_url):
        return cdp_url
    print(
        "Перезапускаю Яндекс Браузер с CDP (вкладки должны восстановиться)…",
        file=sys.stderr,
    )
    if sys.platform == "win32":
        ps = (
            "Get-Process browser -ErrorAction SilentlyContinue | "
            "Where-Object { $_.Path -like '*YandexBrowser*' } | "
            "Stop-Process -Force -ErrorAction SilentlyContinue"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            check=False,
            capture_output=True,
        )
    time.sleep(2)
    subprocess.Popen(
        [
            str(exe),
            f"--remote-debugging-port={port}",
            "--restore-last-session",
            "--no-first-run",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(45):
        if _cdp_alive(cdp_url):
            print(f"CDP готов: {cdp_url}", file=sys.stderr)
            return cdp_url
        time.sleep(1)
    raise RuntimeError(
        f"CDP не поднялся на {cdp_url}. Запусти вручную:\n"
        f'  "{exe}" --remote-debugging-port={port}'
    )


def _resolve_yandex_paths() -> tuple[Path, Path]:
    exe = _YANDEX_EXE
    if not exe.is_file():
        alt = Path(os.environ.get("LOCALAPPDATA", "")) / "Yandex" / "YandexBrowser" / "Application" / "browser.exe"
        if alt.is_file():
            exe = alt
    ud = _YANDEX_USER_DATA
    return exe, ud


def _launch_playwright_context(
    p: Any,
    *,
    browser_name: str,
    headless: bool,
    viewport: dict[str, int],
    storage_state: Path | None,
    access_token: str | None,
) -> tuple[Any | None, Any]:
    """Returns (browser_or_none, context). browser set when not persistent."""
    if browser_name == "chromium":
        browser = p.chromium.launch(headless=headless)
        ctx_kwargs: dict[str, Any] = {"viewport": viewport, "locale": "ru-RU"}
        if storage_state and storage_state.is_file():
            ctx_kwargs["storage_state"] = str(storage_state)
        context = browser.new_context(**ctx_kwargs)
        if access_token and not (storage_state and storage_state.is_file()):
            context.add_init_script(
                f'localStorage.setItem("rawlead_access_token", {json.dumps(access_token)});'
            )
        return browser, context

    exe, user_data = _resolve_yandex_paths()
    if not exe.is_file():
        raise FileNotFoundError(f"Yandex Browser не найден: {exe}")

    if browser_name == "yandex-profile":
        if not user_data.is_dir():
            raise FileNotFoundError(f"Профиль Yandex не найден: {user_data}")
        print(
            "Yandex profile: закрой все окна Яндекс Браузера перед прогоном (иначе lock).",
            file=sys.stderr,
        )
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(user_data),
                executable_path=str(exe),
                headless=headless,
                locale="ru-RU",
                viewport=viewport,
                args=["--profile-directory=Default"],
            )
        except Exception as exc:
            hint = (
                "Профиль занят? Закрой Яндекс Браузер или используйте:\n"
                f'  "{exe}" --remote-debugging-port=9222\n'
                "  затем: --browser yandex-cdp"
            )
            raise RuntimeError(hint) from exc
        return None, context

    if browser_name in ("cdp", "dolphin-cdp", "yandex-cdp"):
        if browser_name == "yandex-cdp":
            port = int(os.environ.get("YANDEX_CDP_PORT", "9222"))
            cdp_url = os.environ.get("YANDEX_CDP_URL", f"http://127.0.0.1:{port}")
            if not _cdp_alive(cdp_url):
                cdp_url = _restart_yandex_with_cdp(exe, port)
        else:
            cdp_url = (
                os.environ.get("DOLPHIN_CDP_URL", "").strip()
                or os.environ.get("CDP_URL", "").strip()
                or "http://127.0.0.1:9222"
            )
            if not _cdp_alive(cdp_url):
                raise RuntimeError(
                    f"CDP недоступен: {cdp_url}. Открой профиль Dolphin Anty с remote debugging "
                    "или задай DOLPHIN_CDP_URL."
                )
        browser = p.chromium.connect_over_cdp(cdp_url)
        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = browser.new_context(viewport=viewport, locale="ru-RU")
        if access_token:
            context.add_init_script(
                f'localStorage.setItem("rawlead_access_token", {json.dumps(access_token)});'
            )
        return browser, context

    if browser_name == "yandex":
        browser = p.chromium.launch(
            executable_path=str(exe),
            headless=headless,
        )
        ctx_kwargs = {"viewport": viewport, "locale": "ru-RU"}
        if storage_state and storage_state.is_file():
            ctx_kwargs["storage_state"] = str(storage_state)
        context = browser.new_context(**ctx_kwargs)
        if access_token and not (storage_state and storage_state.is_file()):
            context.add_init_script(
                f'localStorage.setItem("rawlead_access_token", {json.dumps(access_token)});'
            )
        return browser, context

    raise ValueError(f"unknown browser: {browser_name}")


@dataclass
class JourneyCtx:
    base: str
    page: Any
    profile_auth: bool = False
    allow_manual_login: bool = False
    console_errors: list[str] = field(default_factory=list)
    network_failures: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)

    def add_finding(self, severity: str, message: str, *, journey: str = "") -> None:
        self.findings.append(
            {"severity": severity, "journey": journey, "message": message}
        )

    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f["severity"] == "critical")


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _attach_observers(ctx: JourneyCtx) -> None:
    page = ctx.page

    def on_console(msg: Any) -> None:
        if msg.type in ("error", "warning"):
            text = msg.text or ""
            if "favicon" in text.casefold():
                return
            ctx.console_errors.append(f"[{msg.type}] {text}")

    def on_response(response: Any) -> None:
        status = response.status
        if status < 400:
            return
        url = response.url
        if not any(
            x in url
            for x in ("/wp-json/rawlead", "api.rawlead", "/v1/feed", "/v1/skills")
        ):
            return
        ctx.network_failures.append(
            {"status": status, "url": url, "method": response.request.method}
        )

    def on_request_failed(request: Any) -> None:
        url = request.url or ""
        if "/draft" not in url and "/wp-json/rawlead" not in url:
            return
        failure = request.failure or ""
        ctx.network_failures.append(
            {
                "status": 0,
                "url": url,
                "method": request.method,
                "error": str(failure),
            }
        )

    page.on("console", on_console)
    page.on("response", on_response)
    page.on("requestfailed", on_request_failed)


def _screenshot(ctx: JourneyCtx, journey_id: str, phase: str) -> str:
    _ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    path = _ARTIFACT_DIR / f"{journey_id}_{phase}.png"
    ctx.page.screenshot(path=str(path), full_page=False)
    return str(path.relative_to(_ROOT))


def _feed_error_visible(ctx: JourneyCtx) -> str | None:
    err = ctx.page.locator("#rl-feed-error:not([hidden])")
    if err.count() and err.is_visible():
        return (err.inner_text() or "")[:300]
    return None


def _goto_lenta(ctx: JourneyCtx) -> None:
    ctx.page.goto(f"{ctx.base}/lenta/", wait_until="domcontentloaded")
    ctx.page.wait_for_selector('[data-rl-app="feed"]', state="visible")
    ctx.page.wait_for_selector(
        "#rl-feed-list .rl-lead-card, #rl-feed-list .rl-feed-empty, #rl-feed-count",
        timeout=45_000,
    )


def _open_skills_panel(ctx: JourneyCtx) -> None:
    dd = ctx.page.locator(".rl-feed-skills-dd")
    if not dd.get_attribute("open"):
        ctx.page.locator("#rl-feed-skills-trigger").click()
    ctx.page.wait_for_selector("#rl-feed-skills-panel", state="visible")


def _has_feed_token(ctx: JourneyCtx) -> bool:
    return bool(
        ctx.page.evaluate(
            "() => !!(localStorage.getItem('rawlead_access_token') || '').trim()"
        )
    )


def _wait_feed_logged_in(ctx: JourneyCtx) -> None:
    _goto_lenta(ctx)
    ctx.page.wait_for_timeout(1500)
    if _has_feed_token(ctx):
        return
    msg = (
        "Нет входа в RawLead (localStorage rawlead_access_token пуст). "
        "Нажмите «Войти →» → TG Login на /cabinet/ или в шапке."
    )
    if ctx.allow_manual_login:
        print(f"\n{msg}\nПосле входа вернитесь на /lenta/ и нажмите Enter в терминале…", file=sys.stderr)
        input()
        _goto_lenta(ctx)
        ctx.page.wait_for_timeout(2000)
        if not _has_feed_token(ctx):
            raise RuntimeError(msg)
        return
    raise RuntimeError(msg)


def _wait_effective_access(ctx: JourneyCtx) -> None:
    try:
        ctx.page.wait_for_function(
            """
            async () => {
              const t = (localStorage.getItem('rawlead_access_token') || '').trim();
              const url = window.rawleadFeed && window.rawleadFeed.restSubscription;
              if (!t || !url) return false;
              const r = await fetch(url, {
                credentials: 'same-origin',
                headers: { Authorization: 'Bearer ' + t },
              });
              if (!r.ok) return false;
              const d = await r.json();
              return !!(d && d.effective_access);
            }
            """,
            timeout=60_000,
        )
    except Exception as exc:
        raise RuntimeError(
            "Нет paid-доступа (effective_access). Нужна активная подписка / Stars."
        ) from exc


def _apply_skills_for_match(ctx: JourneyCtx) -> None:
    _open_skills_panel(ctx)
    chip = ctx.page.locator(
        "#rl-feed-skills .rl-feed-skill:not(.is-disabled), #rl-feed-skills .rl-chip"
    ).first
    chip.wait_for(state="visible", timeout=30_000)
    chip.click()
    ctx.page.locator("#rl-feed-skills-apply").click()
    ctx.page.wait_for_timeout(2000)
    if _feed_error_visible(ctx):
        raise RuntimeError("ошибка ленты после «Применить» навыки")


def _card_match_percent(card: Any) -> int:
    label = card.locator(".rl-match__label span, .rl-match__label")
    if not label.count():
        return 0
    text = label.first.inner_text() or ""
    m = re.search(r"(\d+)\s*%", text)
    return int(m.group(1)) if m else 0


def _ensure_feed_draft_ready(ctx: JourneyCtx) -> None:
    """Вход + paid → карточки с кнопкой «Написать отклик» (O61: km=0 OK)."""
    _wait_feed_logged_in(ctx)
    _wait_effective_access(ctx)
    ctx.page.wait_for_selector("#rl-feed-list .rl-lead-card[data-id]", timeout=45_000)
    if not _cards_with_reply_btn(ctx):
        raise RuntimeError(
            "Нет карточек с «Написать отклик». Нужен вход в TG + paid (effective_access). "
            "km=0 допустим (O61)."
        )


def _cards_with_reply_btn(ctx: JourneyCtx) -> list[Any]:
    def _scan() -> list[Any]:
        cards = ctx.page.locator("#rl-feed-list .rl-lead-card[data-id]")
        out: list[Any] = []
        n = cards.count()
        for i in range(n):
            card = cards.nth(i)
            if card.locator(".rl-feed-card__reply-btn").count():
                out.append(card)
                continue
            if not card.evaluate(
                "el => el.classList.contains('is-expanded')"
            ):
                card.locator(".rl-lead-card__title").first.click()
                ctx.page.wait_for_timeout(350)
            if card.locator(".rl-feed-card__reply-btn").count():
                out.append(card)
        return out

    seen: set[str] = set()
    merged: list[Any] = []
    for _ in range(10):
        for card in _scan():
            lid = card.get_attribute("data-id") or ""
            if lid and lid not in seen:
                seen.add(lid)
                merged.append(card)
        if len(merged) >= 2:
            return merged
        more = ctx.page.locator("#rl-feed-load-more")
        if more.count() and more.is_visible() and not more.is_disabled():
            more.click()
            ctx.page.wait_for_timeout(2500)
            continue
        ctx.page.evaluate(
            "document.getElementById('rl-feed-list')?.lastElementChild?.scrollIntoView()"
        )
        ctx.page.wait_for_timeout(800)
        if len(merged) == len(seen):
            break
    return merged


def _draft_rate_limited(ctx: JourneyCtx) -> str | None:
    """429 на draft POST — fail fast (O60b: DRAFT_HOURLY_LIMIT=0 на prod)."""
    draft_429 = [
        f
        for f in ctx.network_failures
        if f.get("status") == 429 and "/draft" in (f.get("url") or "")
    ]
    if draft_429:
        return (
            f"draft 429 ({len(draft_429)}×) — проверь DRAFT_HOURLY_LIMIT=0 на VPS "
            "(O60b)"
        )
    draft_net_err = [
        f
        for f in ctx.network_failures
        if f.get("status") == 0 and "/draft" in (f.get("url") or "")
    ]
    if draft_net_err:
        err = draft_net_err[-1].get("error") or "network error"
        return f"draft request failed: {err}"
    banner = _feed_error_visible(ctx)
    if banner:
        low = banner.casefold()
        if "rate limit" in low or "/час" in low or "429" in low:
            return banner[:240]
        if "недоступ" in low or "503" in low:
            return banner[:240]
    return None


def _wait_draft_text(ctx: JourneyCtx, card: Any) -> None:
    reply = card.locator("[data-reply-text]")
    clicked = False
    deadline = time.perf_counter() + (_DRAFT_TIMEOUT_MS / 1000)
    while time.perf_counter() < deadline:
        limited = _draft_rate_limited(ctx)
        if limited:
            raise RuntimeError(limited)
        banner = _feed_error_visible(ctx)
        if banner and "повтор" in banner.casefold():
            retry = ctx.page.locator(
                "#rl-feed-error .rl-feed-banner__retry, "
                "#rl-feed-error button:has-text('Повторить')"
            )
            if retry.count():
                retry.first.click()
                ctx.page.wait_for_timeout(500)
                clicked = False
        if reply.count():
            text = (reply.first.inner_text() or "").strip()
            if len(text) >= 40:
                return
        btn = card.locator(".rl-feed-card__reply-btn")
        if btn.count() and btn.is_visible() and not clicked:
            label = (btn.inner_text() or "").strip()
            if label == "Написать отклик" and not btn.is_disabled():
                btn.click()
                clicked = True
        ctx.page.wait_for_timeout(2000)
    raise RuntimeError("draft timeout: no reply text >= 40 chars")


def _run_journey(
    journey_id: str,
    title: str,
    severity_on_fail: str,
    fn: Callable[[JourneyCtx], None],
    ctx: JourneyCtx,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    shot_before = shot_after = None
    error = None
    passed = False
    try:
        shot_before = _screenshot(ctx, journey_id, "before")
        fn(ctx)
        err_banner = _feed_error_visible(ctx)
        if err_banner and journey_id.startswith("J") and journey_id in ("J2", "J3", "J4", "J5", "J6", "J10"):
            raise RuntimeError(f"feed error: {err_banner}")
        passed = True
    except Exception as exc:  # noqa: BLE001
        error = str(exc)
        ctx.add_finding(severity_on_fail, f"{title}: {error}", journey=journey_id)
    finally:
        try:
            shot_after = _screenshot(ctx, journey_id, "after")
        except Exception:  # noqa: BLE001
            pass
    ms = int((time.perf_counter() - t0) * 1000)
    return {
        "id": journey_id,
        "title": title,
        "pass": passed,
        "ms": ms,
        "error": error,
        "screenshots": {"before": shot_before, "after": shot_after},
        "console_errors": list(ctx.console_errors),
        "network_failures": list(ctx.network_failures),
    }


# --- Journeys ---


def j1_home(ctx: JourneyCtx) -> None:
    ctx.page.goto(f"{ctx.base}/", wait_until="domcontentloaded")
    ctx.page.wait_for_selector(".rl-hero", state="visible")
    preview = ctx.page.locator("#rl-live-preview-cards")
    preview.wait_for(state="visible")
    ctx.page.wait_for_function(
        """
        () => {
          const box = document.getElementById('rl-live-preview-cards');
          if (!box) return false;
          const cards = box.querySelectorAll('.rl-lead-card');
          if (cards.length < 3) return false;
          const text = box.innerText || '';
          if (box.classList.contains('rl-live-preview__cards--demo')) {
            return ['42', '100', '67'].every(function (p) {
              return text.indexOf(p) >= 0;
            });
          }
          var withPct = 0;
          cards.forEach(function (c) {
            if (/\\d+\\s*%/.test(c.innerText || '')) withPct++;
          });
          return withPct >= 3;
        }
        """,
        timeout=30_000,
    )
    cta = ctx.page.locator('a.rl-btn--primary[href*="/lenta"]', has_text=re.compile("Смотреть ленту"))
    if not cta.count():
        raise RuntimeError("CTA «Смотреть ленту» not found")
    with ctx.page.expect_navigation():
        cta.first.click()
    if "/lenta" not in ctx.page.url:
        raise RuntimeError(f"expected /lenta/, got {ctx.page.url}")


def j2_lenta_load(ctx: JourneyCtx) -> None:
    _goto_lenta(ctx)
    if _feed_error_visible(ctx):
        raise RuntimeError("error banner on load")
    ctx.page.wait_for_selector("#rl-feed-count", state="visible")


def j3_filters(ctx: JourneyCtx) -> None:
    _goto_lenta(ctx)
    ctx.page.locator("#filter-category-design input").check(force=True)
    ctx.page.wait_for_timeout(1200)
    count_text = ctx.page.locator("#rl-feed-count").inner_text()
    if "ошиб" in count_text.casefold():
        raise RuntimeError(f"count error: {count_text}")
    _open_skills_panel(ctx)
    chip = ctx.page.locator(
        "#rl-feed-skills .rl-feed-skill:not(.is-disabled), #rl-feed-skills .rl-chip"
    ).first
    chip.wait_for(state="visible", timeout=30_000)
    chip.click()
    ctx.page.locator("#rl-feed-skills-apply").click()
    ctx.page.wait_for_timeout(1200)
    if _feed_error_visible(ctx):
        raise RuntimeError("error after skills apply")


def j4_card_expand(ctx: JourneyCtx) -> None:
    _goto_lenta(ctx)
    card = ctx.page.locator("#rl-feed-list .rl-lead-card[data-id]").first
    card.wait_for(state="visible")
    card.locator(".rl-lead-card__title").first.click()
    ctx.page.wait_for_timeout(600)
    body = card.locator(".rl-feed-card__body-inner")
    body.wait_for(state="visible", timeout=15_000)
    inner = body.inner_text().casefold()
    if "суть" not in inner and "задан" not in inner:
        raise RuntimeError("task_summary section missing in expanded card")
    link = card.locator(".rl-feed-card__link", has_text=re.compile("Читать на бирже"))
    if not link.count() or not link.first.is_visible():
        raise RuntimeError("«Читать на бирже» not visible")
    card.locator(".rl-lead-card__title").first.click()
    ctx.page.wait_for_timeout(400)
    if "is-expanded" in (card.get_attribute("class") or ""):
        raise RuntimeError("card did not collapse")


def j5_draft_twice(ctx: JourneyCtx) -> None:
    _ensure_feed_draft_ready(ctx)
    cards = _cards_with_reply_btn(ctx)
    if len(cards) < 2:
        n_match = ctx.page.locator(
            "#rl-feed-list .rl-lead-card[data-id]"
        ).count()
        raise RuntimeError(
            f"Нужно 2 карточки с «Написать отклик» (вход + paid, km=0 OK); "
            f"найдено {len(cards)} (лидов в ленте: {n_match}). "
            "Войдите в TG или «Ещё лиды»."
        )
    ids: list[str] = []
    for card in cards[:6]:
        lid = card.get_attribute("data-id") or ""
        if lid and lid not in ids:
            ids.append(lid)
        if len(ids) >= 2:
            break
    if len(ids) < 2:
        raise RuntimeError("could not find 2 distinct lead ids")
    for idx, lid in enumerate(ids[:2]):
        card = ctx.page.locator(f'#rl-feed-list .rl-lead-card[data-id="{lid}"]').first
        card.scroll_into_view_if_needed()
        if not card.locator(".rl-feed-card__body-inner").count():
            card.locator(".rl-lead-card__title").first.click()
            ctx.page.wait_for_timeout(400)
        btn = card.locator(".rl-feed-card__reply-btn")
        if not btn.count():
            raise RuntimeError(f"lead {lid}: no reply button")
        btn.first.click()
        _wait_draft_text(ctx, card)
        if card.locator(".is-expanded").count():
            raise RuntimeError(f"lead {lid}: card should collapse after draft")
        ctx.add_finding("info", f"draft {idx + 1}/2 OK (lead {lid})", journey="J5")


def j6_draft_collapse(ctx: JourneyCtx) -> None:
    _ensure_feed_draft_ready(ctx)
    card = ctx.page.locator(
        "#rl-feed-list .rl-lead-card[data-id]:has([data-reply-text])"
    ).first
    if not card.count():
        ready = _cards_with_reply_btn(ctx)
        if not ready:
            raise RuntimeError("no card with draft to test collapse")
        card = ready[0]
        run_draft = card.locator(".rl-feed-card__reply-btn")
        if run_draft.count():
            run_draft.first.click()
            _wait_draft_text(ctx, card)
    if "is-expanded" in (card.get_attribute("class") or ""):
        card.locator(".rl-lead-card__title").first.click()
        ctx.page.wait_for_timeout(400)
    if "is-expanded" in (card.get_attribute("class") or ""):
        raise RuntimeError("expected collapsed card before re-expand")
    card.locator(".rl-lead-card__title").first.click()
    ctx.page.wait_for_timeout(500)
    card.locator(".rl-feed-card__body-inner").wait_for(state="visible", timeout=15_000)


def j7_cabinet_anon(ctx: JourneyCtx) -> None:
    ctx.page.goto(f"{ctx.base}/cabinet/", wait_until="domcontentloaded")
    ctx.page.wait_for_selector('[data-rl-app="cabinet"]', state="visible")
    ctx.page.wait_for_selector("#rl-cabinet-login", state="visible")
    title = ctx.page.locator(".rl-cabinet-login__title").inner_text().casefold()
    if "кабинет" not in title:
        raise RuntimeError("cabinet login block missing")
    nav = ctx.page.locator(".rl-header nav a, header nav a")
    if nav.count() < 2:
        raise RuntimeError("header nav links missing")


def j8_cabinet_logged(ctx: JourneyCtx) -> None:
    _wait_feed_logged_in(ctx)
    ctx.page.goto(f"{ctx.base}/cabinet/", wait_until="domcontentloaded")
    ctx.page.wait_for_selector('[data-rl-app="cabinet"]', state="visible", timeout=30_000)
    ctx.page.wait_for_timeout(2000)
    login = ctx.page.locator("#rl-cabinet-login")
    if login.count() and login.is_visible():
        has_token = ctx.page.evaluate(
            "() => !!(localStorage.getItem('rawlead_access_token') || '').trim()"
        )
        raise RuntimeError(
            "still on login gate"
            + (" (JWT в localStorage есть — обнови /cabinet/)" if has_token else "")
        )
    inbox = ctx.page.locator(
        "#rl-inbox-list .rl-inbox-card, #rl-inbox-list .rl-lead-card, .rl-cabinet-inbox .rl-lead-card"
    )
    inbox.first.wait_for(state="visible", timeout=45_000)
    card = inbox.first
    card.click()
    ctx.page.wait_for_timeout(800)
    draft = card.locator("[data-reply-text], .rl-feed-card__reply, .rl-inbox-card__reply")
    if draft.count():
        text = (draft.first.inner_text() or "").strip()
        if len(text) < 20:
            raise RuntimeError("inbox expand: draft text too short")
    else:
        body = card.locator(".rl-feed-card__body-inner, .rl-inbox-card__body")
        if not body.count() or not body.first.is_visible():
            raise RuntimeError("inbox card did not expand")


def j9_marketing(ctx: JourneyCtx) -> None:
    paths = ("/how/", "/pricing/", "/faq/", "/contact/")
    for path in paths:
        resp = ctx.page.goto(f"{ctx.base}{path}", wait_until="domcontentloaded")
        if resp and resp.status >= 400:
            raise RuntimeError(f"{path} HTTP {resp.status}")
        ctx.page.wait_for_load_state("domcontentloaded")
    ctx.page.goto(f"{ctx.base}/", wait_until="domcontentloaded")
    for label, path in (
        ("Как работает", "/how"),
        ("Тарифы", "/pricing"),
        ("Вопросы", "/faq"),
        ("Контакты", "/contact"),
    ):
        link = ctx.page.locator(f'.rl-footer__links a[href*="{path}"]')
        if not link.count():
            raise RuntimeError(f"footer link missing: {label}")


def j10_mobile_feed(ctx: JourneyCtx) -> None:
    j2_lenta_load(ctx)
    j3_filters(ctx)
    j4_card_expand(ctx)
    _ensure_feed_draft_ready(ctx)
    j5_draft_twice(ctx)
    j6_draft_collapse(ctx)


def _load_token_from_env_files() -> str | None:
    for name in (".env", ".env.site", ".env.local"):
        path = _ROOT / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("RAWLEAD_PREPROD_ACCESS_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _storage_state_has_auth(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if data.get("cookies"):
        return True
    for origin in data.get("origins") or []:
        for item in origin.get("localStorage") or []:
            if item.get("name") == "rawlead_access_token" and (item.get("value") or "").strip():
                return True
    return False


def _browser_report_label(browser_name: str, access_token: str | None) -> str:
    if access_token:
        return f"{browser_name}+token"
    return browser_name


def _has_auth(*, browser_name: str = "chromium", storage_state: Path | None = None) -> bool:
    if browser_name in ("yandex-profile", "cdp", "dolphin-cdp", "yandex-cdp"):
        return True
    st = storage_state or _DEFAULT_STORAGE
    if _storage_state_has_auth(st):
        return True
    return bool(
        os.environ.get("RAWLEAD_PREPROD_ACCESS_TOKEN", "").strip()
        or _load_token_from_env_files()
    )


def j11_fab(ctx: JourneyCtx) -> None:
    _goto_lenta(ctx)
    fab = ctx.page.locator("#rl-support-fab")
    fab.wait_for(state="visible")
    fab.click()
    modal = ctx.page.locator("#rl-support-modal")
    ctx.page.wait_for_function(
        "() => { const m = document.getElementById('rl-support-modal'); return m && !m.hidden; }",
        timeout=10_000,
    )
    if modal.get_attribute("hidden") is not None:
        raise RuntimeError("support modal still hidden")
    ctx.page.locator("#rl-support-close").click()
    ctx.page.wait_for_timeout(400)
    if modal.get_attribute("hidden") is None:
        raise RuntimeError("support modal did not close")


JOURNEYS: dict[str, tuple[str, str, Callable[[JourneyCtx], None]]] = {
    "J1": ("Главная", "critical", j1_home),
    "J2": ("Лента load", "critical", j2_lenta_load),
    "J3": ("Фильтры", "critical", j3_filters),
    "J4": ("Карточка expand", "critical", j4_card_expand),
    "J5": ("Draft ×2", "critical", j5_draft_twice),
    "J6": ("Draft collapse", "critical", j6_draft_collapse),
    "J7": ("ЛК anon", "critical", j7_cabinet_anon),
    "J8": ("ЛК logged", "warn", j8_cabinet_logged),
    "J9": ("Marketing", "critical", j9_marketing),
    "J10": ("Mobile 390", "critical", j10_mobile_feed),
    "J11": ("FAB support", "critical", j11_fab),
}


def _write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# O37-UX journey report",
        "",
        f"- **URL:** {report['base_url']}",
        f"- **Time:** {report['generated_at']}",
        f"- **PASS:** {report['pass']}",
        f"- **Critical:** {report['critical_count']}",
        f"- **Draft J5:** {report.get('j5_draft_ok', 'n/a')}",
        "",
        "## Journeys",
        "",
        "| ID | Title | Pass | ms | Error |",
        "|----|-------|------|-----|-------|",
    ]
    for r in report["results"]:
        err = (r.get("error") or "—").replace("|", "/").replace("\n", " ")
        lines.append(
            f"| {r['id']} | {r['title']} | {'✅' if r['pass'] else '❌'} | {r['ms']} | {err} |"
        )
    if report.get("findings"):
        lines.extend(["", "## Findings", ""])
        for f in report["findings"]:
            lines.append(f"- **{f['severity']}** [{f.get('journey', '')}] {f['message']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_journeys(
    base_url: str,
    *,
    headless: bool,
    timeout_ms: int,
    viewport: str,
    storage_state: Path | None,
    access_token: str | None,
    only: set[str] | None,
    browser_name: str = "chromium",
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    base = base_url.rstrip("/")
    mobile = viewport == "mobile"
    vp = {"width": 390, "height": 844} if mobile else {"width": 1280, "height": 900}

    results: list[dict[str, Any]] = []
    all_findings: list[dict[str, Any]] = []

    with sync_playwright() as p:
        browser, context = _launch_playwright_context(
            p,
            browser_name=browser_name,
            headless=headless,
            viewport=vp,
            storage_state=storage_state,
            access_token=access_token,
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(timeout_ms)
        ctx = JourneyCtx(
            base=base,
            page=page,
            profile_auth=browser_name
            in ("yandex-profile", "yandex-cdp", "cdp", "dolphin-cdp"),
            allow_manual_login=not headless,
        )
        _attach_observers(ctx)
        has_auth = _has_auth(browser_name=browser_name, storage_state=storage_state) or bool(
            access_token
        )
        if ctx.profile_auth:
            ctx.page.goto(f"{base}/lenta/", wait_until="domcontentloaded")
            has_auth = has_auth or _has_feed_token(ctx)
        journey_keys = list(JOURNEYS.keys())
        if only:
            journey_keys = [k for k in journey_keys if k in only]
        elif mobile:
            journey_keys = ["J10"]
        else:
            journey_keys = [k for k in journey_keys if k != "J10"]
        if not has_auth and not headless:
            ctx.add_finding(
                "warn",
                "J5/J8: нужен вход в TG + paid (km=0 OK, O61). "
                "С --headed будет пауза для ручного входа.",
                journey="setup",
            )

        for jid in journey_keys:
            title, sev, fn = JOURNEYS[jid]
            if jid == "J8" and not has_auth and not ctx.profile_auth:
                results.append(
                    {
                        "id": jid,
                        "title": title,
                        "pass": True,
                        "ms": 0,
                        "error": None,
                        "skipped": "no auth — J8 optional",
                        "screenshots": {},
                        "console_errors": [],
                        "network_failures": [],
                    }
                )
                continue
            ctx.console_errors.clear()
            ctx.network_failures.clear()
            row = _run_journey(jid, title, sev, fn, ctx)
            results.append(row)
            all_findings.extend(ctx.findings)
            ctx.findings.clear()

        if browser_name in ("yandex-cdp", "cdp", "dolphin-cdp"):
            if browser is not None:
                browser.close()
        elif browser is not None:
            browser.close()
        else:
            context.close()

    j5_row = next((r for r in results if r["id"] == "J5"), None)
    j5_ran = j5_row is not None
    j5_ok = bool(j5_row and j5_row["pass"]) if j5_ran else None
    critical = sum(1 for f in all_findings if f["severity"] == "critical")
    passed = sum(1 for r in results if r["pass"])
    ok = critical == 0 and (not j5_ran or bool(j5_ok))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base,
        "browser": _browser_report_label(browser_name, access_token),
        "viewport": viewport,
        "storage_state": str(storage_state) if storage_state else None,
        "has_auth": has_auth,
        "journeys_total": len(results),
        "journeys_pass": passed,
        "critical_count": critical,
        "j5_draft_ok": j5_ok,
        "pass": ok,
        "results": results,
        "findings": all_findings,
        "artifacts_dir": str(_ARTIFACT_DIR.relative_to(_ROOT)),
    }


def save_storage_state(
    base_url: str, path: Path, *, headless: bool, browser_name: str
) -> int:
    """Один раз: войти в /cabinet/ вручную, Enter в терминале — сохранить state."""
    from playwright.sync_api import sync_playwright

    path.parent.mkdir(parents=True, exist_ok=True)
    base = base_url.rstrip("/")
    print(f"Откройте браузер → {base}/cabinet/ → TG Login → затем Enter здесь.")
    with sync_playwright() as p:
        browser, context = _launch_playwright_context(
            p,
            browser_name=browser_name,
            headless=headless,
            viewport={"width": 1280, "height": 900},
            storage_state=None,
            access_token=None,
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(f"{base}/cabinet/", wait_until="domcontentloaded")
        input("После входа (inbox виден) нажмите Enter… ")
        context.storage_state(path=str(path))
        if browser is not None:
            browser.close()
        else:
            context.close()
    print(f"Сохранено: {path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="O37-UX Playwright journeys J1–J11")
    parser.add_argument("--base-url", default="https://rawlead.ru")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument(
        "--browser",
        choices=("chromium", "yandex", "yandex-profile", "yandex-cdp", "cdp", "dolphin-cdp"),
        default="chromium",
        help="chromium | cdp/dolphin-cdp (DOLPHIN_CDP_URL) | yandex-cdp | yandex-profile",
    )
    parser.add_argument(
        "--cdp-url",
        default="",
        help="CDP endpoint (override DOLPHIN_CDP_URL), напр. http://127.0.0.1:9222",
    )
    parser.add_argument("--viewport", choices=("desktop", "mobile"), default="desktop")
    parser.add_argument("--timeout-ms", type=int, default=45_000)
    parser.add_argument("--storage-state", type=Path, default=_DEFAULT_STORAGE)
    parser.add_argument(
        "--journeys",
        help="Comma-separated IDs, e.g. J1,J5 (default: all; mobile mode = J10 only)",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=_ROOT / "data" / "preprod_ux_journey.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=_ROOT / "data" / "preprod_ux_journey.md",
    )
    parser.add_argument(
        "--save-storage-state",
        action="store_true",
        help="Интерактивно сохранить auth state в --storage-state (перед прогоном J5)",
    )
    args = parser.parse_args()

    if args.save_storage_state:
        try:
            return save_storage_state(
                args.base_url,
                args.storage_state,
                headless=not args.headed,
                browser_name=args.browser,
            )
        except ImportError:
            print(
                "playwright не установлен: pip install playwright && playwright install chromium",
                file=sys.stderr,
            )
            return 2

    only = None
    if args.journeys:
        only = {x.strip().upper() for x in args.journeys.split(",") if x.strip()}

    if args.cdp_url.strip():
        os.environ["DOLPHIN_CDP_URL"] = args.cdp_url.strip()

    token = (
        os.environ.get("RAWLEAD_PREPROD_ACCESS_TOKEN", "").strip()
        or _load_token_from_env_files()
        or None
    )
    storage = args.storage_state if args.storage_state else None
    if token and args.browser in ("chromium", "cdp", "dolphin-cdp"):
        storage = None

    try:
        report = run_journeys(
            args.base_url,
            headless=not args.headed,
            timeout_ms=args.timeout_ms,
            viewport=args.viewport,
            storage_state=storage,
            access_token=token,
            only=only,
            browser_name=args.browser,
        )
    except ImportError:
        print(
            "playwright не установлен: pip install playwright && playwright install chromium",
            file=sys.stderr,
        )
        return 2

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _write_markdown(report, args.output_md)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
