#!/usr/bin/env python3
"""Restore hidden YouDo leads delisted by O281 detail-short gate.

Dry-run (report only):
  python scripts/restore_youdo_visible_vps.py

Restore to feed:
  python scripts/restore_youdo_visible_vps.py --apply

VPS:
  sudo -u rawlead env RADAR_PROFILE=site PYTHONPATH=/opt/rawlead/src \\
    /opt/rawlead/.venv/bin/python /opt/rawlead/scripts/restore_youdo_visible_vps.py --apply
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import apply_profile_argv, load_config, load_radar_env  # noqa: E402
from pg_storage import pg_storage_from_config  # noqa: E402
from vacancy_filter import is_physical_service_job  # noqa: E402

_FETCH_SQL = """
SELECT id, external_id, length(body) AS body_len, title, body, ai_verdict
FROM leads
WHERE source = 'youdo'
  AND is_visible = FALSE
  AND (delist_reason IS NULL OR delist_reason = 'youdo_detail_short')
  AND COALESCE(ai_verdict, '') <> 'МИМО'
ORDER BY id
LIMIT 1000
"""

_UPDATE_SQL = """
UPDATE leads
SET is_visible = TRUE, delist_reason = NULL
WHERE source = 'youdo'
  AND is_visible = FALSE
  AND (delist_reason IS NULL OR delist_reason = 'youdo_detail_short')
  AND COALESCE(ai_verdict, '') <> 'МИМО'
  AND id = ANY(%s::bigint[])
"""


def _eligible_for_restore(
    *,
    title: str | None,
    body: str | None,
    ai_verdict: str | None,
) -> bool:
    if (ai_verdict or "").strip() == "МИМО":
        return False
    return not is_physical_service_job(title or "", body or "")


def _fetch_hidden(pg) -> list[tuple]:
    with pg.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(_FETCH_SQL)
            return list(cur.fetchall() or [])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Restore YouDo leads hidden by O281 detail-short gate"
    )
    parser.add_argument("--profile", default="site", help="legacy|site")
    parser.add_argument("--apply", action="store_true", help="Set is_visible=true")
    args = parser.parse_args()

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

    rows = _fetch_hidden(pg)
    eligible = [
        row
        for row in rows
        if _eligible_for_restore(
            title=row[3],
            body=row[4],
            ai_verdict=row[5],
        )
    ]
    skipped_physical = len(rows) - len(eligible)
    mode = "dry-run" if not args.apply else "apply"
    print(
        f"[restore_youdo_visible] mode={mode} candidates={len(rows)} "
        f"eligible={len(eligible)} skipped_physical_or_mimo={skipped_physical}"
    )

    for lead_id, external_id, body_len, title, _body, verdict in eligible[:5]:
        title_short = (title or "")[:60]
        print(
            f"  id={lead_id} ext={external_id} body_len={body_len} "
            f"verdict={verdict!r} title={title_short!r}"
        )
    if len(eligible) > 5:
        print(f"  ... and {len(eligible) - 5} more")

    restored = 0
    if args.apply and eligible:
        restore_ids = [int(row[0]) for row in eligible]
        with pg.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(_UPDATE_SQL, (restore_ids,))
                restored = cur.rowcount or 0
            conn.commit()
        print(f"restored={restored}")

    remaining = _fetch_hidden(pg)
    print(f"remaining_hidden={len(remaining)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
