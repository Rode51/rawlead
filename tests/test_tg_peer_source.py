"""TG peer id: canonical source + PUBLIC_FEED_SOURCES match."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from listing import canonical_tg_peer, telegram_source  # noqa: E402
from public_feed import is_public_feed_source  # noqa: E402


def test_telegram_source_canonical_supergroup() -> None:
    assert canonical_tg_peer(-5177575757) == -1005177575757
    assert canonical_tg_peer(5177575757) == -1005177575757
    assert telegram_source(-5177575757) == "tg:-1005177575757"


def test_is_public_feed_source_tg_peer_alias(monkeypatch) -> None:
    monkeypatch.setenv(
        "PUBLIC_FEED_SOURCES",
        "fl,kwork,tg:-1005177575757",
    )
    from public_feed import public_feed_sources

    public_feed_sources.cache_clear()
    assert is_public_feed_source("tg:-5177575757")
    assert is_public_feed_source("tg:-1005177575757")
