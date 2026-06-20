"""§ O280-E2E-NEXT: Playwright runner n1–n25 for rawlead-next.

  .venv\\Scripts\\python.exe scripts\\preprod_playwright\\next_e2e.py --base-url http://localhost:3001
  .venv\\Scripts\\python.exe scripts\\preprod_playwright\\next_e2e.py --viewport mobile --ids n20
"""

from __future__ import annotations

import argparse
import json
import sys
import time
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
_PLAYWRIGHT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_PLAYWRIGHT_DIR))

import next_ui as ui  # noqa: E402

_ARTIFACT_JSON = _ROOT / "data" / "preprod_next_e2e.json"
_HUMAN_MD = _ROOT / "data" / "preprod_next_e2e_human.md"
_SCREENSHOT_DIR = _ROOT / "data" / "preprod_next_e2e"

DESKTOP_IDS = (
    "n5", "n16", "n17",
    "n1", "n2", "n3", "n6", "n7", "n25",
    "n8", "n9", "n10", "n11", "n12", "n13", "n14", "n15", "n18", "n19",
    "n21", "n22", "n23", "n24",
)
_DRAFT_SCENARIO_IDS = frozenset({"n5", "n16", "n17"})
MOBILE_DEFAULT = ("n20",)


@dataclass
class RunConfig:
    base_url: str
    headless: bool
    slow_mo: int
    timeout_ms: int
    viewport_name: str
    viewport: dict[str, int]
    screenshot_dir: Path
    preprod_token: str | None
    monica_token: str | None
    steps: list[str] = field(default_factory=list)


def _viewport_dict(name: str) -> dict[str, int]:
    if name == "mobile":
        return dict(ui.MOBILE_VIEWPORT)
    return dict(ui.DESKTOP_VIEWPORT)


def _resolve_ids(viewport_name: str, ids_csv: str | None) -> list[str]:
    if ids_csv:
        return [x.strip().lower() for x in ids_csv.split(",") if x.strip()]
    if viewport_name == "mobile":
        return list(MOBILE_DEFAULT)
    return list(DESKTOP_IDS)


def _screenshot(page: Any, cfg: RunConfig, scenario_id: str) -> str | None:
    cfg.screenshot_dir.mkdir(parents=True, exist_ok=True)
    path = cfg.screenshot_dir / f"{scenario_id}_{cfg.viewport_name}_fail.png"
    try:
        page.screenshot(path=str(path), full_page=True)
        return str(path.relative_to(_ROOT))
    except Exception:
        return None


def _log_step(cfg: RunConfig, msg: str) -> None:
    cfg.steps.append(msg)


_TRANSIENT_ERR = (
    "ERR_CONNECTION_TIMED_OUT",
    "ERR_CONNECTION_RESET",
    "ERR_NETWORK_CHANGED",
)


def _run(
    sid: str,
    fn: Callable[[Any, RunConfig], None],
    cfg: RunConfig,
    browser: Any,
    *,
    token: str | None = None,
    clear_quiz: bool = False,
) -> dict[str, Any]:
    last: dict[str, Any] | None = None
    for attempt in range(2):
        t0 = time.perf_counter()
        cfg.steps = []
        ctx = browser.new_context(viewport=cfg.viewport, locale="ru-RU")
        if clear_quiz:
            ui.add_quiz_clear_init_script(ctx)
        if token:
            ui.add_token_init_script(ctx, token)
        page = ctx.new_page()
        page.set_default_timeout(cfg.timeout_ms)
        console_errors: list[str] = []
        ui.attach_console_monitor(page, console_errors)
        ui.attach_http_monitor(page, console_errors)
        err: str | None = None
        shot: str | None = None
        passed = False
        try:
            fn(page, cfg)
            if console_errors:
                err = f"console error: {console_errors[0]}"
            else:
                passed = True
        except Exception as exc:  # noqa: BLE001
            err = str(exc)
            shot = _screenshot(page, cfg, sid)
        finally:
            ctx.close()
        ms = int((time.perf_counter() - t0) * 1000)
        last = {
            "id": sid,
            "viewport": cfg.viewport_name,
            "pass": passed,
            "ms": ms,
            "error": err,
            "screenshot": shot,
            "steps": list(cfg.steps),
        }
        if passed or not any(x in (err or "") for x in _TRANSIENT_ERR) or attempt == 1:
            return last
    return last or {"id": sid, "viewport": cfg.viewport_name, "pass": False, "ms": 0, "error": "unknown", "screenshot": None, "steps": []}


