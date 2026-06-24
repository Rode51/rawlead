"""§ O37c: UX audit «как человек» — U1–U10 desktop+mobile + LLM human.md.

  .venv\\Scripts\\python.exe scripts\\preprod_playwright\\ux_audit.py --base-url https://rawlead.ru
  .venv\\Scripts\\python.exe scripts\\preprod_playwright\\ux_audit.py --browser chromium --headed

Требует: RAWLEAD_PREPROD_ACCESS_TOKEN (paid) · playwright · OpenRouter для human.md
"""

from __future__ import annotations

import argparse
import base64
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

_ROOT = Path(__file__).resolve().parent.parent.parent
_PLAYWRIGHT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_PLAYWRIGHT_DIR))

import feed_ui  # noqa: E402
import next_ui as nui  # noqa: E402
import ux_journey  # noqa: E402

_ARTIFACT_DIR = _ROOT / "data" / "preprod_ux_audit"
_DEFAULT_JSON = _ROOT / "data" / "preprod_ux_audit.json"
_DEFAULT_MD = _ROOT / "data" / "preprod_ux_audit.md"
_DEFAULT_HUMAN = _ROOT / "data" / "preprod_ux_audit_human.md"
_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_DRAFT_TIMEOUT_MS = 120_000

for _stream in (sys.stdout, sys.stderr):
    enc = getattr(_stream, "encoding", None) or ""
    if enc.lower() != "utf-8":
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass


@dataclass
class AuditCtx:
    base: str
    page: Any
    viewport: str
    width: int
    height: int
    is_mobile: bool
    access_token: str | None
    tier: str = "premium"
    console_errors: list[str] = field(default_factory=list)
    network_failures: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    draft_reviews: list[dict[str, Any]] = field(default_factory=list)
    draft_tools_lead_id: str | None = None

    def journey_ctx(self) -> ux_journey.JourneyCtx:
        return ux_journey.JourneyCtx(base=self.base, page=self.page)

    def add_finding(self, severity: str, message: str, *, scenario: str = "") -> None:
        self.findings.append(
            {"severity": severity, "scenario": scenario, "viewport": self.viewport, "message": message}
        )


def _home_is_next(page: Any) -> bool:
    return page.locator('[data-testid="header-logo"]').count() > 0


def _feed_is_next(page: Any) -> bool:
    return page.locator(nui.FEED_APP).count() > 0


def _benign_console_line(text: str) -> bool:
    low = text.casefold()
    if "favicon" in low:
        return True
    if "failed to load resource: the server responded with a status of 404" in low:
        return True
    if "429" in text:
        return True
    if "websocket" in low and "yandex" in low:
        return True
    if "mc.yandex.ru" in text:
        return True
    return nui._benign_console_error(text)


def _load_env_value(key: str) -> str | None:
    for name in (".env.site", ".env", ".env.local"):
        path = _ROOT / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(key, "").strip() or None


def _resolve_token(explicit: str | None) -> str | None:
    if explicit and explicit.strip():
        return explicit.strip()
    return (
        os.environ.get("RAWLEAD_PREPROD_ACCESS_TOKEN", "").strip()
        or ux_journey._load_token_from_env_files()
        or None
    )


def _require_token(token: str | None, *, browser: str) -> str:
    if token:
        return token
    print(
        "O37c: RAWLEAD_PREPROD_ACCESS_TOKEN обязателен (paid test user).\n"
        "См. docs/ops/PREPROD_ACCOUNTS.md — DevTools → localStorage rawlead_access_token → .env.site",
        file=sys.stderr,
    )
    raise SystemExit(2)


def _forbid_owner_browser_gate(browser: str, token: str | None) -> None:
    if browser in ("yandex-profile", "yandex-cdp") and not token:
        print(
            "O37c: gate запрещён только на yandex-cdp/profile без test token (c1 a1).",
            file=sys.stderr,
        )
        raise SystemExit(2)


def _attach_observers(ctx: AuditCtx) -> None:
    page = ctx.page

    def on_console(msg: Any) -> None:
        if msg.type == "error":
            text = msg.text or ""
            if _benign_console_line(text):
                return
            ctx.console_errors.append(f"[{msg.type}] {text}")

    def on_response(response: Any) -> None:
        status = response.status
        if status < 400:
            return
        url = response.url or ""
        if not any(x in url for x in ("/wp-json/rawlead", "/v1/feed", "/v1/me", "/draft")):
            return
        ctx.network_failures.append(
            {"status": status, "url": url, "method": response.request.method}
        )

    def on_request_failed(request: Any) -> None:
        url = request.url or ""
        if not any(x in url for x in ("/draft", "/wp-json/rawlead", "/v1/feed")):
            return
        error = str(request.failure or "")
        if "ERR_ABORTED" in error:
            return
        ctx.network_failures.append(
            {
                "status": 0,
                "url": url,
                "method": request.method,
                "error": error,
            }
        )

    page.on("console", on_console)
    page.on("response", on_response)
    page.on("requestfailed", on_request_failed)


def _shot(ctx: AuditCtx, scenario_id: str, phase: str) -> str:
    _ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"{scenario_id}_{ctx.viewport}_{phase}.png"
    path = _ARTIFACT_DIR / fname
    ctx.page.screenshot(path=str(path), full_page=False)
    return str(path.relative_to(_ROOT)).replace("\\", "/")


def _shot_named(ctx: AuditCtx, name: str) -> str:
    _ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    path = _ARTIFACT_DIR / f"{name}.png"
    ctx.page.screenshot(path=str(path), full_page=False)
    return str(path.relative_to(_ROOT)).replace("\\", "/")


_VENDOR_TOOL_RE = re.compile(
    r"\b(neon|telethon|aiogram|supabase|cursor|openrouter|gemini_deep_research)\b",
    re.I,
)


def _feed_error(ctx: AuditCtx) -> str | None:
    err = ctx.page.locator("#rl-feed-error:not([hidden])")
    if err.count() and err.is_visible():
        return (err.inner_text() or "")[:300]
    return None


def _wait_mobile_feed_sheet(page: Any) -> Any:
    open_btn = page.locator("#rl-feed-filters-open")
    open_btn.wait_for(state="visible")
    open_btn.click()
    page.wait_for_function(
        "() => { const s = document.getElementById('rl-feed-sheet'); return s && !s.hidden; }",
        timeout=10_000,
    )
    panel = page.locator(".rl-feed-sheet__panel")
    panel.wait_for(state="visible", timeout=10_000)
    return panel


def _expand_feed_card(card: Any, page: Any) -> None:
    if not card.locator(feed_ui.CARD_FRONT_BODY).count():
        card.locator(".rl-lead-card__title").first.click()
        page.wait_for_timeout(400)


