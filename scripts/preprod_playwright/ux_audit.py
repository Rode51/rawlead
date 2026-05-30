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
    console_errors: list[str] = field(default_factory=list)
    network_failures: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)

    def journey_ctx(self) -> ux_journey.JourneyCtx:
        return ux_journey.JourneyCtx(base=self.base, page=self.page)

    def add_finding(self, severity: str, message: str, *, scenario: str = "") -> None:
        self.findings.append(
            {"severity": severity, "scenario": scenario, "viewport": self.viewport, "message": message}
        )


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
            if "favicon" in text.casefold():
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


def _tap_cabinet_skills_backdrop(page: Any) -> None:
    overlay = page.locator("#rl-cabinet-skills-modal-overlay")
    box = overlay.bounding_box()
    if box:
        page.mouse.click(box["x"] + 8, box["y"] + 8)
    else:
        page.mouse.click(8, 8)


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
    jctx = ctx.journey_ctx()
    ux_journey._goto_lenta(jctx)
    page = ctx.page
    if ctx.is_mobile:
        sheet = _wait_mobile_feed_sheet(page)
        design = sheet.locator('input[name="category"][value="design"]')
        design.check(force=True)
        page.wait_for_timeout(1200)
        if _feed_error(ctx):
            raise RuntimeError("error banner after category chip")
        chip = sheet.locator(
            ".rl-feed-skill:not(.is-disabled), .rl-chip, .rl-feed-skills .rl-chip"
        ).first
        chip.wait_for(state="visible", timeout=30_000)
        chip.click()
        page.locator("#rl-feed-sheet-apply").click()
        page.wait_for_timeout(2000)
    else:
        page.locator("#filter-category-design input").check(force=True)
        page.wait_for_timeout(1200)
        if _feed_error(ctx):
            raise RuntimeError("error banner after category chip")
        ux_journey._open_skills_panel(jctx)
        chip = page.locator(
            "#rl-feed-skills .rl-feed-skill:not(.is-disabled), #rl-feed-skills .rl-chip"
        ).first
        chip.wait_for(state="visible", timeout=30_000)
        chip.click()
        page.locator("#rl-feed-skills-apply").click()
        page.wait_for_timeout(2000)
    if _feed_error(ctx):
        raise RuntimeError("error banner after «Применить»")
    after = page.locator("#rl-feed-count").inner_text()
    if "ошиб" in after.casefold():
        raise RuntimeError(f"feed count error: {after}")


def u3_sort_dropdown(ctx: AuditCtx) -> None:
    jctx = ctx.journey_ctx()
    ux_journey._goto_lenta(jctx)
    page = ctx.page
    if ctx.is_mobile:
        sheet = _wait_mobile_feed_sheet(page)
        match_radio = sheet.locator('input[name="sort"][value="match"]')
        if not match_radio.count():
            raise RuntimeError("mobile sheet: sort match radio missing")
        time_radio = sheet.locator('input[name="sort"][value="time"]')
        if time_radio.count():
            time_radio.first.click(force=True)
            page.wait_for_timeout(400)
        match_radio.first.click(force=True)
        page.wait_for_timeout(800)
        overlay = page.locator("#rl-feed-sheet-overlay")
        if overlay.count():
            box = overlay.bounding_box()
            if box:
                page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 16)
            else:
                page.mouse.click(195, 16)
        else:
            page.mouse.click(5, 5)
        page.wait_for_timeout(500)
        if page.evaluate(
            "() => { const s = document.getElementById('rl-feed-sheet'); return s && !s.hidden; }"
        ):
            raise RuntimeError("mobile sheet did not close on overlay tap")
        return

    sort_dd = page.locator(".rl-filter-sort-dd")
    sort_dd.locator("summary").click()
    if not sort_dd.evaluate("el => el.open"):
        raise RuntimeError("sort dropdown did not open")
    page.locator('input[name="sort"][value="match"]').check(force=True)
    page.wait_for_timeout(600)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    if sort_dd.evaluate("el => el.open"):
        page.mouse.click(8, 8)
        page.wait_for_timeout(400)
    if sort_dd.evaluate("el => el.open"):
        raise RuntimeError("sort dropdown did not close (Esc / tap outside)")