# ─── Scenarios ────────────────────────────────────────────────────────────────


def n1_home(page: Any, cfg: RunConfig) -> None:
    ui.goto_path(page, cfg.base_url, "/")
    _log_step(cfg, "home loaded")
    page.locator('[data-testid="header-logo"]').click()
    page.wait_for_url("**/")
    page.locator('[data-testid="header-nav-lenta"]').click()
    page.wait_for_url("**/lenta/**")
    page.go_back()
    page.locator('[data-testid="header-login"]').click()
    page.wait_for_selector(ui.LOGIN_MODAL, state="visible")
    page.locator(ui.LOGIN_MODAL_CLOSE).click()
    page.locator('[data-testid="hero-cta-lenta"]').click()
    page.wait_for_url("**/lenta/**")
    page.goto(f"{cfg.base_url}/", wait_until="domcontentloaded")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.6)")
    page.wait_for_timeout(600)
    page.locator('[data-testid="home-pricing-cta"]').click()
    page.wait_for_url("**/pricing/**")
    for path in ("/faq/", "/how/", "/contact/", "/"):
        ui.goto_path(page, cfg.base_url, path)
        if page.url.endswith(path.rstrip("/") + "/") or path == "/":
            _log_step(cfg, f"footer route {path} ok")


def n2_feed_filters(page: Any, cfg: RunConfig) -> None:
    ui.goto_lenta(page, cfg.base_url)
    if ui.feed_card_count(page) < 1:
        raise RuntimeError("feed has no cards")
    if not page.locator(ui.FEED_LIST).count():
        raise RuntimeError("feed list missing")
    for slug in ("dev", "design", "marketing", "text", ""):
        ui.click_category(page, slug)
    page.locator('[data-testid="feed-filter-dropdown"]').click()
    page.wait_for_selector('[data-testid="feed-sort-panel"]', state="visible")
    page.keyboard.press("Escape")
    before = ui.feed_card_count(page)
    more = page.locator(ui.FEED_LOAD_MORE)
    if more.count() and more.is_enabled():
        more.click()
        page.wait_for_timeout(1200)
        if ui.feed_card_count(page) <= before:
            raise RuntimeError("load more did not append cards")


def n3_card_expand(page: Any, cfg: RunConfig) -> None:
    ui.goto_lenta(page, cfg.base_url)
    c1 = ui.expand_card_at(page, 0)
    if not ui.card_body_visible(c1):
        raise RuntimeError("card 1 body not visible")
    c2 = ui.expand_card_at(page, 1)
    if not ui.card_body_visible(c2):
        raise RuntimeError("card 2 body not visible")
    ui.assert_match_visible(c2)


def n4_mobile_sheet(page: Any, cfg: RunConfig) -> None:
    ui.goto_lenta(page, cfg.base_url)
    ui.open_mobile_filter_sheet(page)
    page.locator('[data-testid="sheet-cat-dev"]').click()
    ui.apply_mobile_sheet(page)
    page.wait_for_selector(ui.FEED_SHEET, state="hidden", timeout=10_000)


def n5_draft(page: Any, cfg: RunConfig) -> None:
    if not cfg.preprod_token:
        raise RuntimeError("RAWLEAD_PREPROD_ACCESS_TOKEN required for n5")
    tier = ui.bootstrap_preprod_feed(page, cfg.base_url, cfg.preprod_token)
    if tier != "premium":
        raise RuntimeError(f"preprod feed tier {tier!r}, need premium for draft")
    card = ui.expand_card_at(page, 0)
    text = ui.generate_draft_on_card(page, card)
    if len(text) < 80:
        raise RuntimeError(f"draft too short: {len(text)}")
    ui.copy_draft(card)
    ui.collapse_draft_panel(card)


def n6_quiz_mid_exit(page: Any, cfg: RunConfig) -> None:
    ui.clear_quiz_storage(page, base=cfg.base_url)
    ui.goto_lenta_quiz(page, cfg.base_url)
    ui.start_quiz_from_intro(page)
    ui.answer_n_cards(page, 3)
    if ui.is_result_visible(page):
        raise RuntimeError("quiz finished too early")
    ui.close_quiz_overlay(page)
    ui.goto_lenta(page, cfg.base_url)
    ui.goto_lenta_quiz(page, cfg.base_url)
    ui.assert_intro_visible(page)


