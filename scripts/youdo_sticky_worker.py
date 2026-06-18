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
