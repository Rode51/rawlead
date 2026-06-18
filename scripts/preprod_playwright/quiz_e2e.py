"""§ O218: Playwright quiz lifecycle E2E j1–j7 (prod gate pre-ads).

  .venv\\Scripts\\python.exe scripts\\preprod_playwright\\quiz_e2e.py --base-url https://rawlead.ru
  .venv\\Scripts\\python.exe scripts\\preprod_playwright\\quiz_e2e.py --viewport mobile --ids j1,j2,j5
  .venv\\Scripts\\python.exe scripts\\preprod_playwright\\quiz_e2e.py --headed --slow-mo 100

Env: RAWLEAD_PREPROD_ACCESS_TOKEN (j3/j4/j6) · RAWLEAD_MONICA_TOKEN (j5) · opt. DATABASE_URL (j3/j4 Neon)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
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

import feed_ui  # noqa: E402
import quiz_ui  # noqa: E402

_ARTIFACT_JSON = _ROOT / "data" / "preprod_quiz_e2e.json"
_SCREENSHOT_DIR = _ROOT / "data" / "preprod_quiz_e2e"

ALL_IDS = ("j1", "j2", "j3", "j4", "j5", "j6", "j7")
MOBILE_IDS = frozenset({"j1", "j2", "j5", "j7"})


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


def _load_env_token(key: str) -> str | None:
    val = os.environ.get(key, "").strip()
    if val:
        return val
    for name in (".env.site", ".env", ".env.local"):
        path = _ROOT / name
        if not path.is_file():
            continue
        prefix = f"{key}="
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(prefix):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _viewport_dict(name: str) -> dict[str, int]:
    if name == "mobile":
        return dict(quiz_ui.MOBILE_VIEWPORT)
    return dict(quiz_ui.DESKTOP_VIEWPORT)


def _resolve_ids(viewport_name: str, ids_csv: str | None) -> list[str]:
    if ids_csv:
        selected = [x.strip().lower() for x in ids_csv.split(",") if x.strip()]
    elif viewport_name == "mobile":
        selected = [i for i in ALL_IDS if i in MOBILE_IDS]
    else:
        selected = list(ALL_IDS)
    unknown = [i for i in selected if i not in ALL_IDS]
    if unknown:
        raise ValueError(f"unknown scenario ids: {unknown}")
    return selected


def _screenshot(page: Any, cfg: RunConfig, scenario_id: str) -> str | None:
    cfg.screenshot_dir.mkdir(parents=True, exist_ok=True)
    path = cfg.screenshot_dir / f"{scenario_id}_{cfg.viewport_name}_fail.png"
    try:
        page.screenshot(path=str(path), full_page=True)
        return str(path.relative_to(_ROOT))
    except Exception:
        return None


def _run_scenario(
    scenario_id: str,
    fn: Callable[[Any, RunConfig], None],
    cfg: RunConfig,
    browser: Any,
    *,
    context_token: str | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    context = browser.new_context(viewport=cfg.viewport, locale="ru-RU")
    quiz_ui.add_quiz_clear_init_script(context)
    if context_token:
        quiz_ui.add_token_init_script(context, context_token)
    page = context.new_page()
    page.set_default_timeout(cfg.timeout_ms)
    error: str | None = None
    screenshot: str | None = None
    passed = False
    try:
        fn(page, cfg)
        passed = True
    except Exception as exc:  # noqa: BLE001 — E2E report
        error = str(exc)
        screenshot = _screenshot(page, cfg, scenario_id)
    finally:
        context.close()
    ms = int((time.perf_counter() - t0) * 1000)
    return {
        "id": scenario_id,
        "viewport": cfg.viewport_name,
        "pass": passed,
        "ms": ms,
        "error": error,
        "screenshot": screenshot,
    }


def scenario_j1(page: Any, cfg: RunConfig) -> None:
    """Anon: exit mid-quiz → reopen → intro restored."""
    quiz_ui.clear_quiz_storage(page, base=cfg.base_url)
    quiz_ui.goto_lenta_quiz(page, cfg.base_url)
    quiz_ui.start_quiz_from_intro(page)
    quiz_ui.answer_n_cards(page, 3)
    if quiz_ui.is_result_visible(page):
        raise RuntimeError("quiz finished too early in j1")
    quiz_ui.close_quiz_overlay(page)
    page.goto(f"{cfg.base_url.rstrip('/')}/lenta/", wait_until="domcontentloaded")
    feed_ui.goto_lenta(page, cfg.base_url)
    quiz_ui.goto_lenta_quiz(page, cfg.base_url)
    quiz_ui.assert_intro_visible(page)


def scenario_j2(page: Any, cfg: RunConfig) -> None:
    """Anon: complete → result → «Пройти ещё раз» → new session."""
    quiz_ui.clear_quiz_storage(page, base=cfg.base_url)
    quiz_ui.goto_lenta_quiz(page, cfg.base_url)
    quiz_ui.start_quiz_from_intro(page)
    quiz_ui.answer_until_result(page)
    quiz_ui.assert_result_visible(page)
    if not quiz_ui.read_completed_profile(page):
        raise RuntimeError("completed profile not saved after first run")
    quiz_ui.click_retake_on_result(page)
    quiz_ui.answer_until_result(page)
    quiz_ui.assert_result_visible(page)
    if not quiz_ui.read_completed_profile(page):
        raise RuntimeError("completed profile missing after second run")


def scenario_j3(page: Any, cfg: RunConfig) -> None:
    """Anon complete → JWT inject → tags import (Neon optional)."""
    if not cfg.preprod_token:
        raise RuntimeError("RAWLEAD_PREPROD_ACCESS_TOKEN required for j3")
    tag_before = quiz_ui.count_neon_user_tags(quiz_ui.ACC1_USER_ID)
    api_calls: list[dict[str, Any]] = []
    quiz_ui.clear_quiz_storage(page, base=cfg.base_url)
    quiz_ui.attach_quiz_api_monitor(page, api_calls)
    quiz_ui.goto_lenta_quiz(page, cfg.base_url)
    quiz_ui.start_quiz_from_intro(page)
    quiz_ui.answer_until_result(page)
    quiz_ui.assert_result_visible(page)
    quiz_ui.inject_access_token(page, cfg.preprod_token, base=cfg.base_url)
    page.reload(wait_until="domcontentloaded")
    feed_ui.wait_feed_tier(page, "premium", "free", "trial", timeout_ms=30_000)
    quiz_ui.trigger_post_login_import(page)
    quiz_ui.assert_quiz_api_ok(api_calls)
    if tag_before is not None:
        tag_after = quiz_ui.count_neon_user_tags(quiz_ui.ACC1_USER_ID)
        if tag_after is not None and tag_after <= tag_before:
            raise RuntimeError(
                f"Neon user_tags did not increase ({tag_before} → {tag_after})"
            )


def scenario_j4(page: Any, cfg: RunConfig) -> None:
    """Retake abandon keeps first profile (rawlead_quiz_completed_v1 backup)."""
    if not cfg.preprod_token:
        raise RuntimeError("RAWLEAD_PREPROD_ACCESS_TOKEN required for j4")
    quiz_ui.goto_lenta_quiz(page, cfg.base_url)
    quiz_ui.start_quiz_from_intro(page)
    quiz_ui.answer_until_result(page)
    page.wait_for_timeout(2000)
    first_profile = quiz_ui.read_completed_profile(page)
    if not first_profile or not first_profile.get("profile"):
        raise RuntimeError("first logged-in quiz profile missing")
    quiz_ui.click_retake_on_result(page, start_play=True)
    quiz_ui.answer_n_cards(page, 4)
    quiz_ui.close_quiz_overlay(page)
    quiz_ui.assert_completed_profile_unchanged(page, first_profile)


def scenario_j5_monica(page: Any, cfg: RunConfig) -> None:
    if not cfg.monica_token:
        raise RuntimeError("RAWLEAD_MONICA_TOKEN required for j5")
    feed_ui.goto_lenta(page, cfg.base_url)
    quiz_ui.inject_access_token(page, cfg.monica_token, base=cfg.base_url)
    page.reload(wait_until="domcontentloaded")
    feed_ui.wait_feed_loading_done(page, timeout_ms=60_000)
    try:
        feed_ui.wait_feed_tier(page, "premium", timeout_ms=90_000)
    except Exception:
        page.reload(wait_until="domcontentloaded")
        feed_ui.wait_feed_loading_done(page, timeout_ms=60_000)
        feed_ui.wait_feed_tier(page, "premium", timeout_ms=90_000)
    card = quiz_ui.expand_first_feed_card(page)
    feed_ui.assert_match_for_tier(card, "premium")


def scenario_j5_anon(page: Any, cfg: RunConfig) -> None:
    quiz_ui.clear_quiz_storage(page, base=cfg.base_url)
    feed_ui.goto_lenta(page, cfg.base_url)
    feed_ui.wait_feed_tier(page, "anon", timeout_ms=30_000)
    card = quiz_ui.expand_first_feed_card(page)
    feed_ui.assert_match_for_tier(card, "anon")


def scenario_j6(page: Any, cfg: RunConfig) -> None:
    """Cabinet retake → overlay intro on lenta."""
    if not cfg.preprod_token:
        raise RuntimeError("RAWLEAD_PREPROD_ACCESS_TOKEN required for j6")
    quiz_ui.inject_access_token(page, cfg.preprod_token, base=cfg.base_url)
    quiz_ui.goto_cabinet_logged_in(
        page, cfg.base_url, token=cfg.preprod_token
    )
    quiz_ui.click_cabinet_quiz_retake(page, cfg.base_url)
    if not quiz_ui.is_intro_visible(page) and not quiz_ui.is_play_visible(page):
        raise RuntimeError("cabinet retake did not open quiz overlay intro/cards")
    if quiz_ui.is_result_visible(page):
        raise RuntimeError("cabinet retake opened result instead of retake intro")


def scenario_j7(page: Any, cfg: RunConfig) -> None:
    """Synthetic quiz cards: title visible · source badge hidden."""
    quiz_ui.clear_quiz_storage(page, base=cfg.base_url)
    quiz_ui.goto_lenta_quiz(page, cfg.base_url)
    quiz_ui.assert_synthetic_card_in_quiz(page)


SCENARIOS: dict[str, Callable[[Any, RunConfig], None]] = {
    "j1": scenario_j1,
    "j2": scenario_j2,
    "j3": scenario_j3,
    "j4": scenario_j4,
    "j6": scenario_j6,
    "j7": scenario_j7,
}


def run_quiz_e2e(
    *,
    base_url: str,
    headless: bool = True,
    slow_mo: int = 0,
    timeout_ms: int = 45_000,
    viewport_name: str = "desktop",
    ids: list[str] | None = None,
    screenshot_dir: Path | None = None,
) -> dict[str, Any]:
    selected = ids or _resolve_ids(viewport_name, None)
    preprod = _load_env_token("RAWLEAD_PREPROD_ACCESS_TOKEN")
    monica = _load_env_token("RAWLEAD_MONICA_TOKEN")
    cfg = RunConfig(
        base_url=base_url.rstrip("/"),
        headless=headless,
        slow_mo=slow_mo,
        timeout_ms=timeout_ms,
        viewport_name=viewport_name,
        viewport=_viewport_dict(viewport_name),
        screenshot_dir=screenshot_dir or _SCREENSHOT_DIR,
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
            for sid in selected:
                if sid == "j5":
                    row_m = _run_scenario(
                        "j5",
                        scenario_j5_monica,
                        cfg,
                        browser,
                        context_token=cfg.monica_token,
                    )
                    row_m["persona"] = "monica"
                    results.append(row_m)
                    row_a = _run_scenario("j5", scenario_j5_anon, cfg, browser)
                    row_a["persona"] = "anon"
                    results.append(row_a)
                    continue
                ctx_token: str | None = None
                if sid in ("j4", "j6"):
                    ctx_token = cfg.preprod_token
                fn = SCENARIOS[sid]
                results.append(
                    _run_scenario(sid, fn, cfg, browser, context_token=ctx_token)
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
        "artifacts_dir": str((screenshot_dir or _SCREENSHOT_DIR).relative_to(_ROOT)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="O218 quiz E2E j1–j7")
    parser.add_argument("--base-url", default="https://rawlead.ru")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--slow-mo", type=int, default=0)
    parser.add_argument("--timeout-ms", type=int, default=45_000)
    parser.add_argument("--viewport", choices=("desktop", "mobile"), default="desktop")
    parser.add_argument("--ids", help="Comma-separated j1..j7")
    parser.add_argument(
        "--output-json",
        type=Path,
        default=_ARTIFACT_JSON,
    )
    args = parser.parse_args()

    try:
        ids = _resolve_ids(args.viewport, args.ids)
        report = run_quiz_e2e(
            base_url=args.base_url,
            headless=not args.headed,
            slow_mo=args.slow_mo,
            timeout_ms=args.timeout_ms,
            viewport_name=args.viewport,
            ids=ids,
        )
    except ImportError:
        print(
            "playwright не установлен: pip install playwright && playwright install chromium",
            file=sys.stderr,
        )
        return 2
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
