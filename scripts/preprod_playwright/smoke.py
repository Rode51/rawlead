"""§ PRE-PROD-STRESS t3: Playwright smoke на prod/staging URL (5 сценариев).

  .venv\\Scripts\\python.exe scripts\\preprod_playwright\\smoke.py
  .venv\\Scripts\\python.exe scripts\\preprod_playwright\\smoke.py --base-url https://rawlead.ru

Требует: pip install playwright && playwright install chromium
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

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


def _scenario(name: str, fn) -> dict:
    t0 = time.perf_counter()
    try:
        fn()
        ms = int((time.perf_counter() - t0) * 1000)
        return {"name": name, "pass": True, "ms": ms, "error": None}
    except Exception as exc:  # noqa: BLE001 — smoke report
        ms = int((time.perf_counter() - t0) * 1000)
        return {"name": name, "pass": False, "ms": ms, "error": str(exc)}


def run_smoke(base_url: str, headless: bool, timeout_ms: int) -> list[dict]:
    from playwright.sync_api import sync_playwright

    base = base_url.rstrip("/")
    results: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="ru-RU",
        )
        page = context.new_page()
        page.set_default_timeout(timeout_ms)

        def s1_lenta_loads() -> None:
            page.goto(f"{base}/lenta/", wait_until="domcontentloaded")
            page.wait_for_selector('[data-rl-app="feed"]', state="visible")
            err = page.locator("#rl-feed-error:not([hidden])")
            if err.count() and err.is_visible():
                raise RuntimeError(f"feed error banner: {err.inner_text()[:200]}")
            # карточки или empty — оба ок
            page.wait_for_selector(
                feed_ui.FEED_READY,
                timeout=timeout_ms,
            )

        def s2_multi_category() -> None:
            page.goto(f"{base}/lenta/", wait_until="domcontentloaded")
            page.wait_for_selector("#filter-category-design", state="visible")
            before = page.locator("#rl-feed-list .rl-lead-card").count()
            page.locator("#filter-category-design input").check(force=True)
            page.wait_for_timeout(800)
            meta = page.locator(feed_ui.FEED_META)
            if meta.count():
                text = meta.inner_text()
            else:
                text = ""
            if "ошиб" in text.casefold():
                raise RuntimeError(f"count after category: {text}")
            # сеть могла вернуть 0 — допустимо, главное без error banner
            err = page.locator("#rl-feed-error:not([hidden])")
            if err.count() and err.is_visible():
                raise RuntimeError("error after category filter")
            _ = before  # noqa: F841 — для отладки владельца

        def s3_skills_apply() -> None:
            page.goto(f"{base}/lenta/", wait_until="domcontentloaded")
            page.wait_for_selector(feed_ui.FEED_READY, timeout=timeout_ms)
            if feed_ui.is_filter_locked(page, "skills"):
                return  # anon: locked — ожидаемо
            feed_ui.open_skills_modal(page)
            feed_ui.pick_first_skill_chip(page)
            feed_ui.apply_skills_modal(page)
            page.wait_for_timeout(1000)
            err = page.locator("#rl-feed-error:not([hidden])")
            if err.count() and err.is_visible():
                raise RuntimeError("error after skills apply")

        def s4_cabinet_login_stub() -> None:
            page.goto(f"{base}/cabinet/", wait_until="domcontentloaded")
            page.wait_for_selector('[data-rl-app="cabinet"]', state="visible")
            page.wait_for_selector("#rl-cabinet-login", state="visible")
            title = page.locator(".rl-cabinet-login__title")
            if "кабинет" not in title.inner_text().casefold():
                raise RuntimeError("cabinet login block missing")

        def s5_no_verdict_chips() -> None:
            page.goto(f"{base}/lenta/", wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            cards = page.locator("#rl-feed-list .rl-lead-card")
            n = cards.count()
            if n == 0:
                return
            for i in range(min(n, 5)):
                card = cards.nth(i)
                text = card.inner_text().casefold()
                for bad in ("брать", "не брать", "сомнительно"):
                    if bad in text:
                        raise RuntimeError(f"verdict chip visible: {bad!r}")

        for name, fn in (
            ("lenta_loads", s1_lenta_loads),
            ("multi_category", s2_multi_category),
            ("skills_apply", s3_skills_apply),
            ("cabinet_login_stub", s4_cabinet_login_stub),
            ("no_verdict_chips", s5_no_verdict_chips),
        ):
            results.append(_scenario(name, fn))

        browser.close()

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="PRE-PROD Playwright smoke")
    parser.add_argument("--base-url", default="https://rawlead.ru")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=30000)
    parser.add_argument(
        "--output",
        type=Path,
        default=_ROOT / "data" / "preprod_playwright_report.json",
    )
    args = parser.parse_args()

    try:
        results = run_smoke(args.base_url, headless=not args.headed, timeout_ms=args.timeout_ms)
    except ImportError:
        print("playwright не установлен: pip install playwright && playwright install chromium", file=sys.stderr)
        return 2

    passed = sum(1 for r in results if r["pass"])
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url.rstrip("/"),
        "scenarios_total": len(results),
        "scenarios_pass": passed,
        "s2_pass": all(r["pass"] for r in results),
        "results": results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["s2_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
