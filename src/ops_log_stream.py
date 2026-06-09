"""O161: SSE tail stream for radar_site.log."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Iterator


def resolve_radar_log_path() -> Path | None:
    raw = os.environ.get("RADAR_LOG_PATH", "").strip()
    if raw:
        p = Path(raw)
        if not p.is_absolute():
            root = Path(__file__).resolve().parent.parent
            p = root / p
        return p if p.is_file() else None
    root = Path(__file__).resolve().parent.parent
    for candidate in ("data/radar_site.log", "data/radar.log"):
        p = root / candidate
        if p.is_file():
            return p
    return None


def _tail_lines(path: Path, *, count: int = 100) -> list[str]:
    try:
        with path.open("rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            if size <= 0:
                return []
            chunk = min(size, 65536)
            fh.seek(max(0, size - chunk))
            raw = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return []
    lines = raw.splitlines()
    if len(lines) > count:
        lines = lines[-count:]
    return lines


def iter_radar_log_sse(
    log_path: Path | None = None,
    *,
    tail_lines: int = 100,
    timeout_sec: int = 300,
    poll_sec: float = 0.5,
) -> Iterator[str]:
    """Yield SSE `data:` lines from radar log tail + follow."""
    path = log_path or resolve_radar_log_path()
    if path is None:
        yield "data: [ops] log file not found\n\n"
        return

    for line in _tail_lines(path, count=tail_lines):
        yield f"data: {line.rstrip()}\n\n"

    deadline = time.monotonic() + timeout_sec
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            fh.seek(0, 2)
            while time.monotonic() < deadline:
                line = fh.readline()
                if line:
                    yield f"data: {line.rstrip()}\n\n"
                else:
                    time.sleep(poll_sec)
    except OSError as exc:
        yield f"data: [ops] log read error: {type(exc).__name__}\n\n"
