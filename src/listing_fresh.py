"""O134: fresh-only listing — stop at first known project_id."""

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
    """Keep newest-first prefix until (excluding) first id already in SQLite."""
    if not projects or storage is None:
        return projects
    out: list[ListingProject] = []
    for project in projects:
        if storage.has_seen(source, project.project_id):
            break
        out.append(project)
    skipped = len(projects) - len(out)
    if skipped:
        logger.info(
            "%s: fresh-only stop at known id kept=%d skipped=%d",
            source,
            len(out),
            skipped,
        )
    return out
