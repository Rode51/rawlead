"""O152: exchange trace jsonl + pipeline tail."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from exchange_trace import log_exchange_trace, recent_pipeline_lines, recent_traces


def test_log_exchange_trace_append(tmp_path: Path, monkeypatch) -> None:
    trace_file = tmp_path / "exchange_trace.jsonl"
    monkeypatch.setenv("EXCHANGE_TRACE_PATH", str(trace_file))
    line = log_exchange_trace(
        "youdo",
        stage="browser_goto",
        ms=12400,
        proxy="gate.node-proxy.com:10002",
        http=403,
        ban=3600,
        err="antibot",
    )
    assert "exchange:trace" in line
    assert "source=youdo" in line
    assert trace_file.is_file()
    rows = [json.loads(raw) for raw in trace_file.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["source"] == "youdo"
    assert rows[0]["http"] == 403
    got = recent_traces("youdo", limit=5, path=trace_file)
    assert len(got) == 1
    assert "403" in got[0]


def test_recent_pipeline_lines_tg(tmp_path: Path) -> None:
    log = tmp_path / "radar.log"
    log.write_text(
        "\n".join(
            [
                "2026-06-08 10:00:00 UTC fetch:fl proxy=direct",
                "2026-06-08 10:01:00 UTC pipeline:L1 tg:id=99 verdict=МИМО",
                "2026-06-08 10:02:00 UTC pipeline:skip filter tg:id=100",
                "2026-06-08 10:03:00 UTC pipeline:L1 fl:id=1 verdict=OK",
            ]
        ),
        encoding="utf-8",
    )
    lines = recent_pipeline_lines(log, source="tg", limit=3)
    assert len(lines) == 2
    assert all("tg" in line.lower() for line in lines)
