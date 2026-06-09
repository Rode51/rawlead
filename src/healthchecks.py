"""Healthchecks.io dead man's switch after ok site-cycle (O155)."""

from __future__ import annotations

import logging
import os
import threading
import time

logger = logging.getLogger(__name__)


def _enabled_web_sources() -> frozenset[str]:
    """Web-биржи из PUBLIC_FEED_SOURCES (как O104, без tg)."""
    from exchange_health import _O104_SOURCES
    from public_feed import public_feed_sources

    enabled = public_feed_sources()
    return frozenset(s for s in _O104_SOURCES if s != "tg" and s in enabled)


def _site_url() -> str:
    return os.getenv("HEALTHCHECKS_SITE_URL", "").strip()


def _fail_url() -> str:
    return os.getenv("HEALTHCHECKS_SITE_FAIL_URL", "").strip()


def _attempted_web(summary) -> list[tuple[str, object]]:
    web = _enabled_web_sources()
    return [(s, st) for s, st in summary.sources.items() if s in web]


def _any_web_ok(summary) -> bool:
    return any(not bool(st.fetch_error) for _, st in _attempted_web(summary))


def _all_web_fetch_failed(summary) -> bool:
    attempted = _attempted_web(summary)
    if not attempted:
        return False
    return all(bool(st.fetch_error) for _, st in attempted)


def _tg_monitor_alive(storage) -> bool:
    from config import radar_tg_enabled
    from health_check import (
        _TG_MONITOR_PULSE_KEY,
        _TG_MONITOR_PULSE_MAX_AGE_SEC,
        tg_monitor_warmup_remaining_sec,
    )

    if not radar_tg_enabled():
        return False
    raw = storage.get_setting(_TG_MONITOR_PULSE_KEY, "0").strip()
    try:
        last_pulse = float(raw)
    except ValueError:
        last_pulse = 0.0
    if last_pulse > 0 and (time.time() - last_pulse) <= _TG_MONITOR_PULSE_MAX_AGE_SEC:
        return True
    return tg_monitor_warmup_remaining_sec(storage) > 0


def _cycle_healthy(summary, storage) -> bool:
    """Ok-cycle = хотя бы одна web-биржа без fetch_error или живой tg_main."""
    if _any_web_ok(summary):
        return True
    if storage is not None and _tg_monitor_alive(storage):
        return True
    if not _attempted_web(summary):
        return True
    return False


def _fire_get(url: str) -> None:
    def _run() -> None:
        try:
            import requests

            requests.get(
                url,
                timeout=10,
                headers={"User-Agent": "RawLead-Radar/1.0 (healthchecks-ping)"},
            )
        except Exception as exc:
            logger.debug("healthchecks ping failed: %s", exc)

    threading.Thread(target=_run, daemon=True, name="healthchecks-ping").start()


def ping_after_site_cycle(summary, storage=None) -> None:
    """Fire-and-forget GET after site run_cycle; empty env = no-op."""
    if not _site_url():
        return
    if _cycle_healthy(summary, storage):
        _fire_get(_site_url())
        return
    fail = _fail_url()
    if fail:
        _fire_get(fail)


def ping_cycle_overrun() -> None:
    """Fail ping when site cycle exceeds RADAR_CYCLE_WALL_SEC (O160 L6b)."""
    fail = _fail_url()
    if fail:
        _fire_get(fail)
