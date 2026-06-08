"""Structured stage timing for on-demand draft (grep: draft:trace)."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DraftTimer:
    """Monotonic timer — call log_draft_stage() to bump stage boundary."""

    t0: float = field(default_factory=time.monotonic)
    last: float = field(default_factory=time.monotonic)

    def elapsed_ms(self) -> int:
        return int((time.monotonic() - self.t0) * 1000)

    def stage_ms(self) -> int:
        return int((time.monotonic() - self.last) * 1000)

    def bump(self) -> None:
        self.last = time.monotonic()


def _fmt_fields(fields: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in sorted(fields):
        val = fields[key]
        if val is None or val == "":
            continue
        if isinstance(val, bool):
            parts.append(f"{key}={'1' if val else '0'}")
        else:
            parts.append(f"{key}={val}")
    return " ".join(parts)


def log_draft_stage(
    log_prefix: str,
    *,
    stage: str,
    timer: DraftTimer,
    lead_id: int | None = None,
    **fields: Any,
) -> None:
    """One line: `{prefix}trace stage=X ms=M total_ms=T lead=N …`."""
    stage_ms = timer.stage_ms()
    total_ms = timer.elapsed_ms()
    timer.bump()
    prefix = log_prefix or ""
    if prefix and not prefix.endswith(":"):
        prefix = f"{prefix}:"
    extra = _fmt_fields(fields)
    lead_part = f" lead={lead_id}" if lead_id is not None else ""
    msg = f"{prefix}trace stage={stage} ms={stage_ms} total_ms={total_ms}{lead_part}"
    if extra:
        msg = f"{msg} {extra}"
    logger.info(msg)
