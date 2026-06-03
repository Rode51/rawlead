#!/usr/bin/env python3
"""O96-D: Playwright snapshot prod для Design — все зоны O96-Z1–Z10.

  .venv\\Scripts\\python.exe scripts\\preprod_playwright\\o96_design_survey.py
  .venv\\Scripts\\python.exe scripts\\preprod_playwright\\o96_design_survey.py --headed

Logged-in (Z3/Z4/Z6/Z7): RAWLEAD_PREPROD_ACCESS_TOKEN в .env / .env.site
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent.parent
_PW = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_PW))

import ux_journey  # noqa: E402

_OUT = _ROOT / "data" / "o96_design_survey"
_REPORT = _ROOT / "data" / "o96_design_survey.md"
_JSON = _ROOT / "data" / "o96_design_survey.json"

_PAGES = (
    ("/", "Z1_home"),
    ("/lenta/", "Z2_lenta_anon"),
    ("/cabinet/", "Z5_cabinet"),
    ("/pricing/", "Z8_pricing"),
    ("/how/", "Z9_how"),
    ("/faq/", "Z10_faq"),
)


def _text(page: Any, sel: str, limit: int = 400) -> str:
    loc = page.locator(sel).first
    if not loc.count():
        return ""
    try:
        return (loc.inner_text() or "").strip()[:limit]
    except Exception:
        return ""


def _shot(page: Any, name: str) -> str:
    _OUT.mkdir(parents=True, exist_ok=True)
    path = _OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    return str(path.relative_to(_ROOT)).replace("\\", "/")


def _survey_viewport(
    base: str,
    *,
    label: str,
    width: int,
    height: int,
    token: str | None,
    headless: bool,
    anon_only: bool,
) -> list[dict[str, Any]]:
    from playwright.sync_api import sync_playwright

    rows: list[dict[str, Any]] = []
    with sync_playwright() as p:
        browser, context = ux_journey._launch_playwright_context(
            p,
            browser_name="chromium",
            headless=headless,
            viewport={"width": width, "height": height},
            storage_state=None,
            access_token=None if anon_only else token,
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(45_000)

        pages = _PAGES if anon_only else (("/lenta/", "Z3_lenta_logged"), ("/cabinet/", "Z6_Z7_cabinet_logged"))

        for path, zone in pages:
            url = f"{base}{path}"
            row: dict[str, Any] = {"zone": zone, "path": path, "viewport": label, "url": url}
            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(900)
                row["screenshot"] = _shot(page, f"{label}_{zone}")
                if path == "/":
                    row["title"] = page.title()
                    row["h1"] = _text(page, ".rl-hero__title, h1")
                elif path == "/lenta/":
                    row["count"] = _text(page, "#rl-feed-count")
                    row["delay_strip"] = _text(page, ".rl-feed-delay-notice, .rl-feed-notice")
                    if not anon_only:
                        cards = page.locator("#rl-feed-list .rl-lead-card[data-id]")
                        if cards.count():
                            card = cards.first
                            card.locator(".rl-lead-card__title").first.click()
                            page.wait_for_timeout(500)
                            row["card_shot"] = _shot(page, f"{label}_Z3_card_expanded")
                            row["match_block"] = _text(page, ".rl-match, .rl-match-breakdown")
                elif path == "/cabinet/":
                    row["mode"] = (
                        "logged_in"
                        if page.locator("#rl-cabinet-app").count()
                        and page.locator("#rl-cabinet-app").is_visible()
                        else "anon"
                    )
                    row["headline"] = _text(page, ".rl-cabinet-login__title, .rl-cabinet-app h1, h1")
                elif path == "/pricing/":
                    row["h1"] = _text(page, "h1")
                    row["sub"] = _text(page, ".rl-pricing__lead, .rl-page-lead")
                row["ok"] = True
            except Exception as exc:
                row["ok"] = False
                row["error"] = str(exc)
            rows.append(row)

        if token and not anon_only:
            try:
                page.goto(f"{base}/lenta/", wait_until="domcontentloaded")
                page.wait_for_timeout(1500)
                edit = page.locator("#rl-feed-tags-edit")
                if edit.count() and edit.first.is_visible():
                    edit.first.click()
                    page.wait_for_timeout(800)
                    modal = page.locator("#rl-feed-skills-modal")
                    if modal.count() and modal.first.get_attribute("hidden") is None:
                        rows.append(
                            {
                                "zone": "Z4_skill_tree",
                                "path": "/lenta/ modal",
                                "viewport": label,
                                "screenshot": _shot(page, f"{label}_Z4_skill_modal"),
                                "counter": _text(page, "#rl-feed-skill-tree-counter"),
                                "ok": True,
                            }
                        )
            except Exception as exc:
                rows.append(
                    {
                        "zone": "Z4_skill_tree",
                        "viewport": label,
                        "ok": False,
                        "error": str(exc),
                    }
                )

        if browser is not None:
            browser.close()
        else:
            context.close()
    return rows


def _write_md(report: dict[str, Any]) -> None:
    lines = [
        "# O96-D Design survey (Playwright prod snapshot)",
        "",
        f"- **Time:** {report['generated_at']}",
        f"- **URL:** {report['base_url']}",
        f"- **Auth:** {report['has_auth']}",
        f"- **Copy canon:** `docs/team/product/LEAD_PRODUCT_PROMPT.md` § O96-Z1–Z13",
        "",
        "## Как пользоваться Design",
        "",
        "1. Открой скрины в `data/o96_design_survey/` (desktop + mobile).",
        "2. Сверь **prod copy** в таблице ниже с **каноном O96** — gap = scope UI/copy.",
        "3. Фаза 1: совет с владельцем **без новых docs** → потом спеки.",
        "",
        "## Snapshots",
        "",
        "| Zone | Viewport | Path | Screenshot | Prod snippet |",
        "|------|----------|------|------------|--------------|",
    ]
    for r in report["rows"]:
        if not r.get("ok"):
            lines.append(
                f"| {r.get('zone','?')} | {r.get('viewport','?')} | {r.get('path','?')} | ❌ | {r.get('error','')} |"
            )
            continue
        shot = r.get("screenshot") or r.get("card_shot") or "—"
        snippet = (
            r.get("count")
            or r.get("h1")
            or r.get("headline")
            or r.get("title")
            or r.get("match_block")
            or "—"
        )
        snippet = str(snippet).replace("|", "/").replace("\n", " ")[:120]
        lines.append(
            f"| {r['zone']} | {r['viewport']} | {r.get('path','')} | `{shot}` | {snippet} |"
        )
    lines.extend(
        [
            "",
            "## Design scope (владелец 2026-06-02)",
            "",
            "- UX всех страниц · карточки не «навалено»",
            "- **Категория/ниша на карточке**",
            "- Badge O97 (концепт 2) · Skill Tree O98-w",
            "",
        ]
    )
    _REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="O96-D design survey")
    parser.add_argument("--base-url", default="https://rawlead.ru")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    token = (
        os.environ.get("RAWLEAD_PREPROD_ACCESS_TOKEN", "").strip()
        or ux_journey._load_token_from_env_files()
        or None
    )
    base = args.base_url.rstrip("/")
    all_rows: list[dict[str, Any]] = []
    for label, w, h in (("desktop", 1440, 900), ("mobile", 390, 844)):
        all_rows.extend(
            _survey_viewport(
                base, label=label, width=w, height=h, token=token, headless=not args.headed, anon_only=True
            )
        )
        if token:
            all_rows.extend(
                _survey_viewport(
                    base, label=label, width=w, height=h, token=token, headless=not args.headed, anon_only=False
                )
            )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base,
        "has_auth": bool(token),
        "rows": all_rows,
        "artifacts_dir": str(_OUT.relative_to(_ROOT)).replace("\\", "/"),
    }
    _JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_md(report)
    ok = sum(1 for r in all_rows if r.get("ok"))
    print(json.dumps({"pass": ok == len(all_rows), "ok": ok, "total": len(all_rows), "report": str(_REPORT)}, ensure_ascii=False))
    return 0 if ok == len(all_rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