def n7_quiz_full(page: Any, cfg: RunConfig) -> None:
    ui.clear_quiz_storage(page, base=cfg.base_url)
    ui.goto_lenta_quiz(page, cfg.base_url)
    ui.start_quiz_from_intro(page)
    ui.answer_until_result(page)
    ui.assert_anon_result_login_cta(page)
    ui.assert_quiz_completed_storage(page)
    ui.click_retake_on_result(page)
    ui.answer_until_result(page)
    if not ui.is_result_visible(page):
        raise RuntimeError("second quiz result missing")
    ui.assert_quiz_completed_storage(page)


def n25_anon_funnel(page: Any, cfg: RunConfig) -> None:
    ui.clear_quiz_storage(page, base=cfg.base_url)
    ui.goto_lenta_quiz(page, cfg.base_url)
    ui.start_quiz_from_intro(page)
    ui.answer_until_result(page)
    ui.assert_anon_result_login_cta(page)
    ui.assert_quiz_completed_storage(page)
    ui.close_quiz_watch_feed_anon(page)
    ui.assert_feed_quiz_login_promo(page)
    page.locator(ui.FEED_QUIZ_LOGIN_CTA).click()
    page.wait_for_selector(ui.LOGIN_MODAL, state="visible", timeout=10_000)
    ui.close_login_modal(page)
    _log_step(cfg, "anon funnel: result → promo → login modal ok")


def n8_anon_strip(page: Any, cfg: RunConfig) -> None:
    ui.goto_lenta(page, cfg.base_url)
    strip = page.locator(ui.ANON_STRIP)
    if not strip.count() or not strip.is_visible():
        raise RuntimeError("anon strip hidden")
    if "30 мин" not in (strip.inner_text() or ""):
        raise RuntimeError("anon strip text mismatch")
    ui.open_login_modal_from_strip(page)
    ui.close_login_modal(page)


def n9_how(page: Any, cfg: RunConfig) -> None:
    ui.goto_path(page, cfg.base_url, "/how/")
    if not page.locator("h1").count():
        raise RuntimeError("how h1 missing")
    page.locator('[data-testid="header-nav-lenta"]').click()
    page.wait_for_url("**/lenta/**")


def n10_pricing(page: Any, cfg: RunConfig) -> None:
    ui.goto_path(page, cfg.base_url, "/pricing/")
    if "790" not in (page.content() or ""):
        raise RuntimeError("price not visible")
    btn = page.locator('[data-testid="pricing-checkout"]')
    if btn.count():
        btn.click()
        page.wait_for_timeout(500)


def n11_faq(page: Any, cfg: RunConfig) -> None:
    ui.goto_path(page, cfg.base_url, "/faq/")
    items = page.locator('[data-testid^="faq-item-"]')
    n = min(items.count(), 4)
    if n < 1:
        raise RuntimeError("no faq items")
    for i in range(n):
        btn = items.nth(i)
        btn.scroll_into_view_if_needed()
        page.wait_for_timeout(250)
        btn.click(force=True)
        page.wait_for_timeout(350)
        btn.click(force=True)
        page.wait_for_timeout(200)


def n12_contact(page: Any, cfg: RunConfig) -> None:
    ui.goto_path(page, cfg.base_url, "/contact/")
    link = page.locator('[data-testid="contact-telegram"]')
    link.focus()
    if not link.count():
        raise RuntimeError("contact CTA missing")


def n13_cabinet_anon(page: Any, cfg: RunConfig) -> None:
    ui.goto_path(page, cfg.base_url, "/cabinet/")
    page.wait_for_function(
        """() => {
          const app = document.querySelector('#rl-cabinet-app');
          const panel = document.querySelector('[data-testid="cabinet-login-panel"]');
          const spin = document.querySelector('.animate-spin');
          return !!app && !!panel && !spin;
        }""",
        timeout=60_000,
    )


def n14_cross_nav(page: Any, cfg: RunConfig) -> None:
    ui.goto_path(page, cfg.base_url, "/")
    page.locator('[data-testid="footer-link-pricing"]').click()
    page.wait_for_url("**/pricing/**")
    page.go_back()
    ui.goto_lenta_quiz(page, cfg.base_url)
    if not ui.is_intro_visible(page) and not ui.is_play_visible(page):
        raise RuntimeError("deep link #quiz did not open quiz")