def u4_card_tap_outside(ctx: AuditCtx) -> None:
    jctx = ctx.journey_ctx()
    ux_journey._goto_lenta(jctx)
    card = ctx.page.locator("#rl-feed-list .rl-lead-card[data-id]").first
    card.wait_for(state="visible")
    card.locator(".rl-lead-card__title").first.click()
    ctx.page.wait_for_timeout(600)
    card.locator(".rl-feed-card__body-inner").wait_for(state="visible", timeout=15_000)
    ctx.page.mouse.click(10, 10)
    ctx.page.wait_for_timeout(500)
    if "is-expanded" in (card.get_attribute("class") or ""):
        raise RuntimeError("card did not collapse on tap outside")


def u5_draft_tools(ctx: AuditCtx) -> None:
    jctx = ctx.journey_ctx()
    ux_journey._ensure_feed_draft_ready(jctx)
    cards = ux_journey._cards_with_reply_btn(jctx)
    if not cards:
        raise RuntimeError("no card with «Написать отклик»")
    card = cards[0]
    card.scroll_into_view_if_needed()
    if not card.locator(".rl-feed-card__body-inner").count():
        card.locator(".rl-lead-card__title").first.click()
        ctx.page.wait_for_timeout(400)
    btn = card.locator(".rl-feed-card__reply-btn")
    if not btn.count():
        raise RuntimeError("reply button missing")
    btn.first.click()
    ux_journey._wait_draft_text(jctx, card)
    body = card.inner_text().casefold()
    if "появится после генерации" in body:
        raise RuntimeError("tools placeholder «появится после генерации»")
    reply = card.locator("[data-reply-text]")
    if not reply.count() or len((reply.first.inner_text() or "").strip()) < 40:
        raise RuntimeError("draft text too short after generate")


def u6_fab_modal(ctx: AuditCtx) -> None:
    jctx = ctx.journey_ctx()
    ux_journey._goto_lenta(jctx)
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
    jctx = ctx.journey_ctx()
    ux_journey._goto_lenta(jctx)
    page = ctx.page
    overflow_x = page.evaluate(
        "() => Math.max(0, document.documentElement.scrollWidth - window.innerWidth)"
    )
    if overflow_x > 8:
        ctx.add_finding(
            "critical",
            f"horizontal page scroll {overflow_x}px before skills sheet",
            scenario="U8",
        )

    open_btn = page.locator("#rl-feed-filters-open")
    open_btn.wait_for(state="visible")
    sheet = _wait_mobile_feed_sheet(page)
    apply_btn = sheet.locator("#rl-feed-sheet-apply, .rl-feed-skills-apply").first
    if not apply_btn.count():
        raise RuntimeError("mobile sheet: «Применить» missing")
    actions = sheet.locator(".rl-feed-sheet__actions")
    if actions.count():
        actions_box = actions.first.bounding_box()
        apply_box = apply_btn.bounding_box()
        if actions_box and apply_box and apply_box["y"] < actions_box["y"] - 2:
            raise RuntimeError("«Применить» not in sticky footer (.rl-feed-sheet__actions)")

    scroll_body = sheet.locator(".rl-feed-sheet__body, .rl-skills-panel__body").first
    if scroll_body.count():
        scroll_body.evaluate("el => { el.scrollTop = el.scrollHeight; }")
        page.wait_for_timeout(400)

    chip = sheet.locator(".rl-feed-skill, .rl-chip, .rl-feed-skills .rl-chip").first
    if chip.count():
        chip.click()
        page.wait_for_timeout(400)
    # sticky footer «Применить» closes sheet
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
    errors = [e for e in ctx.console_errors if e.startswith("[error]")]
    if errors:
        raise RuntimeError(f"console errors: {errors[:3]}")
    bad = [f for f in ctx.network_failures if f.get("status", 0) >= 400]
    feed_draft = [
        f
        for f in bad
        if any(x in (f.get("url") or "") for x in ("/feed", "/draft", "/wp-json/rawlead"))
    ]
    if feed_draft:
        sample = feed_draft[:3]
        raise RuntimeError(f"API feed/draft failures: {sample}")


