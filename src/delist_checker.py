"""O65: batch re-check visible leads — delist if source page gone."""

from __future__ import annotations

import logging

from config import Config
from fl_parser import check_project_page_gone as fl_page_gone
from kwork_parser import check_project_page_gone as kwork_page_gone
from listing import SOURCE_FL, SOURCE_KWORK
from pg_storage import NeonLeadStorage

logger = logging.getLogger(__name__)

_DELIST_BATCH_LIMIT = 20
_DELIST_GRACE_HOURS = 6


def _check_gone(source: str, url: str, cfg: Config) -> bool | None:
    src = (source or "").strip().lower()
    if src == SOURCE_FL or src.startswith("fl:"):
        return fl_page_gone(url, cfg)
    if src == SOURCE_KWORK or src.startswith("kwork:"):
        return kwork_page_gone(url, cfg)
    return None


def run_delist_batch(
    cfg: Config,
    pg: NeonLeadStorage,
    *,
    limit: int = _DELIST_BATCH_LIMIT,
    errors: list[str] | None = None,
) -> dict[str, int]:
    """Re-check URLs; delist when gone. Returns checked/delisted counts."""
    err = errors if errors is not None else []
    stats = {"checked": 0, "delisted": 0, "skipped": 0}
    rows = pg.fetch_visible_for_source_recheck(
        limit=limit, grace_hours=_DELIST_GRACE_HOURS, errors=err
    )
    for lead_id, source, url in rows:
        stats["checked"] += 1
        gone = _check_gone(source, url, cfg)
        if gone is None:
            pg.mark_source_checked(lead_id, errors=err)
            stats["skipped"] += 1
            continue
        if gone:
            if pg.delist_lead(lead_id, reason="source_gone", errors=err):
                stats["delisted"] += 1
                logger.info("delist:lead=%d source=%s reason=source_gone", lead_id, source)
        else:
            pg.mark_source_checked(lead_id, errors=err)
    return stats
