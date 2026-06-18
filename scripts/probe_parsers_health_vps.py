#!/usr/bin/env python3
"""O257: Smoke-check parsers health by reading last N cycles from radar_site.log.

Reads the last 500 lines of the log. For each source (fl / kwork / youdo), checks:
  - found at least one `fetch:{src} outcome=ok` in recent lines → green
  - found `fetch:{src} outcome=fail` with no subsequent ok → red
  - no `fetch:{src}` line at all → unknown

Exits 0 if all sources are green or unknown; exits 1 if any source is red.

Usage:
    python scripts/probe_parsers_health_vps.py
    python scripts/probe_parsers_health_vps.py --log /opt/rawlead/data/radar_site.log
    python scripts/probe_parsers_health_vps.py --json
    python scripts/probe_parsers_health_vps.py --last 3
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_SOURCES = ("fl", "kwork", "youdo")
_DEFAULT_LOG = Path(__file__).resolve().parents[1] / "data" / "radar_site.log"
_DEFAULT_TAIL = 500
_OUTCOME_RE = re.compile(
    r"fetch:(?P<src>fl|kwork|youdo)\s+outcome=(?P<outcome>ok|fail)"
    r"(?:.*?\breason=(?P<reason>\S+))?"
    r"(?:.*?\bparsed=(?P<parsed>\d+))?"
)


def _tail_lines(path: Path, n: int) -> list[str]:
    """Read last n lines from a file efficiently."""
    try:
        with path.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            chunk = min(size, n * 200)
            f.seek(max(0, size - chunk))
            raw = f.read().decode("utf-8", errors="replace")
    except OSError as exc:
        return [f"# ERROR: {exc}"]
    lines = raw.splitlines()
    return lines[-n:] if len(lines) > n else lines


def _parse_outcomes(lines: list[str]) -> dict[str, dict]:
    """Return last outcome per source from log lines."""
    results: dict[str, dict] = {src: {"outcome": "unknown", "reason": "", "parsed": -1, "line": ""} for src in _SOURCES}
    for line in lines:
        m = _OUTCOME_RE.search(line)
        if not m:
            continue
        src = m.group("src")
        if src not in results:
            continue
        results[src] = {
            "outcome": m.group("outcome"),
            "reason": m.group("reason") or "",
            "parsed": int(m.group("parsed")) if m.group("parsed") else -1,
            "line": line.strip(),
        }
    return results


def probe(log_path: Path, tail: int = _DEFAULT_TAIL) -> dict:
    lines = _tail_lines(log_path, tail)
    outcomes = _parse_outcomes(lines)
    any_red = any(r["outcome"] == "fail" for r in outcomes.values())
    status = "fail" if any_red else "ok"
    return {
        "status": status,
        "log": str(log_path),
        "lines_scanned": len(lines),
        "sources": outcomes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe parser health from log (read-only)")
    parser.add_argument("--log", default=str(_DEFAULT_LOG), help="Path to radar_site.log")
    parser.add_argument("--last", type=int, default=_DEFAULT_TAIL, help="Lines to scan (default 500)")
    parser.add_argument("--json", dest="json_out", action="store_true", help="JSON output")
    args = parser.parse_args()

    log_path = Path(args.log)
    if not log_path.exists():
        msg = {"status": "error", "error": f"log not found: {log_path}"}
        if args.json_out:
            print(json.dumps(msg))
        else:
            print(f"ERROR: log not found: {log_path}", file=sys.stderr)
        return 1

    result = probe(log_path, args.last)

    if args.json_out or not sys.stdout.isatty():
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "ok" else 1

    status_sym = "✓" if result["status"] == "ok" else "✗"
    print(f"=== Parser health probe — {status_sym} {result['status'].upper()} ===")
    print(f"Log: {result['log']} (last {result['lines_scanned']} lines)")
    for src, info in result["sources"].items():
        sym = {"ok": "✓", "fail": "✗", "unknown": "?"}.get(info["outcome"], "?")
        detail = ""
        if info["reason"]:
            detail = f" reason={info['reason']}"
        if info["parsed"] >= 0:
            detail += f" parsed={info['parsed']}"
        print(f"  {sym} {src:8s} outcome={info['outcome']}{detail}")
        if info["line"]:
            print(f"           {info['line'][:100]}")

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