def n15_token_tier(page: Any, cfg: RunConfig) -> None:
    if not cfg.preprod_token:
        raise RuntimeError("RAWLEAD_PREPROD_ACCESS_TOKEN required")
    ui.bootstrap_preprod_feed(page, cfg.base_url, cfg.preprod_token, timeout_ms=45_000)
    if page.locator(ui.ANON_STRIP).is_visible():
        raise RuntimeError("anon strip visible when logged in")


def n16_draft_twice(page: Any, cfg: RunConfig) -> None:
    if not cfg.preprod_token:
        raise RuntimeError("RAWLEAD_PREPROD_ACCESS_TOKEN required")
    ui.bootstrap_preprod_feed(page, cfg.base_url, cfg.preprod_token, timeout_ms=45_000)
    for idx in (0, 1):
        if idx == 1:
            page.wait_for_timeout(35_000)
        card = ui.expand_card_at(page, idx)
        ui.generate_draft_on_card(page, card)
        card.click()
        page.wait_for_timeout(400)


def n17_draft_collapse_mid(page: Any, cfg: RunConfig) -> None:
    if not cfg.preprod_token:
        raise RuntimeError("RAWLEAD_PREPROD_ACCESS_TOKEN required")
    ui.bootstrap_preprod_feed(page, cfg.base_url, cfg.preprod_token, timeout_ms=45_000)
    card = ui.expand_card_at(page, 0)
    card.locator('[data-testid="feed-card-cta"]').click()
    page.wait_for_timeout(800)
    card.click()
    page.wait_for_timeout(400)


def n18_cabinet_logged(page: Any, cfg: RunConfig) -> None:
    if not cfg.preprod_token:
        raise RuntimeError("RAWLEAD_PREPROD_ACCESS_TOKEN required")
    ui.inject_token(page, cfg.preprod_token, base=cfg.base_url)
    ui.goto_path(page, cfg.base_url, "/cabinet/")
    try:
        page.wait_for_function(
            """() => {
              const app = document.querySelector('#rl-cabinet-app');
              const panel = document.querySelector('[data-testid="cabinet-login-panel"]');
              const spin = document.querySelector('.animate-spin');
              return !!app && !panel && !spin;
            }""",
            timeout=45_000,
        )
    except Exception as exc:
        raise RuntimeError(
            "PREPROD cabinet auth failed — refresh RAWLEAD_PREPROD_ACCESS_TOKEN in .env.site"
        ) from exc
    content = page.content() or ""
    if "Активировать Trial" in content:
        raise RuntimeError("trial activate chip should be hidden")


def n19_monica_inbox(page: Any, cfg: RunConfig) -> None:
    if not cfg.monica_token:
        raise RuntimeError("RAWLEAD_MONICA_TOKEN required")
    ui.inject_token(page, cfg.monica_token, base=cfg.base_url)
    ui.goto_path(page, cfg.base_url, "/cabinet/")
    page.wait_for_timeout(2000)


def n20_mobile_overflow(page: Any, cfg: RunConfig) -> None:
    ui.goto_lenta(page, cfg.base_url)
    if ui.feed_card_count(page) < 1:
        raise RuntimeError("feed has no cards")
    ui.open_mobile_filter_sheet(page)
    page.locator('[data-testid="sheet-cat-dev"]').click()
    ui.apply_mobile_sheet(page)
    page.wait_for_selector(ui.FEED_SHEET, state="hidden", timeout=10_000)
    ui.assert_no_horizontal_overflow(page)


def n21_quiz_import(page: Any, cfg: RunConfig) -> None:
    if not cfg.preprod_token:
        raise RuntimeError("RAWLEAD_PREPROD_ACCESS_TOKEN required")
    tag_before = ui.count_neon_user_tags(ui.ACC1_USER_ID)
    api_calls: list[dict[str, Any]] = []
    ui.clear_quiz_storage(page, base=cfg.base_url)
    ui.attach_quiz_api_monitor(page, api_calls)
    ui.goto_lenta_quiz(page, cfg.base_url)
    ui.start_quiz_from_intro(page)
    ui.answer_until_result(page)
    ui.assert_quiz_completed_storage(page)
    ui.inject_token(page, cfg.preprod_token, base=cfg.base_url)
    page.reload(wait_until="domcontentloaded")
    ui.inject_token(page, cfg.preprod_token, base=cfg.base_url)
    ui.wait_feed_tier(page, "premium", "free", timeout_ms=45_000)
    page.wait_for_timeout(2500)
    ui.assert_quiz_api_ok(api_calls)
    if tag_before is not None:
        tag_after = ui.count_neon_user_tags(ui.ACC1_USER_ID)
        if tag_after is not None and tag_after < tag_before:
            raise RuntimeError("tags decreased after import")


