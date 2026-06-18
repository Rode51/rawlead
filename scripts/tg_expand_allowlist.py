"""O190 Option A: append done join-queue links to TG_PUBLIC_FEED_ALLOWLIST.txt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from public_feed import (  # noqa: E402
    _ALLOWLIST_PATH,
    collect_done_links_from_queues,
    expand_allowlist_from_done_queues,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand TG listen allowlist from done queue")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print how many links would be appended",
    )
    args = parser.parse_args()
    done = len(collect_done_links_from_queues())
    added = expand_allowlist_from_done_queues(dry_run=args.dry_run)
    mode = "would add" if args.dry_run else "added"
    print(f"{mode} {added} links (done in queue: {done}) -> {_ALLOWLIST_PATH}")
    if added == 0 and not args.dry_run:
        raise SystemExit(0)


if __name__ == "__main__":
    main()