def _card_tools_joined(card: Any) -> str:
    tools_el = card.locator(".rl-feed-card__tools li")
    parts: list[str] = []
    if tools_el.count():
        for ti in range(tools_el.count()):
            parts.append((tools_el.nth(ti).inner_text() or "").strip())
    return ", ".join(parts)


def _require_premium_token(ctx: AuditCtx) -> str:
    if not ctx.access_token:
        raise RuntimeError("RAWLEAD_PREPROD_ACCESS_TOKEN required")
    return ctx.access_token


def _reset_next_feed_all_category(ctx: AuditCtx) -> None:
    """Undo prior scenario filters (e.g. U2 design) so expand tests see full feed."""
    page = ctx.page
    if ctx.is_mobile:
        nui.open_mobile_filter_sheet(page)
        page.locator('[data-testid="sheet-cat-all"]').click()
        nui.apply_mobile_sheet(page)
    else:
        nui.click_category(page, "")


def _draftable_lead_ids(
    ctx: AuditCtx,
    need: int,
    *,
    min_need: int | None = None,
    prefer_high_match: bool = False,
) -> list[str]:
    token = _require_premium_token(ctx)
    return nui.draftable_lead_ids_for_e2e(
        token,
        base_url=ctx.base,
        need=need,
        min_need=min_need,
        prefer_high_match=prefer_high_match,
    )


def _card_by_lead_id(ctx: AuditCtx, lead_id: str) -> Any:
    return nui.expand_card_by_lead_id(ctx.page, lead_id)


def _card_draft_ready(card: Any) -> tuple[bool, str]:
    """Same gates as U5: draft ≥40, no tools placeholder, no vendor lock."""
    reply = card.locator("[data-reply-text]")
    text = (reply.first.inner_text() or "").strip() if reply.count() else ""
    if len(text) < 40:
        return False, text or "draft text too short"
    body = card.inner_text().casefold()
    if "появится после генерации" in body:
        return False, "tools placeholder «появится после генерации»"
    if _VENDOR_TOOL_RE.search(_card_tools_joined(card)):
        return False, "vendor lock in tools"
    return True, text


def _ensure_premium_draft(jctx: ux_journey.JourneyCtx, card: Any, page: Any) -> str:
    """Expand card, reuse existing draft or click «Написать отклик» (U5 logic)."""
    _expand_feed_card(card, page)
    ok, detail = _card_draft_ready(card)
    if ok:
        return detail
    btn = card.locator(".rl-feed-card__reply-btn")
    if not btn.count():
        raise RuntimeError(detail)
    btn.first.click()
    ux_journey._wait_draft_text(jctx, card)
    ok, detail = _card_draft_ready(card)
    if not ok:
        raise RuntimeError(detail)
    return detail


def _tap_cabinet_skills_backdrop(page: Any) -> None:
    feed_ui.tap_cabinet_skills_backdrop(page)