def n22_retake_abandon(page: Any, cfg: RunConfig) -> None:
    if not cfg.preprod_token:
        raise RuntimeError("RAWLEAD_PREPROD_ACCESS_TOKEN required")
    ui.goto_lenta_quiz(page, cfg.base_url)
    ui.start_quiz_from_intro(page)
    ui.answer_until_result(page)
    ui.click_retake_on_result(page)
    ui.answer_n_cards(page, 4)
    ui.close_quiz_overlay(page)


def n23_monica_feed(page: Any, cfg: RunConfig) -> None:
    if not cfg.monica_token:
        raise RuntimeError("RAWLEAD_MONICA_TOKEN required")
    ui.inject_token(page, cfg.monica_token, base=cfg.base_url)
    ui.goto_lenta(page, cfg.base_url)
    ui.wait_feed_tier(page, "premium", timeout_ms=90_000)
    card = ui.expand_card_at(page, 0)
    ui.assert_match_visible(card)


def n24_home_fab(page: Any, cfg: RunConfig) -> None:
    ui.goto_path(page, cfg.base_url, "/")
    fab = page.locator(ui.SUPPORT_FAB)
    if not fab.count():
        raise RuntimeError("support FAB missing")
    fab.click()
    page.wait_for_timeout(400)
    fab.click()


SCENARIOS: dict[str, Callable[[Any, RunConfig], None]] = {
    "n1": n1_home,
    "n2": n2_feed_filters,
    "n3": n3_card_expand,
    "n4": n4_mobile_sheet,
    "n5": n5_draft,
    "n6": n6_quiz_mid_exit,
    "n7": n7_quiz_full,
    "n8": n8_anon_strip,
    "n9": n9_how,
    "n10": n10_pricing,
    "n11": n11_faq,
    "n12": n12_contact,
    "n13": n13_cabinet_anon,
    "n14": n14_cross_nav,
    "n15": n15_token_tier,
    "n16": n16_draft_twice,
    "n17": n17_draft_collapse_mid,
    "n18": n18_cabinet_logged,
    "n19": n19_monica_inbox,
    "n20": n20_mobile_overflow,
    "n21": n21_quiz_import,
    "n22": n22_retake_abandon,
    "n23": n23_monica_feed,
    "n24": n24_home_fab,
    "n25": n25_anon_funnel,
}

TOKEN_SCENARIOS = {
    "n5", "n15", "n16", "n17", "n18", "n21", "n22",
}
MONICA_SCENARIOS = {"n19", "n23"}
QUIZ_CLEAR = {"n6", "n7", "n21", "n22", "n25"}


def run_next_e2e(
    *,
    base_url: str,
    headless: bool = True,
    slow_mo: int = 0,
    timeout_ms: int = 60_000,
    viewport_name: str = "desktop",
    ids: list[str] | None = None,
) -> dict[str, Any]:
    selected = ids or _resolve_ids(viewport_name, None)
    preprod = ui.load_env_token("RAWLEAD_PREPROD_ACCESS_TOKEN")
    monica = ui.load_env_token("RAWLEAD_MONICA_TOKEN")
    cfg = RunConfig(
        base_url=base_url.rstrip("/"),
        headless=headless,
        slow_mo=slow_mo,
        timeout_ms=timeout_ms,
        viewport_name=viewport_name,
        viewport=_viewport_dict(viewport_name),
        screenshot_dir=_SCREENSHOT_DIR,
        preprod_token=preprod,
        monica_token=monica,
    )
    results: list[dict[str, Any]] = []

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        launch_kwargs: dict[str, Any] = {"headless": headless}
        if slow_mo:
            launch_kwargs["slow_mo"] = slow_mo
        browser = p.chromium.launch(**launch_kwargs)
        try:
            if preprod and _DRAFT_SCENARIO_IDS.intersection(selected):
                ui.ensure_draft_quota_for_e2e(preprod, base_url=cfg.base_url)
            for sid in selected:
                fn = SCENARIOS.get(sid)
                if not fn:
                    results.append({
                        "id": sid, "viewport": viewport_name, "pass": False,
                        "ms": 0, "error": f"unknown id {sid}", "screenshot": None, "steps": [],
                    })
                    continue
                token = None
                if sid in TOKEN_SCENARIOS or sid in MONICA_SCENARIOS:
                    token = monica if sid in MONICA_SCENARIOS else preprod
                if sid == "n5":
                    time.sleep(5)
                results.append(
                    _run(
                        sid, fn, cfg, browser,
                        token=token,
                        clear_quiz=sid in QUIZ_CLEAR,
                    )
                )
        finally:
            browser.close()

    passed = sum(1 for r in results if r["pass"])
    ok = passed == len(results) and len(results) > 0
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": cfg.base_url,
        "viewport": viewport_name,
        "scenarios_total": len(results),
        "scenarios_pass": passed,
        "pass": ok,
        "has_preprod_token": bool(preprod),
        "has_monica_token": bool(monica),
        "results": results,
        "artifacts_dir": str(_SCREENSHOT_DIR.relative_to(_ROOT)),
    }


