#!/usr/bin/env python3
"""YouDo camoufox fetch worker — clean subprocess (O190 t0i)."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(_SRC))

from exchange_browser_fetch import _fetch_youdo_camoufox_async  # noqa: E402
from html_fetch import HtmlFetchError  # noqa: E402


def _emit(payload: dict, *, json_mode: bool, code: int) -> None:
    if json_mode:
        print(json.dumps(payload, ensure_ascii=False))
    elif "error" in payload:
        print("FAIL", payload["error"])
    else:
        html = payload.get("html", "")
        print("OK html_len", len(html), "data-id", html.count("data-id"))
    raise SystemExit(code)


def main() -> int:
    parser = argparse.ArgumentParser(description="YouDo camoufox fetch worker")
    parser.add_argument("--url", required=True)
    parser.add_argument("--proxy", required=True)
    parser.add_argument("--user-agent", required=True)
    parser.add_argument("--timeout", type=float, default=150.0)
    parser.add_argument("--stage", default="listing")
    parser.add_argument("--slot-attempt", type=int, default=1)
    parser.add_argument("--tier", default="dc")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    os.environ["YOUDO_FETCH_TIER"] = args.tier.strip() or "dc"

    try:
        fetch_result = asyncio.run(
            _fetch_youdo_camoufox_async(
                args.url,
                user_agent=args.user_agent,
                timeout_sec=args.timeout,
                proxy_url=args.proxy,
                stage=args.stage,
                slot_attempt=args.slot_attempt,
                tier=args.tier,
            )
        )
        payload: dict = {
            "html": fetch_result.html,
            "list_view_clicked": fetch_result.list_view.clicked,
            "data_id_count": fetch_result.list_view.data_id_count,
            "list_view_selector": fetch_result.list_view.selector,
            "list_view_debug_path": fetch_result.list_view.debug_path,
            "list_view_selector_tier": fetch_result.list_view.selector_tier,
            "list_view_target_snip": fetch_result.list_view.target_snip,
        }
        _emit(payload, json_mode=args.json, code=0)
    except HtmlFetchError as exc:
        _emit({"error": str(exc)}, json_mode=args.json, code=1)
    except Exception as exc:
        _emit({"error": f"{type(exc).__name__}: {exc}"}, json_mode=args.json, code=1)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