SCENARIOS: dict[str, tuple[str, str, Callable[[AuditCtx], None]]] = {
    "U1": ("Header + footer links", "critical", u1_header_footer),
    "U2": ("Лента: категория + навыки", "critical", u2_lenta_skills),
    "U3": ("Сортировка + закрытие", "critical", u3_sort_dropdown),
    "U4": ("Expand + tap outside", "critical", u4_card_tap_outside),
    "U5": ("Draft + инструменты", "critical", u5_draft_tools),
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
        },
        ensure_ascii=False,
        indent=2,
    )

    user_parts: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "Ты UX-редактор RawLead (фриланс-лента). Оцени mobile-скрины и JSON findings.\n"
                "Вопросы: понятно ли куда жать? криво на 390px? перекрытия? мелкий tap target?\n"
                "Формат ответа — markdown с секциями:\n"
                "## Критично\n## Раздражает\n## Ок\n"
                "В конце: **Rating (1–5)** одной строкой — НЕ ставь 5/5 если U8 mobile не прогонялся или есть critical.\n\n"
                f"Findings JSON:\n```json\n{findings_json}\n```"
            ),
        }
    ]
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
        "# Pre-prod UX audit — human (O37c LLM)",
        "",
        f"- **Time:** {report['generated_at']}",
        f"- **Model:** {model}",
        f"- **Mobile screenshots:** {len(unique)}",
        f"- **Script critical count:** {report['critical_count']}",
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
    access_token: str,
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
            )
            _attach_observers(ctx)

            for sid, (title, sev, fn) in SCENARIOS.items():
                if sid == "U8" and vp_label != "mobile":
                    continue
                if sid in ("U5", "U7") and not access_token:
                    results.append(
                        {
                            "id": sid,
                            "title": title,
                            "viewport": vp_label,
                            "pass": False,
                            "ms": 0,
                            "error": "no test token",
                            "skipped": True,
                            "screenshots": {},
                        }
                    )
                    ctx.add_finding("critical", f"{title}: no test token", scenario=sid)
                    continue
                row = _run_scenario(sid, title, sev, fn, ctx)
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

    critical = sum(1 for f in all_findings if f["severity"] == "critical")
    passed = sum(1 for r in results if r["pass"])
    ok = critical == 0 and passed == len(results)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base,
        "browser": ux_journey._browser_report_label(browser_name, access_token),
        "has_auth": bool(access_token),
        "viewports": [v[0] for v in viewports],
        "scenarios_total": len(results),
        "scenarios_pass": passed,
        "critical_count": critical,
        "pass": ok,
        "results": results,
        "findings": all_findings,
        "artifacts_dir": str(_ARTIFACT_DIR.relative_to(_ROOT)).replace("\\", "/"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="O37c UX audit U1–U10 + LLM human")
    parser.add_argument("--base-url", default="https://rawlead.ru")
    parser.add_argument("--headed", action="store_true")
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

    token = _require_token(_resolve_token(None), browser=args.browser)
    _forbid_owner_browser_gate(args.browser, token)

    try:
        report = run_audit(
            args.base_url,
            headless=not args.headed,
            browser_name=args.browser,
            access_token=token,
        )
    except ImportError:
        print(
            "playwright не установлен: pip install playwright && playwright install chromium",
            file=sys.stderr,
        )
        return 2

    if not args.skip_llm:
        api_key = _load_env_value("AI_API_KEY") or _load_env_value("OPENROUTER_API_KEY")
        model = (
            args.llm_model.strip()
            or _load_env_value("OPENROUTER_MODEL_PREMIUM")
            or "google/gemini-2.5-flash"
        )
        if api_key:
            llm_meta = _llm_human_review(
                report, out_path=args.output_human, model=model, api_key=api_key
            )
            report["human_md"] = llm_meta["path"]
            report["llm"] = llm_meta
        else:
            stub = (
                "# Pre-prod UX audit — human (O37c)\n\n"
                "## Критично\n- AI_API_KEY не задан — LLM pass пропущен\n\n"
                "## Раздражает\n\n## Ок\n\n**Rating:** n/a\n"
            )
            args.output_human.write_text(stub, encoding="utf-8")
            report["human_md"] = str(args.output_human.relative_to(_ROOT)).replace("\\", "/")
            report["llm"] = {"skipped": "no AI_API_KEY"}

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _write_markdown(report, args.output_md)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