def _write_human(report: dict[str, Any]) -> None:
    lines = [
        f"# Next E2E — {report.get('generated_at', '')}",
        f"base: {report.get('base_url', report.get('desktop', {}).get('base_url', ''))}",
    ]
    if "desktop" in report:
        d = report["desktop"]
        m = report.get("mobile", {})
        lines.append(
            f"pass: {report.get('scenarios_pass')}/{report.get('scenarios_total')} "
            f"(desktop {d.get('scenarios_pass')}/{d.get('scenarios_total')}, "
            f"mobile {m.get('scenarios_pass')}/{m.get('scenarios_total')})"
        )
        lines.append("")
        for label, block in (("desktop", d), ("mobile", m)):
            lines.append(f"## {label}")
            for row in block.get("results", []):
                mark = "OK" if row.get("pass") else "FAIL"
                lines.append(f"### {row.get('id')} [{mark}] ({row.get('ms')} ms)")
                if row.get("error"):
                    lines.append(f"- error: {row['error']}")
                for step in row.get("steps") or []:
                    lines.append(f"- {step}")
                lines.append("")
    else:
        lines.append(
            f"pass: {report.get('scenarios_pass')}/{report.get('scenarios_total')} · "
            f"viewport: {report.get('viewport')}"
        )
        lines.append("")
        for row in report.get("results", []):
            mark = "OK" if row.get("pass") else "FAIL"
            lines.append(f"## {row.get('id')} [{mark}] ({row.get('ms')} ms)")
            if row.get("error"):
                lines.append(f"- error: {row['error']}")
            for step in row.get("steps") or []:
                lines.append(f"- {step}")
            lines.append("")
    _HUMAN_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="O280 next E2E n1–n25")
    parser.add_argument("--base-url", default="http://localhost:3001")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--slow-mo", type=int, default=0)
    parser.add_argument("--timeout-ms", type=int, default=60_000)
    parser.add_argument("--viewport", choices=("desktop", "mobile"), default="desktop")
    parser.add_argument("--ids", help="Comma-separated n1..n25")
    parser.add_argument("--output-json", type=Path, default=_ARTIFACT_JSON)
    parser.add_argument(
        "--gate-all",
        action="store_true",
        help="Run desktop matrix + mobile n20 and merge into one report",
    )
    args = parser.parse_args()

    try:
        if args.gate_all:
            desktop = run_next_e2e(
                base_url=args.base_url,
                headless=not args.headed,
                slow_mo=args.slow_mo,
                timeout_ms=args.timeout_ms,
                viewport_name="desktop",
            )
            mobile = run_next_e2e(
                base_url=args.base_url,
                headless=not args.headed,
                slow_mo=args.slow_mo,
                timeout_ms=args.timeout_ms,
                viewport_name="mobile",
                ids=["n20"],
            )
            report = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "base_url": args.base_url.rstrip("/"),
                "pass": desktop["pass"] and mobile["pass"],
                "desktop": desktop,
                "mobile": mobile,
                "scenarios_total": desktop["scenarios_total"] + mobile["scenarios_total"],
                "scenarios_pass": desktop["scenarios_pass"] + mobile["scenarios_pass"],
            }
        else:
            ids = _resolve_ids(args.viewport, args.ids)
            report = run_next_e2e(
                base_url=args.base_url,
                headless=not args.headed,
                slow_mo=args.slow_mo,
                timeout_ms=args.timeout_ms,
                viewport_name=args.viewport,
                ids=ids,
            )
    except ImportError:
        print("pip install playwright && playwright install chromium", file=sys.stderr)
        return 2

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_human(report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
