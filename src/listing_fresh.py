"""O134/O139: fresh-only listing — keep unseen ids, skip known (incl. pinned)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from listing import ListingProject

if TYPE_CHECKING:
    from storage import ProjectStorage

logger = logging.getLogger(__name__)


def trim_listing_at_known(
    projects: list[ListingProject],
    storage: ProjectStorage | None,
    source: str,
) -> list[ListingProject]:
    """Filter to project ids not yet in SQLite (skip known pins/gaps, no prefix-stop)."""
    if not projects or storage is None:
        return projects
    out: list[ListingProject] = []
    skipped = 0
    for project in projects:
        if storage.has_seen(source, project.project_id):
            skipped += 1
            continue
        out.append(project)
    if skipped:
        logger.info(
            "%s: skipped_known=%d kept=%d",
            source,
            skipped,
            len(out),
        )
    return out
