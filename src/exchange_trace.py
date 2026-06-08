"""Structured trace for exchange fetch cycles (grep: exchange:trace)."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from config import radar_timestamp

logger = logging.getLogger(__name__)

_ROTATE_DAYS = 7
_TRACE_BASENAME = "exchange_trace.jsonl"


def trace_path() -> Path:
    raw = os.getenv("EXCHANGE_TRACE_PATH", "").strip()
    if raw:
        return Path(raw)
    return Path(__file__).resolve().parent.parent / "data" / _TRACE_BASENAME


def _fmt_fields(fields: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in sorted(fields):
        val = fields[key]
        if val is None or val == "":
            continue
        if isinstance(val, bool):
            parts.append(f"{key}={'1' if val else '0'}")
        else:
            s = str(val).replace("\n", " ").strip()
            if s:
                parts.append(f"{key}={s}")
    return " ".join(parts)


def _rotate_jsonl(path: Path) -> None:
    if not path.is_file():
        return
    cutoff = time.time() - _ROTATE_DAYS * 86400
    kept: list[str] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = str(row.get("ts") or "")
            epoch = None
            for fmt in ("%Y-%m-%d %H:%M:%S",):
                try:
                    from datetime import datetime

                    epoch = datetime.strptime(ts.replace(" UTC", ""), fmt).timestamp()
                    break
                except ValueError:
                    continue
            if epoch is None or epoch >= cutoff:
                kept.append(line)
    except OSError:
        return
    if len(kept) < 20 and path.stat().st_size < 2_000_000:
        return
    try:
        tmp = path.with_suffix(".tmp")
        tmp.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass


def log_exchange_trace(
    source: str,
    *,
    stage: str,
    ms: int | None = None,
    **fields: Any,
) -> str:
    """One journal line + append JSONL. Returns the line text."""
    src = (source or "").strip().lower() or "?"
    extra = _fmt_fields(fields)
    parts = [f"exchange:trace source={src} stage={stage}"]
    if ms is not None:
        parts.append(f"ms={int(ms)}")
    if extra:
        parts.append(extra)
    line = " ".join(parts)
    logger.info(line)
    record = {
        "ts": radar_timestamp(),
        "source": src,
        "stage": stage,
        "line": line,
    }
    if ms is not None:
        record["ms"] = int(ms)
    for key, val in fields.items():
        if val is not None and val != "":
            record[key] = val
    path = trace_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        _rotate_jsonl(path)
    except OSError:
        pass
    return line


def recent_traces(
    source: str | None = None,
    *,
    limit: int = 10,
    path: Path | None = None,
) -> list[str]:
    """Last N trace lines from jsonl, newest first."""
    p = path or trace_path()
    if not p.is_file():
        return []
    src = (source or "").strip().lower()
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out: list[str] = []
    for raw in reversed(lines):
        raw = raw.strip()
        if not raw:
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if src and str(row.get("source") or "").lower() != src:
            continue
        text = str(row.get("line") or "").strip()
        if not text:
            continue
        out.append(text)
        if len(out) >= limit:
            break
    return out


def _pipeline_line_matches(raw: str, source: str) -> bool:
    if "pipeline:" not in raw:
        return False
    src = (source or "").strip().lower()
    if not src:
        return True
    low = raw.lower()
    return (
        f"pipeline:l1 {src}:" in low
        or f"{src}:id=" in low
        or f" {src}:" in low
        or (src == "tg" and "tg" in low)
    )


def recent_pipeline_lines(
    log_path: Path | None,
    *,
    source: str = "tg",
    limit: int = 3,
) -> list[str]:
    """Tail radar log for pipeline:* lines (TG card on /ops/)."""
    if log_path is None or not log_path.is_file():
        return []
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    rows = text.splitlines()
    out: list[str] = []
    for raw in reversed(rows[-4000:]):
        if not _pipeline_line_matches(raw, source):
            continue
        line = raw.strip()
        if len(line) > 220:
            line = line[:217] + "..."
        out.append(line)
        if len(out) >= limit:
            break
    return out
