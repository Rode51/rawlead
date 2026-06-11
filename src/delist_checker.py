"""O65/O122: batch re-check visible leads — delist if source page gone."""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from config import Config
from exchange_delist import check_source_page_gone
from pg_storage import NeonLeadStorage

if TYPE_CHECKING:
    from storage import ProjectStorage

logger = logging.getLogger(__name__)

DELIST_LAST_RUN_KEY = "delist_last_run_epoch"
DELIST_LAST_STATS_KEY = "delist_last_stats_json"

_DEFAULT_BATCH_LIMIT = 80
_DEFAULT_INTERVAL_SEC = 900
_DEFAULT_GRACE_HOURS = 6


def delist_batch_limit() -> int:
    raw = os.environ.get("DELIST_BATCH_LIMIT", str(_DEFAULT_BATCH_LIMIT)).strip()
    try:
        return max(1, min(200, int(raw)))
    except ValueError:
        return _DEFAULT_BATCH_LIMIT


def delist_interval_sec() -> int:
    raw = os.environ.get("DELIST_INTERVAL_SEC", str(_DEFAULT_INTERVAL_SEC)).strip()
    try:
        return max(300, min(86400, int(raw)))
    except ValueError:
        return _DEFAULT_INTERVAL_SEC


def delist_grace_hours() -> int:
    raw = os.environ.get("DELIST_GRACE_HOURS", str(_DEFAULT_GRACE_HOURS)).strip()
    try:
        return max(1, min(72, int(raw)))
    except ValueError:
        return _DEFAULT_GRACE_HOURS


def load_delist_last_stats(storage: ProjectStorage) -> dict[str, Any]:
    raw = storage.get_setting(DELIST_LAST_STATS_KEY, "").strip()
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                epoch = float(data.get("epoch") or 0)
                return {
                    "last_run_at": _format_epoch(epoch) if epoch else None,
                    "checked": int(data.get("checked") or 0),
                    "delisted": int(data.get("delisted") or 0),
                    "skipped": int(data.get("skipped") or 0),
                }
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    epoch_raw = storage.get_setting(DELIST_LAST_RUN_KEY, "0").strip()
    try:
        epoch = float(epoch_raw)
    except ValueError:
        epoch = 0.0
    return {
        "last_run_at": _format_epoch(epoch) if epoch else None,
        "checked": 0,
        "delisted": 0,
        "skipped": 0,
    }


def save_delist_run(
    storage: ProjectStorage,
    stats: dict[str, int],
    *,
    epoch: float | None = None,
) -> None:
    now = epoch if epoch is not None else time.time()
    storage.set_setting(DELIST_LAST_RUN_KEY, str(now))
    payload = {
        "epoch": now,
        "checked": int(stats.get("checked") or 0),
        "delisted": int(stats.get("delisted") or 0),
        "skipped": int(stats.get("skipped") or 0),
    }
    storage.set_setting(DELIST_LAST_STATS_KEY, json.dumps(payload, separators=(",", ":")))


def _format_epoch(epoch: float) -> str:
    return (
        datetime.fromtimestamp(epoch, tz=timezone.utc)
        .strftime("%d.%m.%Y %H:%M UTC")
    )


def run_delist_batch(
    cfg: Config,
    pg: NeonLeadStorage,
    *,
    limit: int | None = None,
    errors: list[str] | None = None,
) -> dict[str, int]:
    """Re-check URLs; delist when gone. Returns checked/delisted counts."""
    err = errors if errors is not None else []
    batch_limit = delist_batch_limit() if limit is None else max(1, int(limit))
    stats = {"checked": 0, "delisted": 0, "skipped": 0}
    rows = pg.fetch_visible_for_source_recheck(
        limit=batch_limit, grace_hours=delist_grace_hours(), errors=err
    )
    for lead_id, source, url in rows:
        stats["checked"] += 1
        gone = check_source_page_gone(source, url, cfg)
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


def maybe_run_delist_batch(
    cfg: Config,
    pg: NeonLeadStorage | None,
    storage: ProjectStorage,
    errors: list[str],
) -> dict[str, int] | None:
    """Scheduled delist pass from radar main loop (O65/O122). None = skipped by interval."""
    if cfg.radar_profile != "site" or pg is None or not pg.enabled:
        return None
    now = time.time()
    raw = storage.get_setting(DELIST_LAST_RUN_KEY, "0").strip()
    try:
        last = float(raw)
    except ValueError:
        last = 0.0
    if now - last < delist_interval_sec():
        return None
    stats = run_delist_batch(cfg, pg, errors=errors)
    save_delist_run(storage, stats, epoch=now)
    return stats
