#!/usr/bin/env python3
"""YouDo long-lived Camoufox sticky session worker (O266/O267 persistent profile)."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(_SRC))

from exchange_browser_fetch import (  # noqa: E402
    _check_camoufox_playwright_compat,
    _log_youdo_browser_trace,
    _validate_youdo_html,
    _youdo_goto_wait_until_for_attempt,
    _youdo_headless,
    _youdo_html_is_servicepipe,
    _youdo_launch_extra_kw,
    _youdo_listing_goto_timeout_ms,
    _youdo_persistent_profile_dir,
    _youdo_sticky_reload_sp_abort_sec,
    _youdo_sticky_reload_wait_until,
    _youdo_wait_listing_ready_async,
    pick_browser_user_agent,
    youdo_persistent_profile_enabled,
)
from html_fetch import HtmlFetchError, _playwright_proxy  # noqa: E402


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False), flush=True)


async def _run_listing_fetch(
    page: Any,
    *,
    url: str,
    tier: str,
    timeout_sec: float,
    proxy_url: str,
    stage: str,
) -> dict[str, Any]:
    timeout_ms = max(int(timeout_sec * 1000), 5000)
    listing_timeout_ms = _youdo_listing_goto_timeout_ms(timeout_sec)
    if stage == "sticky_reload":
        listing_timeout_ms = min(
            listing_timeout_ms,
            int(_youdo_sticky_reload_sp_abort_sec() * 1000),
        )
    goto_t0 = time.monotonic()
    list_view_results: list[Any] = []
    if stage == "sticky_goto":
        await page.goto(
            url,
            wait_until=_youdo_goto_wait_until_for_attempt(1),
            timeout=listing_timeout_ms,
        )
    else:
        await page.reload(
            wait_until=_youdo_sticky_reload_wait_until(),
            timeout=listing_timeout_ms,
        )
    html_after_nav = await page.content()
    if stage == "sticky_reload" and _youdo_html_is_servicepipe(html_after_nav):
        raise HtmlFetchError(
            "ServicePipe antibot challenge (youdo sticky reload fast-fail)."
        )
    await _youdo_wait_listing_ready_async(
        page,
        listing_timeout_ms,
        list_view_out=list_view_results,
        tier=tier,
    )
    html = await page.content()
    goto_ms = int((time.monotonic() - goto_t0) * 1000)
    _validate_youdo_html(html, proxy_url)
    _log_youdo_browser_trace(
        launch_ms=0,
        goto_ms=goto_ms,
        status="200",
        html_len=len(html),
        antibot_hit=False,
    )
    list_view = list_view_results[-1] if list_view_results else None
    payload: dict[str, Any] = {
        "html": html,
        "stage": stage,
        "goto_ms": goto_ms,
        "html_len": len(html),
    }
    if list_view is not None:
        payload["list_view_clicked"] = int(getattr(list_view, "clicked", False))
        payload["data_id_count"] = int(getattr(list_view, "data_id_count", 0))
    return payload


# --- Click-through detail (§ YOUDO-DETAIL-BREAKTHROUGH) ---

_DESC_SELECTORS = [
    '[class*="TaskDescription"]',
    '[class*="Description_text"]',
    '[class*="taskDescription"]',
    '[class*="TaskNeed"]',
    '[class*="Need_text"]',
    ".task-description",
    "article",
]


def _parse_detail_body(html: str) -> str:
    """Extract description text from detail page HTML (sync fallback)."""
    from bs4 import BeautifulSoup

    if not html or not html.strip():
        return ""
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if script and script.string:
        try:
            import json as _json

            payload = _json.loads(script.string)
            props = payload.get("props", {}).get("pageProps", {})
            for key in ("task", "taskData", "data"):
                block = props.get(key)
                if isinstance(block, dict):
                    for field in ("description", "text", "content", "body"):
                        val = block.get(field)
                        if isinstance(val, str) and len(val.strip()) > 100:
                            return val.strip()
        except Exception:
            pass
    for sel in _DESC_SELECTORS:
        for node in soup.select(sel):
            text = node.get_text("\n", strip=True)
            if len(text) > 100:
                return text
    return ""


async def _run_click_through_details(
    page: Any,
    *,
    lead_ids: list[str],
    listing_url: str,
    timeout_sec: float,
    proxy_url: str,
) -> dict[str, Any]:
    """Click through to detail pages for new leads in the same sticky session."""
    import random as _rng

    t0 = time.monotonic()
    results: dict[str, dict[str, Any]] = {}
    listing_url = listing_url or await page.evaluate("() => window.location.href")

    for idx, ext_id in enumerate(lead_ids[:10]):  # cap 10
        # Inter-card jitter (human-like: 1.5-4s between clicks)
        if idx > 0:
            await page.wait_for_timeout(_rng.randint(1500, 4000))

        lead_t0 = time.monotonic()
        outcome = "selector_miss"
        body = ""
        clicked = False
        selector_used = ""
        fallback_goto = False
        debug_path = ""

        # Find card by data-id or href /t{id}
        card = None
        for sel in (
            f'a[data-id="{ext_id}"]',
            f'a[href*="/t{ext_id}"]',
            f'[data-id="{ext_id}"]',
        ):
            loc = page.locator(sel)
            if await loc.count() > 0:
                card = loc.first
                selector_used = sel.split("[")[0] if "[" in sel else sel
                break

        if card is None:
            outcome = "selector_miss"
            results[ext_id] = {
                "outcome": outcome,
                "selector": selector_used or "none",
                "clicked": 0,
                "body_len": 0,
                "ms": int((time.monotonic() - lead_t0) * 1000),
                "fallback": "",
                "debug_path": "",
            }
            continue

        # Hover before click (human-like)
        try:
            await card.hover(timeout=3000)
            await page.wait_for_timeout(_rng.randint(300, 800))
        except Exception:
            pass

        # Click the card
        try:
            await card.click(timeout=5000)
            clicked = True
        except Exception:
            outcome = "click_fail"
            results[ext_id] = {
                "outcome": outcome,
                "selector": selector_used,
                "clicked": 0,
                "body_len": 0,
                "ms": int((time.monotonic() - lead_t0) * 1000),
                "fallback": "",
                "debug_path": "",
            }
            continue

        # Wait for description to appear
        detail_html = ""
        sp_on_click = False
        try:
            for desc_sel in _DESC_SELECTORS:
                try:
                    await page.wait_for_selector(desc_sel, timeout=8000)
                    break
                except Exception:
                    continue
            detail_html = await page.content()
            body = _parse_detail_body(detail_html)
            sp_on_click = "ServicePipe" in (detail_html or "") or len(detail_html or "") < 2000
        except Exception:
            outcome = "parse_fail"

        if body and len(body) >= 100:
            outcome = "ok"
        elif sp_on_click:
            outcome = "antibot"
        elif not body:
            outcome = "empty_body"

        # On SP/click fail: try go_back() in same tab (don't tear down sticky)
        if outcome in ("antibot", "click_fail", "parse_fail", "empty_body"):
            try:
                await page.go_back(wait_until="domcontentloaded", timeout=10000)
                await page.wait_for_timeout(1500)
                back_html = await page.content()
                if "ServicePipe" not in (back_html or "") and len(back_html or "") > 5000:
                    outcome = "go_back_ok"
            except Exception:
                pass

        # Fallback: goto /t{id} in same session (last resort)
        if outcome != "ok":
            fallback_goto = True
            detail_url = f"https://youdo.com/t{ext_id}"
            try:
                await page.goto(detail_url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(2000)
                detail_html = await page.content()
                body = _parse_detail_body(detail_html)
                if body and len(body) >= 100:
                    outcome = "fallback_ok"
                elif "ServicePipe" in (detail_html or "") or len(detail_html or "") < 2000:
                    outcome = "fallback_antibot"
                else:
                    outcome = "fallback_empty"
            except Exception:
                outcome = "fallback_fail"

            # Navigate back to listing
            try:
                await page.goto(listing_url, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(2000)
            except Exception:
                pass

        if outcome not in ("ok", "fallback_ok") and debug_path == "":
            try:
                debug_path = f"/opt/rawlead/data/debug_listings/youdo_click_miss_{ext_id}.html"
            except Exception:
                pass

        results[ext_id] = {
            "outcome": outcome,
            "selector": selector_used,
            "clicked": 1 if clicked else 0,
            "body_len": len(body),
            "body": body[:2000] if body else "",
            "ms": int((time.monotonic() - lead_t0) * 1000),
            "fallback": "goto" if fallback_goto else "",
            "debug_path": debug_path,
        }

    total_ms = int((time.monotonic() - t0) * 1000)
    ok_count = sum(1 for r in results.values() if r["outcome"] in ("ok", "fallback_ok"))
    return {
        "stage": "click_through_details",
        "results": results,
        "ok_count": ok_count,
        "total_count": len(lead_ids),
        "total_ms": total_ms,
    }


async def _session_loop(*, proxy_url: str, user_agent: str) -> int:
    _check_camoufox_playwright_compat()
    try:
        from camoufox.async_api import AsyncCamoufox
    except ImportError as exc:
        _emit({"error": f"Camoufox missing: {exc}"})
        return 1

    ua = pick_browser_user_agent(user_agent)
    px = _playwright_proxy(proxy_url)
    launch_kw: dict[str, Any] = {"headless": _youdo_headless()}
    launch_kw.update(_youdo_launch_extra_kw())
    if px:
        launch_kw["proxy"] = px

    use_persistent = youdo_persistent_profile_enabled()
    profile_dir: Path | None = None
    if use_persistent:
        profile_dir = _youdo_persistent_profile_dir(proxy_url)
        profile_dir.mkdir(parents=True, exist_ok=True)
        launch_kw["persistent_context"] = True
        launch_kw["user_data_dir"] = str(profile_dir)

    browser = None
    try:
        async with AsyncCamoufox(**launch_kw) as browser_or_ctx:
            if use_persistent:
                ctx = browser_or_ctx
                page = await ctx.new_page()
            else:
                ctx = await browser_or_ctx.new_context(
                    user_agent=ua,
                    locale="ru-RU",
                    timezone_id="Europe/Moscow",
                    viewport={"width": 1366, "height": 768},
                )
                page = await ctx.new_page()
            while True:
                line = await asyncio.to_thread(sys.stdin.readline)
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    req = json.loads(line)
                except json.JSONDecodeError as je:
                    _emit({"error": f"bad request json: {je}"})
                    continue
                cmd = str(req.get("cmd") or "").strip().lower()
                if cmd == "teardown":
                    _emit({"stage": "sticky_teardown", "ok": 1})
                    break
                if cmd == "ping":
                    _emit({"stage": "sticky_ping", "ok": 1})
                    continue
                if cmd == "click_through_details":
                    lead_ids_raw = req.get("lead_ids") or []
                    lead_ids = [str(x) for x in lead_ids_raw if x]
                    listing_url_cmd = str(req.get("listing_url") or "").strip()
                    timeout_ct = float(req.get("timeout") or 60.0)
                    try:
                        payload = await _run_click_through_details(
                            page,
                            lead_ids=lead_ids,
                            listing_url=listing_url_cmd,
                            timeout_sec=timeout_ct,
                            proxy_url=proxy_url,
                        )
                        if profile_dir is not None:
                            payload["profile_dir"] = str(profile_dir)
                        _emit(payload)
                    except Exception as exc:
                        _emit({
                            "error": f"{type(exc).__name__}: {exc}",
                            "stage": "click_through_details",
                        })
                    continue
                url = str(req.get("url") or "").strip()
                tier = str(req.get("tier") or "dc").strip() or "dc"
                timeout_sec = float(req.get("timeout") or 150.0)
                if cmd not in ("goto", "reload"):
                    _emit({"error": f"unknown cmd: {cmd}"})
                    continue
                if not url:
                    _emit({"error": "missing url"})
                    continue
                stage = "sticky_goto" if cmd == "goto" else "sticky_reload"
                try:
                    payload = await _run_listing_fetch(
                        page,
                        url=url,
                        tier=tier,
                        timeout_sec=timeout_sec,
                        proxy_url=proxy_url,
                        stage=stage,
                    )
                    if profile_dir is not None:
                        payload["profile_dir"] = str(profile_dir)
                    _emit(payload)
                except HtmlFetchError as exc:
                    err_payload: dict[str, Any] = {"error": str(exc), "stage": stage}
                    if profile_dir is not None:
                        err_payload["profile_dir"] = str(profile_dir)
                    _emit(err_payload)
                except Exception as exc:
                    err_payload = {
                        "error": f"{type(exc).__name__}: {exc}",
                        "stage": stage,
                    }
                    if profile_dir is not None:
                        err_payload["profile_dir"] = str(profile_dir)
                    _emit(err_payload)
    finally:
        pass
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="YouDo sticky Camoufox worker")
    parser.add_argument("--proxy", required=True)
    parser.add_argument("--user-agent", required=True)
    args = parser.parse_args()
    os.environ.setdefault(
        "YOUDO_STICKY_RELOAD_WAIT_UNTIL",
        _youdo_sticky_reload_wait_until(),
    )
    return asyncio.run(
        _session_loop(proxy_url=args.proxy, user_agent=args.user_agent)
    )


if __name__ == "__main__":
    raise SystemExit(main())
