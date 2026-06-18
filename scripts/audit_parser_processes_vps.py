#!/usr/bin/env python3
"""O257: Read-only process audit — count fl/youdo/camoufox/chromium orphan PIDs.

Safe to run on VPS without sudo. No secrets in output.
Exit 0 always (read-only diagnostic).

Usage:
    python scripts/audit_parser_processes_vps.py
    python scripts/audit_parser_processes_vps.py --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_MARKERS_FL = (
    "fl_fetch_worker",
    "chrome-headless",
    "headless_shell",
    "chromium",
    "ms-playwright/chromium",
    "playwright/chromium",
    "playwright/driver",
    "patchright",
)
_MARKERS_YOUDO = (
    "youdo_fetch_worker",
    "camoufox",
    "firefox",
    "geckodriver",
    "playwright/firefox",
)
_RADAR_MARKERS = ("main.py", "rawlead-radar", "rawlead_radar")


def _category(name: str, cmd: str) -> str:
    blob = f"{name} {cmd}".casefold()
    if any(m in blob for m in _MARKERS_YOUDO if m in ("youdo_fetch_worker", "camoufox", "geckodriver")):
        return "youdo_worker"
    if "firefox" in blob and "playwright" in blob:
        return "youdo_browser"
    if any(m in blob for m in ("fl_fetch_worker",)):
        return "fl_worker"
    if any(m in blob for m in ("chrome-headless", "headless_shell")):
        return "chromium_headless"
    if "chromium" in blob and ("playwright" in blob or "ms-playwright" in blob):
        return "chromium_playwright"
    if any(m in blob for m in _RADAR_MARKERS):
        return "radar"
    return ""


def _user() -> str:
    try:
        import getpass
        return getpass.getuser()
    except Exception:
        return ""


def audit() -> dict:
    try:
        import psutil
    except ImportError:
        return {"error": "psutil not installed — pip install psutil", "counts": {}}

    my_user = _user().casefold()
    my_pid = os.getpid()
    counts: dict[str, int] = {}
    details: list[dict] = []

    for proc in psutil.process_iter(["pid", "name", "username", "cmdline", "status"]):
        try:
            info = proc.info
            pid = int(info.get("pid") or 0)
            if pid <= 0 or pid == my_pid:
                continue
            owner = str(info.get("username") or "").casefold()
            if my_user and owner and owner != my_user:
                continue
            name = str(info.get("name") or "")
            cmdline = info.get("cmdline") or []
            cmd = " ".join(str(p) for p in cmdline)
            cat = _category(name, cmd)
            if not cat:
                continue
            counts[cat] = counts.get(cat, 0) + 1
            details.append({"pid": pid, "category": cat, "name": name})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return {
        "user": my_user or "unknown",
        "counts": counts,
        "details": details,
        "expected": {
            "fl_worker": "0 at rest, 1 during FL fetch cycle",
            "youdo_worker": "0 at rest, 1 during YouDo fetch cycle",
            "youdo_browser": "0 at rest (subprocess ephemeral)",
            "chromium_headless": "0 at rest",
            "chromium_playwright": "0 at rest",
            "radar": "1 (rawlead-radar)",
        },
        "orphan_risk": {
            cat: count
            for cat, count in counts.items()
            if cat not in ("radar",) and count > 0
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit parser processes (read-only)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    result = audit()

    if args.json or not sys.stdout.isatty():
        print(json.dumps(result, indent=2))
        return 0

    counts = result.get("counts", {})
    orphans = result.get("orphan_risk", {})
    print(f"=== Parser process audit (user={result.get('user', '?')}) ===")
    print(f"radar:              {counts.get('radar', 0)}")
    print(f"fl_worker:          {counts.get('fl_worker', 0)}  (expected 0 at rest)")
    print(f"youdo_worker:       {counts.get('youdo_worker', 0)}  (expected 0 at rest)")
    print(f"youdo_browser:      {counts.get('youdo_browser', 0)}  (expected 0 at rest)")
    print(f"chromium_headless:  {counts.get('chromium_headless', 0)}  (expected 0 at rest)")
    print(f"chromium_playwright:{counts.get('chromium_playwright', 0)}  (expected 0 at rest)")

    if orphans:
        print(f"\n⚠  Possible orphans: {orphans}")
        for d in result.get("details", []):
            if d["category"] in orphans:
                print(f"  pid={d['pid']} cat={d['category']} name={d['name']}")
    else:
        print("\n✓  No orphan processes detected")

    if result.get("error"):
        print(f"\nERROR: {result['error']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
