"""O75: hide visible leads older than feed window (not DB purge)."""

from __future__ import annotations

import logging

from public_feed import FEED_VISIBILITY_DAYS
from pg_storage import NeonLeadStorage

logger = logging.getLogger(__name__)

_RETENTION_BATCH_LIMIT = 200


def run_feed_retention_batch(
    pg: NeonLeadStorage,
    *,
    days: int = FEED_VISIBILITY_DAYS,
    limit: int = _RETENTION_BATCH_LIMIT,
    errors: list[str] | None = None,
) -> dict[str, int]:
    """Set is_visible=false for stale feed rows. Returns hidden count."""
    hidden = pg.hide_feed_older_than(days=days, limit=limit, errors=errors)
    if hidden:
        logger.info("feed_retention:hidden=%d days=%d", hidden, days)
    return {"hidden": hidden}
