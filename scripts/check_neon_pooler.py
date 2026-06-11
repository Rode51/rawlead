"""O131: verify DATABASE_URL uses Neon connection pooler (required for load@50)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

try:
    from dotenv import load_dotenv

    load_dotenv(_ROOT / ".env")
    load_dotenv(_ROOT / ".env.site")
except ImportError:
    pass


def db_connection_mode(url: str) -> str:
    u = url.strip().lower()
    if not u:
        return "unset"
    if "pooler" in u or ":6543" in u:
        return "pooler"
    return "direct"


def to_pooler_url(url: str) -> str:
    """Neon direct → pooler (:6543 or *-pooler host). Idempotent."""
    u = (url or "").strip()
    if not u or db_connection_mode(u) == "pooler":
        return u
    out = u.replace(":5432/", ":6543/", 1).replace(":5432?", ":6543?", 1)
    if "pooler" not in out.casefold():
        import re

        out = re.sub(
            r"@(ep-[^./@]+)(\.)",
            r"@\1-pooler\2",
            out,
            count=1,
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Neon pooler in DATABASE_URL")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 when URL is not pooler (CI / pre-load gate)",
    )
    parser.add_argument(
        "--require-pooler",
        action="store_true",
        help="alias for --strict (O168 load gate)",
    )
    args = parser.parse_args()
    if args.require_pooler:
        args.strict = True
    url = os.getenv("DATABASE_URL", "").strip()
    mode = db_connection_mode(url)
    if mode == "pooler":
        print("OK: db=pooler")
        return 0
    if mode == "unset":
        print("WARN: DATABASE_URL not set", file=sys.stderr)
    else:
        print(
            "WARN: DATABASE_URL looks direct (no pooler host or port 6543) — "
            "use Neon Connection pooling before load@50",
            file=sys.stderr,
        )
    return 1 if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
