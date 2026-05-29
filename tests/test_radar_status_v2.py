"""BOT-STATUS-V2 (O32): smoke для format_status_message."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from radar_cycle_log import SourceCycleStats, parse_site_rollup_metrics
from radar_status import (
    _bot_label,
    _format_cycle_block_v2,
    _format_exchange_line,
    _human_ago,
    _ru_new,
)
from radar_cycle_log import CycleSummary


class _Cfg:
    radar_profile: str = "site"


def test_bot_label_by_profile() -> None:
    cfg = _Cfg()
    assert _bot_label(cfg) == "@rawlead_bot"  # type: ignore[arg-type]
    cfg.radar_profile = "legacy"
    assert _bot_label(cfg) == "@FLPARSINGBOT"  # type: ignore[arg-type]


def test_ru_new_plural() -> None:
    assert _ru_new(1) == "1 новый"
    assert _ru_new(5) == "5 новых"


def test_exchange_line_fetch_ok() -> None:
    st = SourceCycleStats("fl", downloaded=90, new_ids=0)
    line = _format_exchange_line(st, neon_insert=0)
    assert "FL.ru" in line
    assert "fetch OK" in line


def test_parse_site_rollup_metrics() -> None:
    line = "site:сводка │ 10мин │ l1 8 │ l2 0 │ is_visible 3"
    assert parse_site_rollup_metrics(line) == (8, 0, 3)


def test_human_ago_utc() -> None:
    import time

    ts = "2020-01-01 00:00:00 UTC"
    ago = _human_ago(ts, now=time.mktime((2020, 1, 1, 0, 5, 0, 0, 0, 0)))
    assert ago is not None
    assert "мин" in ago or "сек" in ago


def test_cycle_block_v2() -> None:
    summary = CycleSummary(ts="2026-05-29 12:00:00", cycle_sec=234.0, neon_dup_skip=102)
    rollup = "site:сводка │ 10мин │ l1 8 │ l2 0 │ is_visible 3"
    lines = _format_cycle_block_v2(summary, rollup)
    text = "\n".join(lines)
    assert "── Цикл ──" in text
    assert "234 с" in text
    assert "neon_dup_skip=102" in text
    assert "visible=3" in text
