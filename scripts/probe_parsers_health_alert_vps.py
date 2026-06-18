#!/usr/bin/env python3
"""O258: Parser health probe with FLPARSING alert on sustained failure.

Runs every 15 min via cron on VPS. FL browser_error + httpx fallback ok in the
same cycle does not alert (O257 design).

Usage:
    python scripts/probe_parsers_health_alert_vps.py
    python scripts/probe_parsers_health_alert_vps.py --dry-run
    python scripts/probe_parsers_health_alert_vps.py --force-alert
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from parser_probe_alert import (  # noqa: E402
    evaluate_probe_alert,
    format_probe_alert_text,
    maybe_send_probe_alert,
)
from probe_parsers_health_vps import _DEFAULT_LOG, _DEFAULT_TAIL, _tail_lines  # noqa: E402


def run_probe_alert(
    log_path: Path,
    *,
    tail: int = _DEFAULT_TAIL,
    dry_run: bool = False,
    force_alert: bool = False,
) -> dict:
    if not log_path.exists():
        return {"status": "error", "error": f"log not found: {log_path}", "should_alert": False}

    lines = _tail_lines(log_path, tail)
    result = evaluate_probe_alert(lines)
    result["log"] = str(log_path)
    result["alert_sent"] = False
    result["alert_skip"] = ""

    if not result.get("should_alert"):
        return result

    if dry_run:
        result["alert_text"] = format_probe_alert_text(result)
        result["alert_skip"] = "dry_run"
        return result

    from config import load_config_for_profile
    from storage import storage_from_config

    cfg = load_config_for_profile("site", merge_root_env=True)
    storage = storage_from_config(cfg)
    sent, detail = maybe_send_probe_alert(storage, result, force=force_alert)
    result["alert_sent"] = sent
    result["alert_skip"] = detail if not sent else ""
    if sent or force_alert:
        result["alert_text"] = format_probe_alert_text(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe parsers + FLPARSING alert")
    parser.add_argument("--log", default=str(_DEFAULT_LOG), help="Path to radar_site.log")
    parser.add_argument("--last", type=int, default=_DEFAULT_TAIL, help="Lines to scan")
    parser.add_argument("--json", dest="json_out", action="store_true", help="JSON output")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate only, no TG send")
    parser.add_argument("--force-alert", action="store_true", help="Send even inside cooldown")
    args = parser.parse_args()

    result = run_probe_alert(
        Path(args.log),
        tail=args.last,
        dry_run=args.dry_run,
        force_alert=args.force_alert,
    )

    if args.json_out or not sys.stdout.isatty():
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        status = result.get("status", "error")
        sym = "✓" if status == "ok" else "✗"
        print(f"=== Parser probe alert — {sym} {status.upper()} ===")
        print(f"Log: {result.get('log', args.log)}")
        for src, info in (result.get("sources") or {}).items():
            eff = info.get("effective_outcome") or info.get("outcome")
            print(f"  {src}: effective={eff} raw={info.get('outcome')} reason={info.get('reason') or '—'}")
        if result.get("alert_sent"):
            print("  alert: sent ✓")
        elif result.get("should_alert"):
            print(f"  alert: skipped ({result.get('alert_skip') or 'no'})")
        if result.get("alert_text"):
            print("--- alert text ---")
            print(result["alert_text"])

    if result.get("status") == "error":
        return 1
    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