def _run_scenario(
    scenario_id: str,
    title: str,
    severity_on_fail: str,
    fn: Callable[[AuditCtx], None],
    ctx: AuditCtx,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    shot_before = shot_after = None
    error = None
    passed = False
    try:
        shot_before = _shot(ctx, scenario_id, "before")
        fn(ctx)
        passed = True
    except Exception as exc:  # noqa: BLE001
        error = str(exc)
        ctx.add_finding(severity_on_fail, f"{title}: {error}", scenario=scenario_id)
    finally:
        try:
            shot_after = _shot(ctx, scenario_id, "after")
        except Exception:  # noqa: BLE001
            pass
    ms = int((time.perf_counter() - t0) * 1000)
    return {
        "id": scenario_id,
        "title": title,
        "viewport": ctx.viewport,
        "pass": passed,
        "ms": ms,
        "error": error,
        "screenshots": {"before": shot_before, "after": shot_after},
    }


# --- U1–U10 ---


def u1_header_footer(ctx: AuditCtx) -> None:
    base = ctx.base
    page = ctx.page
    page.goto(f"{base}/", wait_until="domcontentloaded")
    if _home_is_next(page):
        page.locator('[data-testid="header-logo"]').click()
        page.wait_for_url(re.compile(r"/$|/\?"), timeout=15_000)
        if ctx.is_mobile:
            page.goto(f"{base}/lenta/", wait_until="domcontentloaded")
        else:
            page.locator('[data-testid="header-nav-lenta"]').click()
            page.wait_for_url(re.compile(r"/lenta"), timeout=15_000)
        cabinet = page.locator('[data-testid="header-cabinet"], a[href*="/cabinet"]')
        if not cabinet.count():
            page.goto(f"{base}/", wait_until="domcontentloaded")
            cabinet = page.locator('a[href*="/cabinet"]')
        if not cabinet.count():
            raise RuntimeError("cabinet link missing in header/footer")
        for path in ("/how/", "/pricing/", "/faq/", "/contact/"):
            resp = page.goto(f"{base}{path}", wait_until="domcontentloaded")
            if resp and resp.status >= 400:
                raise RuntimeError(f"{path} HTTP {resp.status}")
        return

    page.wait_for_selector(".rl-hero", state="visible")

    page.locator("a.rl-logo").first.click()
    page.wait_for_url(re.compile(r"/$|/\?"), timeout=15_000)

    if ctx.is_mobile:
        page.locator("#rl-burger").click()
        page.wait_for_function(
            "() => { const d = document.getElementById('rl-nav-drawer'); return d && !d.hidden; }",
            timeout=10_000,
        )
        page.locator('.rl-nav-drawer__link[href*="/lenta"]').first.click()
    else:
        lenta = page.locator('.rl-header__link[href*="/lenta"]')
        if not lenta.count():
            raise RuntimeError("header «Лента» missing")
        lenta.first.click()
    page.wait_for_url(re.compile(r"/lenta"), timeout=15_000)

    cabinet_link = page.locator(
        'a.rl-header__login[href*="/cabinet"], a.rl-header__user[href*="/cabinet"], '
        '.rl-footer__links a[href*="/cabinet"], .rl-nav-drawer__link[href*="/cabinet"]'
    )
    if not cabinet_link.count():
        raise RuntimeError("cabinet link missing in header/footer")
    href = cabinet_link.first.get_attribute("href") or ""
    if "/cabinet" not in href:
        raise RuntimeError(f"bad cabinet href: {href}")

    page.goto(f"{base}/", wait_until="domcontentloaded")
    for path in ("/how/", "/pricing/", "/faq/", "/contact/"):
        resp = page.goto(f"{base}{path}", wait_until="domcontentloaded")
        if resp and resp.status >= 400:
            raise RuntimeError(f"{path} HTTP {resp.status}")


def u2_lenta_skills(ctx: AuditCtx) -> None:
    feed_ui.goto_lenta(ctx.page, ctx.base)
    if _feed_is_next(ctx.page):
        tier = ctx.tier or nui.wait_feed_tier(ctx.page, "anon", "free", "premium")
        if ctx.is_mobile:
            nui.open_mobile_filter_sheet(ctx.page)
            ctx.page.locator('[data-testid="sheet-cat-design"]').click()
            nui.apply_mobile_sheet(ctx.page)
        else:
            nui.click_category(ctx.page, "design")
        page = ctx.page
        app = page.locator(nui.FEED_APP)
        if app.count():
            text = (app.inner_text() or "")[:400]
            if "не удалось загрузить ленту" in text.casefold():
                raise RuntimeError(f"feed error: {text[:200]}")
        return
    tier = ctx.tier or feed_ui.wait_feed_tier(ctx.page, "anon", "free", "premium")
    feed_ui.apply_category_design(ctx.page, is_mobile=ctx.is_mobile)
    if _feed_error(ctx):
        raise RuntimeError("error banner after category chip")
    if tier == "anon":
        if ctx.is_mobile:
            return  # mobile: навыки в sheet/modal gated JS-ом
        if not feed_ui.is_filter_locked(ctx.page, "skills"):
            raise RuntimeError("anon: skills filter should be locked")
        return
    feed_ui.open_skills_modal(ctx.page, is_mobile=ctx.is_mobile)
    feed_ui.pick_first_skill_chip(ctx.page)
    feed_ui.apply_skills_modal(ctx.page)
    if _feed_error(ctx):
        raise RuntimeError("error banner after skills apply")
    after = feed_ui.feed_meta_text(ctx.page)
    if "ошиб" in after.casefold():
        raise RuntimeError(f"feed count error: {after}")


def _u3_sort_next_premium(ctx: AuditCtx) -> None:
    page = ctx.page
    if ctx.is_mobile:
        nui.open_mobile_filter_sheet(page)
        page.get_by_role("button", name="По совместимости").click()
        nui.apply_mobile_sheet(page)
        page.wait_for_selector(nui.FEED_SHEET, state="hidden", timeout=10_000)
        return
    page.locator('[data-testid="feed-filter-dropdown"]').click()
    panel = page.locator('[data-testid="feed-sort-panel"]')
    panel.wait_for(state="visible", timeout=10_000)
    page.get_by_role("button", name="По совм.").click()
    panel.get_by_role("button", name="Применить").click()
    page.wait_for_timeout(600)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    if panel.is_visible():
        page.mouse.click(8, 8)
        page.wait_for_timeout(400)
    if panel.is_visible():
        raise RuntimeError("sort dropdown did not close (Esc / tap outside)")


def u3_sort_dropdown(ctx: AuditCtx) -> None:
    feed_ui.goto_lenta(ctx.page, ctx.base)
    if _feed_is_next(ctx.page):
        tier = ctx.tier or nui.wait_feed_tier(ctx.page, "anon", "free", "premium")
        if tier == "anon":
            if ctx.is_mobile:
                nui.open_mobile_filter_sheet(ctx.page)
                if not ctx.page.locator('[data-testid="sheet-cat-all"]').count():
                    raise RuntimeError("mobile sheet: category filters missing")
                nui.apply_mobile_sheet(ctx.page)
            return
        if tier == "free":
            return
        _u3_sort_next_premium(ctx)
        return
    tier = ctx.tier or feed_ui.get_feed_tier(ctx.page)
    if tier == "anon":
        if ctx.is_mobile:
            sheet = feed_ui.open_mobile_feed_sheet(ctx.page)
            if not sheet.locator('input[name="category"]').count():
                raise RuntimeError("mobile sheet: category filters missing")
            ctx.page.locator(feed_ui.MOBILE_SHEET_APPLY).click()
            ctx.page.wait_for_timeout(800)
            return
        if not feed_ui.is_filter_locked(ctx.page, "sort"):
            raise RuntimeError("anon: sort filter should be locked")
        return
    if tier == "free":
        if ctx.is_mobile:
            sheet = feed_ui.open_mobile_feed_sheet(ctx.page)
            time_radio = sheet.locator(f'{feed_ui.SORT_RADIO_MOBILE}[value="time"]')
            if not time_radio.count():
                raise RuntimeError("free mobile: time sort radio missing")
            time_radio.first.click(force=True)
            ctx.page.locator(feed_ui.MOBILE_SHEET_APPLY).click()
            ctx.page.wait_for_timeout(800)
            return
        sort_dd = ctx.page.locator(feed_ui.SORT_DD)
        sort_dd.locator("summary").click()
        time_radio = ctx.page.locator(f'{feed_ui.SORT_RADIO_DESKTOP}[value="time"]')
        if not time_radio.count():
            raise RuntimeError("free desktop: time sort radio missing")
        time_radio.first.check(force=True)
        ctx.page.locator("#rl-feed-sort-apply").click()
        ctx.page.wait_for_timeout(600)
        return
    if ctx.is_mobile:
        feed_ui.apply_sort_match(ctx.page, is_mobile=True)
        feed_ui.close_mobile_sheet_overlay(ctx.page)
        if ctx.page.evaluate(
            "() => { const s = document.getElementById('rl-feed-sheet'); return s && !s.hidden; }"
        ):
            raise RuntimeError("mobile sheet did not close")
        return
    sort_dd = ctx.page.locator(feed_ui.SORT_DD)
    sort_dd.locator("summary").click()
    if not sort_dd.evaluate("el => el.open"):
        raise RuntimeError("sort dropdown did not open")
    match = ctx.page.locator(f'{feed_ui.SORT_RADIO_DESKTOP}[value="match"]')
    if not match.count():
        raise RuntimeError("desktop: rl-feed-sort match radio missing")
    match.first.check(force=True)
    ctx.page.wait_for_timeout(600)
    ctx.page.keyboard.press("Escape")
    ctx.page.wait_for_timeout(400)
    if sort_dd.evaluate("el => el.open"):
        ctx.page.mouse.click(8, 8)
        ctx.page.wait_for_timeout(400)
    if sort_dd.evaluate("el => el.open"):
        raise RuntimeError("sort dropdown did not close (Esc / tap outside)")


def u4_card_tap_outside(ctx: AuditCtx) -> None:
    feed_ui.goto_lenta(ctx.page, ctx.base)
    if _feed_is_next(ctx.page):
        if ctx.access_token:
            nui.bootstrap_preprod_feed(ctx.page, ctx.base, ctx.access_token)
        _reset_next_feed_all_category(ctx)
        nui.wait_feed_card_count(ctx.page, 2, timeout_ms=60_000)
        c1 = nui.expand_card_at(ctx.page, 0)
        if not nui.card_body_visible(c1):
            raise RuntimeError("card 1 did not expand")
        c2 = nui.expand_card_at(ctx.page, 1)
        if nui.card_body_visible(c1):
            raise RuntimeError("card 1 should collapse when card 2 opens")
        if not nui.card_body_visible(c2):
            raise RuntimeError("card 2 did not expand")
        return
    card = ctx.page.locator(feed_ui.FEED_CARD).first
    card.wait_for(state="visible")
    feed_ui.collapse_card_tap_outside(card, ctx.page)


def u5_draft_tools(ctx: AuditCtx) -> None:
    jctx = ctx.journey_ctx()
    feed_ui.goto_lenta(ctx.page, ctx.base)
    if _feed_is_next(ctx.page):
        token = _require_premium_token(ctx)
        nui.bootstrap_preprod_feed(ctx.page, ctx.base, token)
        _reset_next_feed_all_category(ctx)
        nui.wait_feed_card_count(ctx.page, 1, timeout_ms=60_000)
        last_err = "no draftable card with draft/tools"
        for lid in _draftable_lead_ids(ctx, need=12, min_need=1):
            try:
                card = _card_by_lead_id(ctx, lid)
                _ensure_premium_draft(jctx, card, ctx.page)
                ctx.draft_tools_lead_id = lid
                return
            except RuntimeError as exc:
                last_err = str(exc)
                continue
        raise RuntimeError(last_err)

    ux_journey._wait_feed_logged_in(jctx)
    ux_journey._wait_effective_access(jctx)
    ctx.page.wait_for_selector("#rl-feed-list .rl-lead-card[data-id]", timeout=45_000)

    pool = ctx.page.locator("#rl-feed-list .rl-lead-card[data-id]")
    n_pool = min(pool.count(), 12)
    last_err = "no card with draft/tools"
    for i in range(n_pool):
        card = pool.nth(i)
        card.scroll_into_view_if_needed()
        try:
            _ensure_premium_draft(jctx, card, ctx.page)
            ctx.draft_tools_lead_id = card.get_attribute("data-id") or None
            return
        except RuntimeError as exc:
            last_err = str(exc)
            continue
    raise RuntimeError(last_err)


def u6_fab_modal(ctx: AuditCtx) -> None:
    jctx = ctx.journey_ctx()
    ux_journey._goto_lenta(jctx)
    if _feed_is_next(ctx.page):
        fab = ctx.page.locator(nui.SUPPORT_FAB)
        fab.wait_for(state="visible")
        fab.click()
        ctx.page.wait_for_timeout(400)
        backdrop = ctx.page.locator("div.fixed.inset-0.z-40")
        if backdrop.count():
            backdrop.first.click(force=True)
        else:
            fab.click()
        ctx.page.wait_for_timeout(500)
        if fab.get_attribute("class") and "rl-support-fab--open" in (fab.get_attribute("class") or ""):
            raise RuntimeError("support modal did not close on overlay tap")
        return
    fab = ctx.page.locator("#rl-support-fab")
    fab.wait_for(state="visible")
    fab.click()
    modal = ctx.page.locator("#rl-support-modal")
    ctx.page.wait_for_function(
        "() => { const m = document.getElementById('rl-support-modal'); return m && !m.hidden; }",
        timeout=10_000,
    )
    overlay = ctx.page.locator("#rl-support-overlay")
    overlay.click(force=True)
    ctx.page.wait_for_timeout(500)
    if modal.get_attribute("hidden") is None:
        raise RuntimeError("support modal did not close on overlay tap")


def u7_cabinet_skills_inbox(ctx: AuditCtx) -> None:
    if ctx.access_token:
        nui.inject_token(ctx.page, ctx.access_token, base=ctx.base)
        nui.goto_path(ctx.page, ctx.base, "/cabinet/")
        if ctx.page.locator('[data-testid="cabinet-app"]').count():
            ctx.page.wait_for_function(
                """() => {
                  const app = document.querySelector('#rl-cabinet-app');
                  const panel = document.querySelector('[data-testid="cabinet-login-panel"]');
                  const spin = document.querySelector('.animate-spin');
                  return !!app && !panel && !spin;
                }""",
                timeout=45_000,
            )
            if not ctx.page.get_by_role("heading", name="Мои отклики").count():
                raise RuntimeError("cabinet inbox section missing")
            cards = ctx.page.locator("article")
            if cards.count():
                cards.first.click()
                ctx.page.wait_for_timeout(800)
                body = cards.first.locator('[data-reply-text], p')
                if not body.count():
                    raise RuntimeError("inbox card did not expand")
            return
    jctx = ctx.journey_ctx()
    ux_journey._wait_feed_logged_in(jctx)
    ctx.page.goto(f"{ctx.base}/cabinet/", wait_until="domcontentloaded")
    ctx.page.wait_for_selector("#rl-cabinet-app", state="visible", timeout=30_000)
    ctx.page.wait_for_timeout(2000)
    login = ctx.page.locator("#rl-cabinet-login")
    if login.count() and login.is_visible():
        raise RuntimeError("cabinet still on login gate with token")

    picker = ctx.page.locator(
        "#rl-cabinet-tag-add, #rl-cabinet-change-skills, #rl-cabinet-add-first"
    ).first
    picker.wait_for(state="visible", timeout=30_000)
    picker.click()
    ctx.page.wait_for_function(
        "() => { const m = document.getElementById('rl-cabinet-skills-modal'); return m && !m.hidden; }",
        timeout=10_000,
    )
    _tap_cabinet_skills_backdrop(ctx.page)
    ctx.page.wait_for_timeout(500)
    if ctx.page.evaluate(
        "() => { const m = document.getElementById('rl-cabinet-skills-modal'); return m && !m.hidden; }"
    ):
        raise RuntimeError("cabinet skills modal did not close on overlay tap")

    inbox = ctx.page.locator(
        "#rl-inbox-list .rl-inbox-card, #rl-inbox-list .rl-lead-card, #rl-cabinet-list .rl-lead-card"
    )
    inbox.first.wait_for(state="visible", timeout=45_000)
    card = inbox.first
    card.click()
    ctx.page.wait_for_timeout(800)
    expanded = card.locator(
        ".rl-feed-card__body-inner, .rl-inbox-card__body, [data-reply-text]"
    )
    if not expanded.count() or not expanded.first.is_visible():
        raise RuntimeError("inbox card did not expand")


def u8_mobile_skills_sheet(ctx: AuditCtx) -> None:
    if not ctx.is_mobile:
        return
    feed_ui.goto_lenta(ctx.page, ctx.base)
    page = ctx.page
    tier = ctx.tier or feed_ui.get_feed_tier(page)
    overflow_x = page.evaluate(
        "() => Math.max(0, document.documentElement.scrollWidth - window.innerWidth)"
    )
    if overflow_x > 8:
        ctx.add_finding(
            "critical",
            f"horizontal page scroll {overflow_x}px before skills sheet",
            scenario="U8",
        )
    sheet = feed_ui.open_mobile_feed_sheet(page)
    apply_btn = sheet.locator(feed_ui.MOBILE_SHEET_APPLY)
    apply_btn.wait_for(state="visible", timeout=10_000)
    if tier != "anon":
        skills_open = page.locator(feed_ui.MOBILE_SKILLS_OPEN)
        if skills_open.count():
            skills_open.first.click()
            feed_ui.pick_first_skill_chip(page)
            feed_ui.apply_skills_modal(page)
    apply_btn.click()
    page.wait_for_timeout(1500)
    if page.evaluate(
        "() => { const s = document.getElementById('rl-feed-sheet'); return s && !s.hidden; }"
    ):
        raise RuntimeError("sheet did not close after «Применить»")
    overflow_after = page.evaluate(
        "() => Math.max(0, document.documentElement.scrollWidth - window.innerWidth)"
    )
    if overflow_after > 8:
        raise RuntimeError(f"horizontal page scroll {overflow_after}px after skills sheet")


def u9_marketing_cta(ctx: AuditCtx) -> None:
    page = ctx.page
    for path in ("/how/", "/pricing/"):
        page.goto(f"{ctx.base}{path}", wait_until="domcontentloaded")
        cta = page.locator('a.rl-btn--primary[href*="/lenta"], a[href*="/lenta/"], a[href*="/cabinet"]')
        if not cta.count():
            raise RuntimeError(f"{path}: no CTA to /lenta/ or /cabinet/")
        href = cta.first.get_attribute("href") or ""
        if "/lenta" not in href and "/cabinet" not in href:
            raise RuntimeError(f"{path}: CTA href unexpected: {href}")


def u10_console_network(ctx: AuditCtx) -> None:
    errors = []
    for e in ctx.console_errors:
        if not e.startswith("[error]"):
            continue
        text = e.removeprefix("[error] ").strip()
        if _benign_console_line(text):
            continue
        errors.append(e)
    if errors:
        raise RuntimeError(f"console errors: {errors[:3]}")
    bad = [
        f
        for f in ctx.network_failures
        if f.get("status", 0) >= 400 and f.get("status") not in (429,)
    ]
    bad = [
        f
        for f in bad
        if not (
            f.get("status") == 404
            and any(
                x in (f.get("url") or "")
                for x in nui._BENIGN_HTTP_404_PARTS
            )
        )
    ]
    feed_draft = [
        f
        for f in bad
        if any(x in (f.get("url") or "") for x in ("/feed", "/draft", "/wp-json/rawlead"))
    ]
    if feed_draft:
        sample = feed_draft[:3]
        raise RuntimeError(f"API feed/draft failures: {sample}")


def u10b_draft_tools_batch(ctx: AuditCtx) -> None:
    """O80: «Написать отклик» до 3 карточек — блоки Инструменты + Черновик."""
    jctx = ctx.journey_ctx()
    feed_ui.goto_lenta(ctx.page, ctx.base)
    if _feed_is_next(ctx.page):
        token = _require_premium_token(ctx)
        nui.bootstrap_preprod_feed(ctx.page, ctx.base, token)
        _reset_next_feed_all_category(ctx)
        nui.wait_feed_card_count(ctx.page, 1, timeout_ms=60_000)
        lead_ids = _draftable_lead_ids(ctx, need=12, min_need=3, prefer_high_match=True)
        pending_ids: list[str] = []
        ready_ids: list[str] = []
        for lid in lead_ids:
            card = ctx.page.locator(f'{nui.FEED_CARD}[data-id="{lid}"]')
            if not card.count():
                pending_ids.append(lid)
                continue
            card.first.scroll_into_view_if_needed()
            _expand_feed_card(card.first, ctx.page)
            ok, _ = _card_draft_ready(card.first)
            (ready_ids if ok else pending_ids).append(lid)
        ordered_ids = pending_ids + ready_ids
        reviewed = 0
        for lid in ordered_ids:
            if reviewed >= 3:
                break
            if reviewed > 0:
                ctx.page.wait_for_timeout(35_000)
            card = _card_by_lead_id(ctx, lid)
            lead_id = lid
            card.scroll_into_view_if_needed()
            try:
                draft_text = _ensure_premium_draft(jctx, card, ctx.page)
            except RuntimeError as exc:
                msg = str(exc).casefold()
                if "rate limit" in msg or "/час" in msg:
                    if reviewed >= 3:
                        break
                    continue
                if "недоступ" in msg or "timeout" in msg or "429" in msg:
                    continue
                raise

            tools_list: list[str] = []
            tools_el = card.locator(".rl-feed-card__tools li")
            if tools_el.count():
                for ti in range(tools_el.count()):
                    tools_list.append((tools_el.nth(ti).inner_text() or "").strip())

            reviewed += 1
            section = card.locator(".rl-feed-card__section").first
            if section.count():
                section.first.scroll_into_view_if_needed()
            shot_tools = _shot_named(ctx, f"U10b_{ctx.viewport}_card{reviewed}_tools")
            shot_draft = _shot_named(ctx, f"U10b_{ctx.viewport}_card{reviewed}_draft")

            ctx.draft_reviews.append(
                {
                    "lead_id": lead_id,
                    "index": reviewed,
                    "tools": tools_list,
                    "draft_preview": draft_text[:500],
                    "screenshots": {"tools": shot_tools, "draft": shot_draft},
                }
            )
            ctx.page.wait_for_timeout(3000)

        if reviewed < 3:
            raise RuntimeError(f"U10b: only {reviewed}/3 drafts OK (AI fail on other cards)")
        return

    ux_journey._wait_feed_logged_in(jctx)
    ux_journey._wait_effective_access(jctx)
    ctx.page.wait_for_selector("#rl-feed-list .rl-lead-card[data-id]", timeout=45_000)

    pool = ctx.page.locator("#rl-feed-list .rl-lead-card[data-id]")
    n_pool = min(pool.count(), 15)
    ready: list[Any] = []
    pending: list[Any] = []
    for i in range(n_pool):
        card = pool.nth(i)
        card.scroll_into_view_if_needed()
        _expand_feed_card(card, ctx.page)
        btn = card.locator(".rl-feed-card__reply-btn")
        ok, _ = _card_draft_ready(card)
        if ok:
            ready.append(card)
        elif btn.count():
            pending.append(card)

    candidates = ready + pending
    if len(candidates) < 3:
        raise RuntimeError(f"U10b: need ≥3 draft cards, got {len(candidates)}")

    reviewed = 0
    for card in candidates:
        if reviewed >= 3:
            break
        lead_id = card.get_attribute("data-id") or str(reviewed + 1)
        card.scroll_into_view_if_needed()
        try:
            draft_text = _ensure_premium_draft(jctx, card, ctx.page)
        except RuntimeError as exc:
            msg = str(exc).casefold()
            if "rate limit" in msg or "/час" in msg:
                if reviewed >= 3:
                    break
                continue
            if "недоступ" in msg or "timeout" in msg or "429" in msg:
                continue
            raise

        tools_list: list[str] = []
        tools_el = card.locator(".rl-feed-card__tools li")
        if tools_el.count():
            for ti in range(tools_el.count()):
                tools_list.append((tools_el.nth(ti).inner_text() or "").strip())

        reviewed += 1
        section = card.locator(".rl-feed-card__section").first
        if section.count():
            section.first.scroll_into_view_if_needed()
        shot_tools = _shot_named(ctx, f"U10b_{ctx.viewport}_card{reviewed}_tools")
        shot_draft = _shot_named(ctx, f"U10b_{ctx.viewport}_card{reviewed}_draft")

        ctx.draft_reviews.append(
            {
                "lead_id": lead_id,
                "index": reviewed,
                "tools": tools_list,
                "draft_preview": draft_text[:500],
                "screenshots": {"tools": shot_tools, "draft": shot_draft},
            }
        )
        ctx.page.wait_for_timeout(3000)

    if reviewed < 3:
        raise RuntimeError(f"U10b: only {reviewed}/3 drafts OK (AI fail on other cards)")


def u11_match_breakdown(ctx: AuditCtx) -> None:
    """O82: tier-aware match block; no verdict chips."""
    feed_ui.goto_lenta(ctx.page, ctx.base)
    tier = ctx.tier or feed_ui.wait_feed_tier(ctx.page, "anon", "free", "premium")
    ctx.page.wait_for_selector(feed_ui.FEED_CARD, timeout=45_000)
    pool = ctx.page.locator(feed_ui.FEED_CARD)
    n = min(3, pool.count())
    if n < 1:
        raise RuntimeError("U11: no feed cards")
    for i in range(n):
        card = pool.nth(i)
        card.scroll_into_view_if_needed()
        feed_ui.assert_match_for_tier(card, tier)


def u12_tools_auth_only(ctx: AuditCtx) -> None:
    """O83: anon/free — no tools; premium — tools section after draft (WP) or draft CTA (Next)."""
    tier = ctx.tier or "premium"
    feed_ui.goto_lenta(ctx.page, ctx.base)
    if _feed_is_next(ctx.page):
        if tier != "premium" or not ctx.access_token:
            nui.wait_feed_tier(ctx.page, "anon", "free", timeout_ms=45_000)
            for i in range(min(3, nui.feed_card_count(ctx.page))):
                card = ctx.page.locator(nui.FEED_CARD).nth(i)
                text = (card.inner_text() or "").casefold()
                if "инструменты" in text:
                    raise RuntimeError("U12: anon/free sees «Инструменты» without premium draft")
            return
        nui.bootstrap_preprod_feed(ctx.page, ctx.base, ctx.access_token, timeout_ms=45_000)
        if ctx.is_mobile:
            nui.open_mobile_filter_sheet(ctx.page)
            ctx.page.locator('[data-testid="sheet-cat-all"]').click()
            nui.apply_mobile_sheet(ctx.page)
        else:
            nui.click_category(ctx.page, "")
        ctx.page.wait_for_timeout(1000)
        if nui.feed_card_count(ctx.page) < 1:
            raise RuntimeError("U12: no feed cards")
        card = nui.expand_card_at(ctx.page, 0)
        draft = card.locator(nui.FEED_DRAFT_TEXT)
        reply_btn = card.locator('[data-testid="feed-card-cta"]')
        if draft.count() and (draft.first.inner_text() or "").strip():
            return
        if reply_btn.count():
            return
        raise RuntimeError("U12: premium — no draft CTA on expanded card")
    jctx = ctx.journey_ctx()
    if tier == "premium" and ctx.access_token:
        ux_journey._wait_feed_logged_in(jctx)
        ux_journey._wait_effective_access(jctx)
        ctx.page.wait_for_selector(feed_ui.FEED_CARD, timeout=45_000)

        if ctx.draft_tools_lead_id:
            card = ctx.page.locator(
                f'{feed_ui.FEED_CARD}[data-id="{ctx.draft_tools_lead_id}"]'
            )
            if card.count():
                card.first.scroll_into_view_if_needed()
                _expand_feed_card(card.first, ctx.page)
                if card.first.locator(".rl-feed-card__tools li").count():
                    return
                if feed_ui.card_has_tools_section(card.first):
                    return

        pool = ctx.page.locator(feed_ui.FEED_CARD)
        for i in range(min(8, pool.count())):
            card = pool.nth(i)
            card.scroll_into_view_if_needed()
            _expand_feed_card(card, ctx.page)
            ok, _ = _card_draft_ready(card)
            if ok and (
                card.locator(".rl-feed-card__tools li").count()
                or feed_ui.card_has_tools_section(card)
            ):
                return
        raise RuntimeError("U12: premium — no «Инструменты» after draft")

    feed_ui.goto_lenta(ctx.page, ctx.base)
    if tier == "free" and ctx.access_token:
        feed_ui.wait_feed_tier(ctx.page, "free")
    ctx.page.wait_for_selector(feed_ui.FEED_CARD, timeout=45_000)
    pool = ctx.page.locator(feed_ui.FEED_CARD)
    for i in range(min(3, pool.count())):
        card = pool.nth(i)
        card.scroll_into_view_if_needed()
        if not card.locator(feed_ui.CARD_FRONT_BODY).count():
            feed_ui.expand_card(card, ctx.page)
        if feed_ui.card_has_tools_section(card):
            raise RuntimeError("U12: anon/free sees «Инструменты» without premium draft")


SCENARIOS: dict[str, tuple[str, str, Callable[[AuditCtx], None]]] = {
    "U1": ("Header + footer links", "critical", u1_header_footer),
    "U2": ("Лента: категория + навыки", "critical", u2_lenta_skills),
    "U3": ("Сортировка + закрытие", "critical", u3_sort_dropdown),
    "U4": ("Expand + tap outside", "critical", u4_card_tap_outside),
    "U10b": ("Draft×3 tools audit", "critical", u10b_draft_tools_batch),
    "U11": ("Match breakdown", "critical", u11_match_breakdown),
    "U5": ("Draft + инструменты", "critical", u5_draft_tools),
    "U12": ("Tools auth-only", "critical", u12_tools_auth_only),
    "U6": ("FAB support modal", "warn", u6_fab_modal),
    "U7": ("ЛК: навыки + inbox", "critical", u7_cabinet_skills_inbox),
    "U8": ("Mobile bottom sheet", "critical", u8_mobile_skills_sheet),
    "U9": ("Marketing CTA", "critical", u9_marketing_cta),
    "U10": ("Console + network", "critical", u10_console_network),
}


def _write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Pre-prod UX audit (O37c)",
        "",
        f"- **URL:** {report['base_url']}",
        f"- **Time:** {report['generated_at']}",
        f"- **Browser:** {report['browser']}",
        f"- **Auth:** {report['has_auth']}",
        f"- **PASS:** {report['pass']}",
        f"- **Critical:** {report['critical_count']}",
        "",
        "## Scenarios",
        "",
        "| ID | Viewport | Title | Pass | ms | Error |",
        "|----|----------|-------|------|-----|-------|",
    ]
    for r in report["results"]:
        err = (r.get("error") or "—").replace("|", "/").replace("\n", " ")
        lines.append(
            f"| {r['id']} | {r['viewport']} | {r['title']} | "
            f"{'✅' if r['pass'] else '❌'} | {r['ms']} | {err} |"
        )
    if report.get("findings"):
        lines.extend(["", "## Findings", ""])
        for f in report["findings"]:
            lines.append(
                f"- **{f['severity']}** [{f.get('scenario', '')}/{f.get('viewport', '')}] {f['message']}"
            )
    lines.extend(
        [
            "",
            "## Human review",
            "",
            f"См. `{report.get('human_md', 'data/preprod_ux_audit_human.md')}` — LLM-слой (не авто-rating).",
            "",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _encode_image_b64(path: Path) -> str:
    return base64.standard_b64encode(path.read_bytes()).decode("ascii")


def _llm_human_review(
    report: dict[str, Any],
    *,
    out_path: Path,
    model: str,
    api_key: str,
) -> dict[str, Any]:
    mobile_shots: list[Path] = []
    for r in report["results"]:
        if r.get("viewport") != "mobile":
            continue
        for key in ("before", "after"):
            rel = (r.get("screenshots") or {}).get(key)
            if rel:
                p = _ROOT / rel.replace("/", os.sep)
                if p.is_file():
                    mobile_shots.append(p)
    # dedupe, cap 12 images
    seen: set[str] = set()
    unique: list[Path] = []
    for p in mobile_shots:
        s = str(p)
        if s not in seen:
            seen.add(s)
            unique.append(p)
    unique = unique[:12]

    findings_json = json.dumps(
        {
            "findings": report.get("findings", []),
            "failed": [r for r in report["results"] if not r["pass"]],
            "u8_ran_mobile": any(
                r["id"] == "U8" and r["viewport"] == "mobile" for r in report["results"]
            ),
            "draft_reviews": report.get("draft_reviews") or [],
        },
        ensure_ascii=False,
        indent=2,
    )

    draft_block = report.get("draft_reviews") or []
    draft_prompt = ""
    if draft_block:
        draft_prompt = (
            "\n\n## U10b — отклики и инструменты (до 5 карточек)\n"
            "Для **каждой** карточки в draft_reviews оцени:\n"
            "- **draft_as_is** 1–5 — отправил бы отклик as-is на FL?\n"
            "- **tools_too_narrow** да/нет — neon/telethon/aiogram/supabase/cursor в tools = **да (fail)**\n"
            "- **tools_match_tz** 1–5 — инструменты из ТЗ заказа, не стек исполнителя?\n"
            "В конце секция **## Draft/tools summary** со средним draft_as_is и count vendor-lock fails.\n"
        )

    user_parts: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "Ты UX-редактор RawLead (фриланс-лента). Оцени mobile-скрины и JSON findings.\n"
                "Вопросы: понятно ли куда жать? криво на 390px? перекрытия? мелкий tap target?\n"
                "Формат ответа — markdown с секциями:\n"
                "## Критично\n## Раздражает\n## Ок\n"
                + draft_prompt
                + "В конце: **Rating (1–5)** одной строкой — НЕ ставь 5/5 если U8 mobile не прогонялся или есть critical.\n\n"
                f"Findings JSON:\n```json\n{findings_json}\n```"
            ),
        }
    ]
    for review in draft_block:
        for key in ("tools", "draft"):
            rel = (review.get("screenshots") or {}).get(key)
            if not rel:
                continue
            p = _ROOT / rel.replace("/", os.sep)
            if p.is_file() and len(unique) < 12:
                unique.append(p)
    for p in unique:
        user_parts.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{_encode_image_b64(p)}"},
            }
        )

    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Отвечай по-русски. Будь честен — лучше critical, чем ложный PASS.",
            },
            {"role": "user", "content": user_parts},
        ],
        "temperature": 0.2,
        "max_tokens": 2500,
    }
    req = urllib.request.Request(
        _OPENROUTER_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://rawlead.ru",
            "X-Title": "RawLead O37c UX audit",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
        content = (
            "# UX audit human (LLM failed)\n\n"
            f"OpenRouter error: {exc}\n\n"
            "## Критично\n- LLM pass не выполнен — проверь AI_API_KEY в .env.site\n\n"
            "## Раздражает\n\n## Ок\n"
        )

    header = [
        "# Pre-prod UX audit — human (O80 LLM)",
        "",
        f"- **Time:** {report['generated_at']}",
        f"- **Model:** {model}",
        f"- **Mobile screenshots:** {len(unique)}",
        f"- **Script critical count:** {report['critical_count']}",
        f"- **U10b draft cards:** {len(report.get('draft_reviews') or [])}",
        "",
        "---",
        "",
    ]
    out_path.write_text("\n".join(header) + content.strip() + "\n", encoding="utf-8")
    rating_match = re.search(r"Rating.*?(\d)\s*/\s*5", content, re.I)
    return {
        "path": str(out_path.relative_to(_ROOT)).replace("\\", "/"),
        "model": model,
        "mobile_screenshots": len(unique),
        "llm_rating": int(rating_match.group(1)) if rating_match else None,
    }


def run_audit(
    base_url: str,
    *,
    headless: bool,
    browser_name: str,
    access_token: str | None,
    tier: str = "premium",
    timeout_ms: int = 45_000,
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    base = base_url.rstrip("/")
    viewports = (
        ("desktop", 1440, 900),
        ("mobile", 390, 844),
    )
    results: list[dict[str, Any]] = []
    all_findings: list[dict[str, Any]] = []
    all_draft_reviews: list[dict[str, Any]] = []

    with sync_playwright() as p:
        for vp_label, width, height in viewports:
            browser, context = ux_journey._launch_playwright_context(
                p,
                browser_name=browser_name,
                headless=headless,
                viewport={"width": width, "height": height},
                storage_state=None,
                access_token=access_token,
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(timeout_ms)
            ctx = AuditCtx(
                base=base,
                page=page,
                viewport=vp_label,
                width=width,
                height=height,
                is_mobile=vp_label == "mobile",
                access_token=access_token,
                tier=tier,
            )
            _attach_observers(ctx)
            if tier in ("free", "premium") and access_token:
                feed_ui.goto_lenta(page, base)
                if _feed_is_next(page):
                    if tier == "premium":
                        nui.bootstrap_preprod_feed(page, base, access_token, timeout_ms=60_000)
                    else:
                        nui.reload_with_token(page, base, access_token)
                        nui.wait_feed_tier(page, tier, timeout_ms=60_000)
                else:
                    feed_ui.wait_feed_tier(page, tier, timeout_ms=60_000)

            for sid, (title, sev, fn) in SCENARIOS.items():
                if sid == "U8" and vp_label != "mobile":
                    continue
                if sid == "U10b" and vp_label != "desktop":
                    continue
                if sid in ("U5", "U7", "U10b") and tier != "premium":
                    results.append(
                        {
                            "id": sid,
                            "title": title,
                            "viewport": vp_label,
                            "pass": True,
                            "ms": 0,
                            "error": None,
                            "skipped": True,
                            "skip_reason": f"tier={tier}",
                            "screenshots": {},
                        }
                    )
                    continue
                row = _run_scenario(sid, title, sev, fn, ctx)
                results.append(row)
                all_findings.extend(ctx.findings)
                if ctx.draft_reviews:
                    all_draft_reviews = list(ctx.draft_reviews)
                ctx.findings.clear()

            if browser_name in ("yandex-cdp", "cdp", "dolphin-cdp"):
                if browser is not None:
                    browser.close()
            elif browser is not None:
                browser.close()
            else:
                context.close()

    critical = sum(1 for f in all_findings if f["severity"] == "critical")
    passed = sum(1 for r in results if r["pass"])
    runnable = [r for r in results if not r.get("skipped")]
    ok = critical == 0 and all(r["pass"] for r in runnable)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base,
        "tier": tier,
        "browser": ux_journey._browser_report_label(browser_name, access_token),
        "has_auth": bool(access_token),
        "viewports": [v[0] for v in viewports],
        "scenarios_total": len(results),
        "scenarios_pass": passed,
        "critical_count": critical,
        "pass": ok,
        "results": results,
        "findings": all_findings,
        "draft_reviews": all_draft_reviews,
        "artifacts_dir": str(_ARTIFACT_DIR.relative_to(_ROOT)).replace("\\", "/"),
    }


def _remint_premium_token() -> None:
    """acc1 shared: после free mint подписка free — восстановить agent."""
    py = sys.executable
    script = _ROOT / "scripts" / "preprod_mint_token.py"
    r = subprocess.run(
        [py, str(script), "--account", "acc1", "--plan", "agent", "--write-env-site"],
        cwd=str(_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 0:
        raise RuntimeError(f"premium remint failed: {r.stderr or r.stdout}")


def _token_for_tier(tier: str) -> str | None:
    if tier == "anon":
        return None
    if tier == "free":
        return (
            os.environ.get("RAWLEAD_PREPROD_FREE_TOKEN", "").strip()
            or _load_env_value("RAWLEAD_PREPROD_FREE_TOKEN")
        )
    return _resolve_token(None)


def main() -> int:
    parser = argparse.ArgumentParser(description="O37c UX audit U1–U10 + LLM human")
    parser.add_argument("--base-url", default="https://rawlead.ru")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument(
        "--tier",
        default="premium",
        choices=("anon", "free", "premium", "all"),
        help="anon|free|premium или all (3 прогона Wave 1)",
    )
    parser.add_argument(
        "--browser",
        default="chromium",
        choices=("chromium", "cdp", "dolphin-cdp", "yandex-cdp"),
        help="default chromium+token (не yandex-profile для gate)",
    )
    parser.add_argument("--cdp-url", default="")
    parser.add_argument("--output-json", type=Path, default=_DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=_DEFAULT_MD)
    parser.add_argument("--output-human", type=Path, default=_DEFAULT_HUMAN)
    parser.add_argument("--skip-llm", action="store_true", help="dev only — без human.md LLM")
    parser.add_argument(
        "--llm-model",
        default="",
        help="OpenRouter model (default OPENROUTER_MODEL_PREMIUM or gemini-2.5-flash)",
    )
    args = parser.parse_args()

    if args.cdp_url.strip():
        os.environ["DOLPHIN_CDP_URL"] = args.cdp_url.strip()

    tiers = ("anon", "free", "premium") if args.tier == "all" else (args.tier,)
    combined: list[dict[str, Any]] = []
    exit_code = 0

    for tier in tiers:
        if tier == "premium" and "free" in tiers:
            _remint_premium_token()
        token = _token_for_tier(tier)
        if tier == "premium" and not token:
            token = _require_token(None, browser=args.browser)
        if tier == "free" and not token:
            print(
                "RAWLEAD_PREPROD_FREE_TOKEN не задан. "
                "Mint: preprod_mint_token.py --plan free "
                "--env-key RAWLEAD_PREPROD_FREE_TOKEN --write-env-site",
                file=sys.stderr,
            )
            return 2
        if tier == "premium":
            _forbid_owner_browser_gate(args.browser, token)

        out_json = args.output_json
        if args.tier == "all":
            out_json = _ROOT / "data" / f"preprod_ux_audit_{tier}.json"

        try:
            report = run_audit(
                args.base_url,
                headless=not args.headed,
                browser_name=args.browser,
                access_token=token,
                tier=tier,
            )
        except ImportError:
            print(
                "playwright не установлен: pip install playwright && playwright install chromium",
                file=sys.stderr,
            )
            return 2

        if tier == "premium" and not args.skip_llm:
            api_key = _load_env_value("AI_API_KEY") or _load_env_value("OPENROUTER_API_KEY")
            model = (
                args.llm_model.strip()
                or _load_env_value("OPENROUTER_MODEL_PREMIUM")
                or "google/gemini-2.5-flash"
            )
            human_path = args.output_human
            if args.tier == "all":
                human_path = _ROOT / "data" / f"preprod_ux_audit_{tier}_human.md"
            if api_key:
                llm_meta = _llm_human_review(
                    report, out_path=human_path, model=model, api_key=api_key
                )
                report["human_md"] = llm_meta["path"]
                report["llm"] = llm_meta
            else:
                stub = (
                    "# Pre-prod UX audit — human (O37c)\n\n"
                    "## Критично\n- AI_API_KEY не задан — LLM pass пропущен\n\n"
                    "## Раздражает\n\n## Ок\n\n**Rating:** n/a\n"
                )
                human_path.write_text(stub, encoding="utf-8")
                report["human_md"] = str(human_path.relative_to(_ROOT)).replace("\\", "/")
                report["llm"] = {"skipped": "no AI_API_KEY"}

        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        if tier == args.tier or tier == "premium":
            _write_markdown(report, args.output_md if tier == "premium" else out_json.with_suffix(".md"))
        print(
            json.dumps(
                {
                    "tier": report["tier"],
                    "pass": report["pass"],
                    "critical_count": report["critical_count"],
                    "scenarios_pass": report["scenarios_pass"],
                    "scenarios_total": report["scenarios_total"],
                },
                ensure_ascii=False,
            )
        )
        combined.append(report)
        if not report["pass"]:
            exit_code = 1

    if args.tier == "all":
        summary_path = _ROOT / "data" / "preprod_ux_audit_wave1.json"
        summary_path.write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wave1 summary → {summary_path}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
