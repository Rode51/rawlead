#!/usr/bin/env python3
"""O281: Audit visible YouDo leads with body shorter than full TZ threshold.

Dry-run (report only):
  python scripts/audit_youdo_short_visible_vps.py --dry-run

Hide from feed:
  python scripts/audit_youdo_short_visible_vps.py --apply

VPS:
  sudo -u rawlead env RADAR_PROFILE=site PYTHONPATH=/opt/rawlead/src \\
    /opt/rawlead/.venv/bin/python /opt/rawlead/scripts/audit_youdo_short_visible_vps.py --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import apply_profile_argv, load_config, load_radar_env  # noqa: E402
from lead_pipeline import _youdo_detail_min_chars  # noqa: E402
from pg_storage import pg_storage_from_config  # noqa: E402


def _fetch_short_visible(pg, min_chars: int) -> list[tuple]:
    with pg.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, external_id, length(body) AS body_len, title
                FROM leads
                WHERE source = 'youdo'
                  AND is_visible = TRUE
                  AND length(COALESCE(body, '')) < %s
                ORDER BY id
                """,
                (min_chars,),
            )
            return list(cur.fetchall() or [])


def main() -> int:
    parser = argparse.ArgumentParser(description="O281: audit visible short YouDo leads")
    parser.add_argument("--profile", default="site", help="legacy|site")
    parser.add_argument("--dry-run", action="store_true", help="Report only")
    parser.add_argument("--apply", action="store_true", help="Set is_visible=false")
    parser.add_argument(
        "--min-chars",
        type=int,
        default=0,
        help="Override YOUDO_DETAIL_MIN_CHARS (default from env)",
    )
    args = parser.parse_args()

    if args.apply and args.dry_run:
        print("Укажите только --dry-run или --apply", file=sys.stderr)
        return 2
    dry_run = not args.apply

    if args.profile:
        sys.argv = [sys.argv[0], "--profile", args.profile.strip()] + [
            a for a in sys.argv[1:] if a not in ("--profile", args.profile.strip())
        ]
    apply_profile_argv()
    load_radar_env()

    cfg = load_config()
    pg = pg_storage_from_config(cfg)
    if pg is None or not pg.enabled:
        print("DATABASE_URL не задан", file=sys.stderr)
        return 1

    min_chars = args.min_chars or _youdo_detail_min_chars()
    rows = _fetch_short_visible(pg, min_chars)
    mode = "dry-run" if dry_run else "apply"
    print(f"[audit_youdo_short_visible] mode={mode} min_chars={min_chars} count={len(rows)}")

    errors: list[str] = []
    hidden = 0
    for lead_id, external_id, body_len, title in rows:
        title_short = (title or "")[:60]
        print(f"  id={lead_id} ext={external_id} body_len={body_len} title={title_short!r}")
        if not dry_run:
            if pg.delist_lead(
                int(lead_id),
                reason="youdo_detail_short",
                errors=errors,
            ):
                hidden += 1

    if not dry_run:
        print(f"hidden={hidden}")
    if errors:
        for msg in errors:
            print(f"  warn: {msg}", file=sys.stderr)

    remaining = _fetch_short_visible(pg, min_chars)
    print(f"remaining_visible_short={len(remaining)}")
    return 0 if len(remaining) == 0 or dry_run else 1


if __name__ == "__main__":
    raise SystemExit(main())
