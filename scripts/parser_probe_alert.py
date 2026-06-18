"""O258: Parser probe alert logic — FL httpx fallback ok, cooldown, FLPARSING message."""
from __future__ import annotations

import os
import re
import time
from typing import Any

_SOURCES = ("fl", "kwork", "youdo")
_ALERT_KEY = "parser_probe_last_alert_at"
_DEFAULT_COOLDOWN_SEC = 1800

_OUTCOME_RE = re.compile(
    r"fetch:(?P<src>fl|kwork|youdo)\s+outcome=(?P<outcome>ok|fail)"
    r"(?:.*?\breason=(?P<reason>\S+))?"
    r"(?:.*?\bparsed=(?P<parsed>\d+))?"
)
_FL_HTTPX_OK_RE = re.compile(r"fetch:fl\s+stage=fallback\s+httpx\s+outcome=ok")


def parser_probe_alert_cooldown_sec() -> int:
    raw = os.environ.get("PARSER_PROBE_ALERT_COOLDOWN_SEC", "").strip()
    if not raw:
        return _DEFAULT_COOLDOWN_SEC
    try:
        return max(0, int(raw))
    except ValueError:
        return _DEFAULT_COOLDOWN_SEC


def _blank_source() -> dict[str, Any]:
    return {"outcome": "unknown", "reason": "", "parsed": -1, "line": "", "effective_outcome": "unknown"}


def _parse_last_outcomes(lines: list[str]) -> dict[str, dict[str, Any]]:
    results = {src: _blank_source() for src in _SOURCES}
    for line in lines:
        m = _OUTCOME_RE.search(line)
        if not m:
            continue
        src = m.group("src")
        if src not in results:
            continue
        results[src] = {
            "outcome": m.group("outcome"),
            "reason": m.group("reason") or "",
            "parsed": int(m.group("parsed")) if m.group("parsed") else -1,
            "line": line.strip(),
            "effective_outcome": m.group("outcome"),
        }
    return results


def _fl_rescued_by_httpx_fallback(lines: list[str], fail_idx: int) -> bool:
    for line in lines[fail_idx + 1 :]:
        if _FL_HTTPX_OK_RE.search(line):
            return True
        m = _OUTCOME_RE.search(line)
        if m and m.group("src") == "fl":
            break
    return False


def _apply_fl_httpx_fallback(lines: list[str], fl_info: dict[str, Any]) -> dict[str, Any]:
    if fl_info["outcome"] != "fail":
        return fl_info
    if fl_info["reason"] != "browser_error":
        return fl_info
    try:
        fail_idx = lines.index(fl_info["line"])
    except ValueError:
        fail_idx = -1
    if fail_idx >= 0 and _fl_rescued_by_httpx_fallback(lines, fail_idx):
        patched = dict(fl_info)
        patched["effective_outcome"] = "ok"
        patched["reason"] = "browser_error+httpx_ok"
        return patched
    return fl_info


def evaluate_probe_alert(lines: list[str]) -> dict[str, Any]:
    """Return probe status plus per-source effective outcomes for alerting."""
    sources = _parse_last_outcomes(lines)
    sources["fl"] = _apply_fl_httpx_fallback(lines, sources["fl"])
    for src in _SOURCES:
        sources[src]["effective_outcome"] = sources[src].get("effective_outcome") or sources[src]["outcome"]

    failing = [
        src
        for src in _SOURCES
        if sources[src]["effective_outcome"] == "fail"
    ]
    status = "fail" if failing else "ok"
    return {
        "status": status,
        "should_alert": status == "fail",
        "failing_sources": failing,
        "sources": sources,
        "lines_scanned": len(lines),
    }


def format_probe_alert_text(result: dict[str, Any]) -> str:
    lines = ["FLPARSING · парсеры", f"status={result['status']}"]
    for src in _SOURCES:
        info = result["sources"][src]
        eff = info.get("effective_outcome") or info.get("outcome") or "unknown"
        raw = info.get("outcome") or "unknown"
        reason = info.get("reason") or "—"
        parsed = info.get("parsed", -1)
        parsed_part = f" parsed={parsed}" if parsed >= 0 else ""
        detail = f"{src}: outcome={eff}"
        if raw != eff:
            detail += f" (raw={raw})"
        detail += f" reason={reason}{parsed_part}"
        lines.append(detail)
        snippet = (info.get("line") or "").strip()
        if snippet:
            lines.append(f"  {snippet[:240]}")
    return "\n".join(lines)


def alert_cooldown_ok(storage, cooldown_sec: int | None = None) -> bool:
    cooldown = parser_probe_alert_cooldown_sec() if cooldown_sec is None else cooldown_sec
    raw = storage.get_setting(_ALERT_KEY, "0").strip()
    try:
        last = float(raw)
    except ValueError:
        last = 0.0
    return (time.time() - last) >= cooldown


def mark_alert_sent(storage) -> None:
    storage.set_setting(_ALERT_KEY, str(int(time.time())))


def maybe_send_probe_alert(
    storage,
    result: dict[str, Any],
    *,
    cooldown_sec: int | None = None,
    force: bool = False,
) -> tuple[bool, str]:
    """Send FLPARSING alert when probe fails; respect cooldown unless force."""
    if not result.get("should_alert"):
        return False, "probe_ok"
    if not force and not alert_cooldown_ok(storage, cooldown_sec):
        return False, "cooldown"
    try:
        from health_check import send_flparsing_admin_text
    except ImportError as exc:
        return False, f"import:{exc}"

    text = format_probe_alert_text(result)
    ok, err = send_flparsing_admin_text(text)
    if ok:
        mark_alert_sent(storage)
        return True, err or "sent"
    return False, err or "send_fail"
