#!/usr/bin/env python3
"""O262k: DC-only YouDo listing probe — what HTML does DC proxy slot 1 return?

Camoufox (prod path) via youdo_fetch_worker. Optional Playwright Chromium compare.
No RU carousel — DC slot 1 only, tier=dc.

Usage:
  python scripts/probe_youdo_dc_page.py
  python scripts/probe_youdo_dc_page.py --chromium
  python scripts/probe_youdo_dc_page.py --json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.site", override=True)

from config import load_config, load_radar_env  # noqa: E402
from exchange_browser_fetch import (  # noqa: E402
    _fetch_youdo_ephemeral,
    _youdo_html_has_task_cards,
    _youdo_html_is_servicepipe,
    pick_browser_user_agent,
)
from exchange_proxy import _hint_from_url, _youdo_dc_pool  # noqa: E402
from html_fetch import HtmlFetchError  # noqa: E402
from youdo_parser import _listing_url, _save_listing_html_debug  # noqa: E402

_WORKER = _ROOT / "scripts" / "youdo_fetch_worker.py"
_TASK_LINK_RE = re.compile(r'data-id=["\']?(\d+)["\']?', re.I)
_DEFAULT_TIMEOUT = 150.0


def _data_id_count(html: str) -> int:
    ids = {m.group(1) for m in _TASK_LINK_RE.finditer(html or "")}
    return len(ids)


def _detect_view_mode(html: str) -> str:
    low = (html or "").casefold()
    if _youdo_html_is_servicepipe(html) or "servicepipe" in low:
        return "servicepipe"
    if _youdo_html_has_task_cards(html):
        return "list"
    if "показать списком" in low:
        return "map"
    if "exhkqyad" in low or "just a moment" in low:
        return "antibot"
    return "unknown"


def analyze_html(html: str) -> dict[str, Any]:
    low = (html or "").casefold()
    flags = {
        "servicepipe": _youdo_html_is_servicepipe(html) or "servicepipe" in low,
        "pokazat_spiskom": "показать списком" in low,
        "data_id_count": _data_id_count(html),
        "has_task_cards": _youdo_html_has_task_cards(html),
        "view_mode": _detect_view_mode(html),
    }
    compact = re.sub(r"\s+", " ", (html or "")).strip()
    snippet = compact[:800] if len(compact) >= 500 else compact
    if len(snippet) < 500 and len(compact) > len(snippet):
        snippet = compact[: min(800, len(compact))]
    return {
        "html_len": len(html or ""),
        "snippet": snippet,
        "flags": flags,
    }


def _dc_slot1() -> str:
    pool = _youdo_dc_pool()
    if not pool:
        raise SystemExit(
            "FAIL — DC pool empty (set YOUDO_DC_PROXY_URLS + YOUDO_O191_DC_SLOTS=4)"
        )
    return pool[0]


def _fetch_camoufox(
    url: str,
    proxy_url: str,
    *,
    user_agent: str,
    timeout_sec: float,
) -> tuple[str, dict[str, Any]]:
    cmd = [
        sys.executable,
        str(_WORKER),
        "--url",
        url,
        "--proxy",
        proxy_url,
        "--user-agent",
        user_agent,
        "--timeout",
        str(int(timeout_sec)),
        "--stage",
        "listing",
        "--slot-attempt",
        "1",
        "--tier",
        "dc",
        "--json",
    ]
    env = {
        **os.environ,
        "PYTHONPATH": str(_ROOT / "src"),
        "YOUDO_FETCH_TIER": "dc",
        "YOUDO_PROBE_SKIP_VALIDATE": "1",
    }
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_sec + 45,
        env=env,
        cwd=str(_ROOT),
    )
    lines = (proc.stdout or "").strip().splitlines()
    if proc.returncode != 0 or not lines:
        err = (proc.stderr or "").strip() or "camoufox worker failed"
        for line in reversed(lines):
            try:
                obj = json.loads(line)
                err = str(obj.get("error", err))
                break
            except json.JSONDecodeError:
                if line.strip():
                    err = line.strip()[:300]
                    break
        raise HtmlFetchError(err)
    result = json.loads(lines[-1])
    if "error" in result:
        raise HtmlFetchError(str(result["error"]))
    meta = {
        "list_view_clicked": result.get("list_view_clicked"),
        "list_view_selector": result.get("list_view_selector"),
        "list_view_selector_tier": result.get("list_view_selector_tier"),
        "worker_data_id_count": result.get("data_id_count"),
    }
    return str(result.get("html", "")), meta


def _fetch_chromium(
    url: str,
    proxy_url: str,
    *,
    user_agent: str,
    timeout_sec: float,
) -> str:
    prev = os.environ.get("YOUDO_BROWSER")
    os.environ["YOUDO_BROWSER"] = "playwright"
    os.environ["YOUDO_FETCH_TIER"] = "dc"
    try:
        return _fetch_youdo_ephemeral(
            url,
            user_agent=user_agent,
            timeout_sec=timeout_sec,
            proxy_url=proxy_url,
            stage="listing",
            slot_attempt=1,
            tier="dc",
        )
    finally:
        if prev is None:
            os.environ.pop("YOUDO_BROWSER", None)
        else:
            os.environ["YOUDO_BROWSER"] = prev


def _run_backend(
    backend: str,
    url: str,
    proxy_url: str,
    *,
    user_agent: str,
    timeout_sec: float,
) -> dict[str, Any]:
    hint = _hint_from_url(proxy_url)
    row: dict[str, Any] = {
        "backend": backend,
        "tier": "dc",
        "proxy_hint": hint,
        "url": url,
    }
    try:
        if backend == "camoufox":
            html, worker_meta = _fetch_camoufox(
                url, proxy_url, user_agent=user_agent, timeout_sec=timeout_sec
            )
            row["worker"] = worker_meta
        else:
            html = _fetch_chromium(
                url, proxy_url, user_agent=user_agent, timeout_sec=timeout_sec
            )
        analysis = analyze_html(html)
        tag = f"youdo_dc_probe_{backend}"
        debug_path = _save_listing_html_debug(html, tag=tag)
        row.update(analysis)
        row["debug_path"] = debug_path
        row["ok"] = bool(html)
    except (HtmlFetchError, subprocess.TimeoutExpired, OSError) as exc:
        row["ok"] = False
        row["error"] = str(exc)[:500]
    return row


def probe(*, chromium: bool = False, timeout_sec: float = _DEFAULT_TIMEOUT) -> dict[str, Any]:
    load_radar_env()
    load_config()
    url = _listing_url()
    proxy = _dc_slot1()
    ua = pick_browser_user_agent("")
    dc_slots = os.getenv("YOUDO_O191_DC_SLOTS", "?")
    report: dict[str, Any] = {
        "probe": "o262k_youdo_dc",
        "listing_url": url,
        "dc_slots_env": dc_slots,
        "dc_pool_size": len(_youdo_dc_pool()),
        "proxy_hint": _hint_from_url(proxy),
        "backends": [],
    }
    for backend in ("camoufox", "chromium") if chromium else ("camoufox",):
        report["backends"].append(
            _run_backend(
                backend,
                url,
                proxy,
                user_agent=ua,
                timeout_sec=timeout_sec,
            )
        )
    return report


def _print_human(report: dict[str, Any]) -> None:
    print(f"=== O262k YouDo DC probe (slot 1, no RU) ===")
    print(f"url: {report['listing_url']}")
    print(f"dc_slots: {report['dc_slots_env']} pool={report['dc_pool_size']}")
    print(f"proxy: {report['proxy_hint']}")
    for row in report["backends"]:
        print(f"\n--- {row['backend']} tier={row['tier']} ---")
        if not row.get("ok"):
            print(f"FAIL: {row.get('error', '?')}")
            continue
        flags = row["flags"]
        print(f"html_len: {row['html_len']}")
        print(
            f"flags: servicepipe={flags['servicepipe']} "
            f"pokazat_spiskom={flags['pokazat_spiskom']} "
            f"data_id_count={flags['data_id_count']} "
            f"view_mode={flags['view_mode']}"
        )
        if row.get("worker"):
            w = row["worker"]
            print(
                f"list_view: clicked={w.get('list_view_clicked')} "
                f"selector={w.get('list_view_selector')!r}"
            )
        print(f"debug: {row.get('debug_path')}")
        print(f"snippet:\n{row.get('snippet', '')[:800]}")


def main() -> int:
    parser = argparse.ArgumentParser(description="O262k YouDo DC page probe")
    parser.add_argument(
        "--chromium",
        action="store_true",
        help="Also fetch with Playwright Chromium for compare",
    )
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--timeout",
        type=float,
        default=_DEFAULT_TIMEOUT,
        help=f"Browser timeout sec (default {_DEFAULT_TIMEOUT})",
    )
    args = parser.parse_args()
    report = probe(chromium=args.chromium, timeout_sec=args.timeout)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        _print_human(report)
    ok = any(b.get("ok") for b in report["backends"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
