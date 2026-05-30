"""O37b b4: UX review ПК (1440) + мобила (390) → data/preprod_ux_review.md."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
_PLAYWRIGHT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_PLAYWRIGHT_DIR))

import ux_journey  # noqa: E402

_REVIEW_DIR = _ROOT / "data" / "preprod_ux_review"
_DEFAULT_MD = _ROOT / "data" / "preprod_ux_review.md"


def _rating(pass_ok: bool, critical: int, warnings: int) -> int:
    if critical:
        return 1
    if not pass_ok:
        return 2
    if warnings:
        return 4
    return 5


def _run_viewport_review(
    base_url: str,
    *,
    label: str,
    width: int,
    height: int,
    browser_name: str,
    headless: bool,
    access_token: str | None,
) -> dict:
    from playwright.sync_api import sync_playwright

    base = base_url.rstrip("/")
    shots: list[str] = []
    notes: list[str] = []
    critical = 0

    with sync_playwright() as p:
        browser, context = ux_journey._launch_playwright_context(
            p,
            browser_name=browser_name,
            headless=headless,
            viewport={"width": width, "height": height},
            storage_state=None,
            access_token=access_token,
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(45_000)

        for path, name in (
            ("/", "home"),
            ("/lenta/", "lenta"),
            ("/cabinet/", "cabinet"),
        ):
            try:
                page.goto(f"{base}{path}", wait_until="domcontentloaded")
                page.wait_for_timeout(800)
                _REVIEW_DIR.mkdir(parents=True, exist_ok=True)
                fname = f"{label}_{name}.png"
                out = _REVIEW_DIR / fname
                page.screenshot(path=str(out), full_page=True)
                shots.append(str(out.relative_to(_ROOT)).replace("\\", "/"))
            except Exception as exc:
                critical += 1
                notes.append(f"{path}: {exc}")

        if label == "desktop":
            page.goto(f"{base}/lenta/", wait_until="domcontentloaded")
            card = page.locator(".rl-lead-card").first
            if card.count():
                card.click()
                page.wait_for_timeout(500)
                page.mouse.click(10, 10)
                page.wait_for_timeout(400)
                if page.locator(".rl-lead-card.is-expanded").count():
                    notes.append("tap outside: карточка не свернулась")
            else:
                notes.append("лента: нет карточек для expand/tap-outside")

        if browser_name in ("cdp", "dolphin-cdp", "yandex-cdp"):
            if browser is not None:
                browser.close()
        elif browser is not None:
            browser.close()
        else:
            context.close()

    ok = critical == 0
    return {
        "label": label,
        "viewport": f"{width}x{height}",
        "screenshots": shots,
        "notes": notes,
        "critical": critical,
        "rating": _rating(ok, critical, len(notes)),
        "ok": ok,
    }


def _write_markdown(sections: list[dict], *, base_url: str, browser: str) -> str:
    lines = [
        "# Pre-prod UX review (O37b)",
        "",
        f"- **URL:** {base_url}",
        f"- **Time:** {datetime.now(timezone.utc).isoformat()}",
        f"- **Browser:** {browser}",
        "",
    ]
    for sec in sections:
        lines.append(f"## {sec['label'].title()} ({sec['viewport']}) — **{sec['rating']}/5**")
        lines.append("")
        if sec["ok"]:
            lines.append("**OK**")
        else:
            lines.append("**Критично**" if sec["critical"] else "**Замечания**")
        lines.append("")
        if sec["screenshots"]:
            lines.append("### Скрины (full-page)")
            for s in sec["screenshots"]:
                lines.append(f"- `{s}`")
            lines.append("")
        if sec["notes"]:
            lines.append("### Замечания")
            for n in sec["notes"]:
                lines.append(f"- {n}")
            lines.append("")
    crit = [n for s in sections for n in s["notes"] if s["critical"]]
    lines.append("## Сводка")
    lines.append("")
    lines.append(
        f"- **ПК:** {sections[0]['rating']}/5 · **Мобила:** {sections[1]['rating']}/5"
    )
    if crit:
        lines.append("- **Критично:** см. разделы выше")
    else:
        lines.append("- **Критично:** нет (авто-обход главных страниц)")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="O37b UX review PC+mobile")
    parser.add_argument("--base-url", default="https://rawlead.ru")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument(
        "--browser",
        default="cdp",
        choices=("chromium", "cdp", "dolphin-cdp", "yandex-cdp"),
    )
    parser.add_argument("--output", type=Path, default=_DEFAULT_MD)
    parser.add_argument("--cdp-url", default="")
    args = parser.parse_args()

    if args.cdp_url.strip():
        os.environ["DOLPHIN_CDP_URL"] = args.cdp_url.strip()

    token = (
        os.environ.get("RAWLEAD_PREPROD_ACCESS_TOKEN", "").strip()
        or ux_journey._load_token_from_env_files()
        or None
    )
    browser_label = ux_journey._browser_report_label(args.browser, token)

    desktop = _run_viewport_review(
        args.base_url,
        label="desktop",
        width=1440,
        height=900,
        browser_name=args.browser,
        headless=not args.headed,
        access_token=token,
    )
    mobile = _run_viewport_review(
        args.base_url,
        label="mobile",
        width=390,
        height=844,
        browser_name=args.browser,
        headless=not args.headed,
        access_token=token,
    )
    md = _write_markdown([desktop, mobile], base_url=args.base_url, browser=browser_label)
    args.output.write_text(md, encoding="utf-8")
    print(md)
    ok = desktop["ok"] and mobile["ok"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
