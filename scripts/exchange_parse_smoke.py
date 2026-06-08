#!/usr/bin/env python3
"""Live parse smoke: FL.ru / Kwork / Freelance.ru — cards on listing page (no ingest).

Exit 0 = all enabled sources parsed >=1 card. Exit 1 = at least one hard fail.

Usage:
  python scripts/exchange_parse_smoke.py
  python scripts/exchange_parse_smoke.py --source fl
  python scripts/exchange_parse_smoke.py --write-health  # fail → O104 red in SQLite

Cron (optional, every 15m on VPS):
  */15 * * * * cd /opt/rawlead && .venv/bin/python scripts/exchange_parse_smoke.py --write-health
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from config import load_config, load_radar_env  # noqa: E402

_SMOKE_SOURCES: dict[str, tuple[str, str]] = {
    "fl": ("fl_parser", "fetch_listing_projects"),
    "kwork": ("kwork_parser", "fetch_listing_projects"),
    "freelance_ru": ("freelance_ru_parser", "fetch_listing_projects"),
}


def _fetch_raw(cfg, mod_name: str, fn_name: str) -> int:
    import importlib
    import inspect

    mod = importlib.import_module(mod_name)
    fn = getattr(mod, fn_name)
    kwargs: dict[str, object] = {}
    if "storage" in inspect.signature(fn).parameters:
        kwargs["storage"] = None
    projects = fn(cfg, **kwargs)
    return len(projects or [])


def main() -> int:
    parser = argparse.ArgumentParser(description="Exchange listing parse smoke")
    parser.add_argument(
        "--source",
        action="append",
        choices=sorted(_SMOKE_SOURCES),
        help="Only these sources (default: all three)",
    )
    parser.add_argument(
        "--write-health",
        action="store_true",
        help="On fail, record_fetch(ok=False) into exchange_health SQLite",
    )
    args = parser.parse_args()
    load_radar_env()
    cfg = load_config()
    targets = args.source or list(_SMOKE_SOURCES)
    failed = 0
    storage = None
    if args.write_health:
        from exchange_health import record_fetch
        from storage import ProjectStorage

        storage = ProjectStorage(cfg.sqlite_path)
    print("=== exchange parse smoke ===")
    for sid in targets:
        mod_name, fn_name = _SMOKE_SOURCES[sid]
        label = {"fl": "FL.ru", "kwork": "Kwork", "freelance_ru": "Freelance.ru"}.get(
            sid, sid
        )
        try:
            n = _fetch_raw(cfg, mod_name, fn_name)
            if n >= 1:
                print(f"OK  {label}: parsed={n} cards")
            else:
                print(f"FAIL {label}: parsed=0 cards (empty or blocked)")
                if storage is not None:
                    record_fetch(
                        storage,
                        sid,
                        ok=False,
                        error_msg="parse smoke: parsed=0",
                        parsed_cards=0,
                    )
                failed += 1
        except Exception as exc:
            print(f"FAIL {label}: {type(exc).__name__}: {exc}")
            if storage is not None:
                record_fetch(
                    storage,
                    sid,
                    ok=False,
                    error_msg=str(exc)[:80],
                )
            failed += 1
    print("=== done ===")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
