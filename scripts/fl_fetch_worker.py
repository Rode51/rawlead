#!/usr/bin/env python3
"""FL listing fetch worker — clean subprocess (O193)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(_SRC))

from exchange_browser_fetch import fetch_fl_listing_ephemeral_standalone  # noqa: E402
from html_fetch import HtmlFetchError  # noqa: E402


def _emit(payload: dict, *, json_mode: bool, code: int) -> None:
    if json_mode:
        print(json.dumps(payload, ensure_ascii=False))
    elif payload.get("ok"):
        print("OK html_len", payload.get("html_len", 0))
    else:
        print("FAIL", payload.get("error", "unknown"))
    raise SystemExit(code)


def main() -> int:
    parser = argparse.ArgumentParser(description="FL listing fetch worker")
    parser.add_argument("--url", required=True)
    parser.add_argument("--proxy", default="")
    parser.add_argument("--user-agent", required=True)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        html = fetch_fl_listing_ephemeral_standalone(
            args.url,
            user_agent=args.user_agent,
            timeout_sec=args.timeout,
            proxy_url=args.proxy,
        )
        _emit(
            {"ok": True, "html": html, "html_len": len(html)},
            json_mode=args.json,
            code=0,
        )
    except HtmlFetchError as exc:
        _emit({"ok": False, "error": str(exc)}, json_mode=args.json, code=1)
    except Exception as exc:
        _emit(
            {"ok": False, "error": f"{type(exc).__name__}: {exc}"},
            json_mode=args.json,
            code=1,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
