"""O75 prod verify: /v1/feed items within 7d; optional Neon stale visible count."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from public_feed import FEED_VISIBILITY_DAYS

_DEFAULT_API = "https://api.rawlead.ru/v1/feed"


def _parse_dt(raw: str) -> datetime:
    s = raw.strip()
    if s.endswith("Z"):
        s = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def check_api_feed(api_url: str, *, limit: int) -> tuple[bool, str]:
    url = f"{api_url}?limit={limit}"
    with urlopen(url, timeout=30) as resp:
        body = resp.read().decode("utf-8")
    data = json.loads(body)
    items = data.get("items") or []
    now = datetime.now(timezone.utc)
    over: list[tuple[int, float]] = []
    for it in items:
        ca = it.get("created_at") or it.get("published_at")
        if not ca:
            continue
        age_days = (now - _parse_dt(str(ca))).total_seconds() / 86400.0
        if age_days > FEED_VISIBILITY_DAYS + 0.05:
            over.append((int(it.get("id") or 0), round(age_days, 2)))
    ok = not over
    msg = (
        f"api items={len(items)} over_{FEED_VISIBILITY_DAYS}d={len(over)} "
        f"sample={over[:3]}"
    )
    return ok, msg


def check_neon_stale() -> tuple[bool | None, str]:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return None, "neon: skip (no DATABASE_URL)"
    import psycopg

    with psycopg.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)::int
                FROM leads
                WHERE is_visible = TRUE
                  AND created_at < NOW() - make_interval(days => %s)
                """,
                (FEED_VISIBILITY_DAYS,),
            )
            stale = int(cur.fetchone()[0])
            cur.execute(
                """
                SELECT COUNT(*)::int
                FROM leads
                WHERE is_visible = TRUE AND delist_reason IS NOT NULL
                """,
            )
            bad = int(cur.fetchone()[0])
    ok = stale == 0 and bad == 0
    return ok, f"neon visible_older_{FEED_VISIBILITY_DAYS}d={stale} visible_with_delist={bad}"


def main() -> int:
    parser = argparse.ArgumentParser(description="O75 feed prod verify")
    parser.add_argument("--api-url", default=_DEFAULT_API)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    api_ok, api_msg = check_api_feed(args.api_url, limit=args.limit)
    print(api_msg)
    neon_ok, neon_msg = check_neon_stale()
    print(neon_msg)

    if not api_ok:
        print("FAIL: API feed has items older than window")
        return 1
    if neon_ok is False:
        print("WARN: Neon still has visible leads older than window (batch after deploy)")
        return 1
    print("O75 VERIFY OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
