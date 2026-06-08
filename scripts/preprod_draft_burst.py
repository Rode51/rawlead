"""O129: controlled draft burst — cap OpenRouter spend (DRAFT_BURST_MAX=20).

  .venv\\Scripts\\python.exe scripts\\preprod_draft_burst.py --api-url https://api.rawlead.ru
"""

from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

for _stream in (sys.stdout, sys.stderr):
    enc = getattr(_stream, "encoding", None) or ""
    if enc.lower() != "utf-8":
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

DRAFT_BURST_MAX = 20
_DRAFT_TIMEOUT_SEC = 90.0
_POLL_INTERVAL_SEC = 0.8
_UA = "RawLeadDraftBurst/1.0"


@dataclass
class PhaseTimingsMs:
    feed: float = 0.0
    expand: float = 0.0
    tools: float = 0.0
    shared_l2: float | None = None
    l3: float | None = None
    draft_wait: float = 0.0
    total: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "feed_ms": round(self.feed, 1),
            "expand_ms": round(self.expand, 1),
            "tools_ms": round(self.tools, 1),
            "shared_l2_ms": None if self.shared_l2 is None else round(self.shared_l2, 1),
            "l3_ms": None if self.l3 is None else round(self.l3, 1),
            "draft_wait_ms": round(self.draft_wait, 1),
            "total_ms": round(self.total, 1),
        }


@dataclass
class DraftBurstRow:
    lead_id: int
    status: int | None
    draft_status: str
    error: str | None = None
    reply_len: int = 0
    tools_count: int = 0
    rate_limited: bool = False
    server_error: bool = False
    smell: str | None = None
    timings: PhaseTimingsMs = field(default_factory=PhaseTimingsMs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lead_id": self.lead_id,
            "http_status": self.status,
            "draft_status": self.draft_status,
            "error": self.error,
            "reply_len": self.reply_len,
            "tools_count": self.tools_count,
            "rate_limited": self.rate_limited,
            "server_error": self.server_error,
            "smell": self.smell,
            "timings": self.timings.to_dict(),
        }


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = int(round((pct / 100.0) * (len(ordered) - 1)))
    return ordered[max(0, min(idx, len(ordered) - 1))]


def _load_token() -> str:
    token = os.environ.get("RAWLEAD_PREPROD_ACCESS_TOKEN", "").strip()
    if token:
        return token
    for name in (".env.site", ".env", ".env.local"):
        path = _ROOT / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("RAWLEAD_PREPROD_ACCESS_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _http_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    timeout: float = 30.0,
    data: bytes | None = None,
) -> tuple[float, int | None, dict[str, Any] | None, str | None]:
    headers = {"User-Agent": _UA, "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    t0 = time.perf_counter()
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            ms = (time.perf_counter() - t0) * 1000.0
            try:
                body = json.loads(raw.decode("utf-8")) if raw else {}
            except json.JSONDecodeError:
                body = None
            return ms, resp.status, body if isinstance(body, dict) else None, None
    except HTTPError as exc:
        ms = (time.perf_counter() - t0) * 1000.0
        try:
            raw = exc.read()
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except (HTTPError, json.JSONDecodeError, OSError):
            body = None
        return ms, exc.code, body if isinstance(body, dict) else None, str(exc.reason)
    except URLError as exc:
        ms = (time.perf_counter() - t0) * 1000.0
        return ms, None, None, str(exc.reason)


def _lead_ids_from_feed_body(body: dict[str, Any] | None, limit: int) -> list[int]:
    items = (body or {}).get("items") or []
    ids: list[int] = []
    for it in items:
        lid = it.get("id")
        if lid is not None:
            ids.append(int(lid))
        if len(ids) >= limit:
            break
    return ids


def fetch_feed_lead_ids(api_url: str, *, token: str, limit: int) -> list[int]:
    """Auth personal feed may be empty (km=0); fall back to anon or ?skills= for draft ids."""
    lim = max(limit, 20)
    base = f"{api_url.rstrip('/')}/v1/feed?limit={lim}"

    _, status, body, err = _http_json("GET", base, token=token, timeout=20.0)
    if status != 200:
        raise RuntimeError(f"feed fetch failed status={status} err={err}")
    ids = _lead_ids_from_feed_body(body, limit)
    if ids:
        return ids

    _, anon_st, anon_body, anon_err = _http_json("GET", base, token=None, timeout=20.0)
    if anon_st == 200:
        ids = _lead_ids_from_feed_body(anon_body, limit)
        if ids:
            return ids

    for skill in ("design", "javascript", "seo", "wordpress"):
        skill_url = f"{base}&skills={skill}"
        _, skill_st, skill_body, _ = _http_json("GET", skill_url, token=token, timeout=20.0)
        if skill_st == 200:
            ids = _lead_ids_from_feed_body(skill_body, limit)
            if ids:
                return ids

    raise RuntimeError(
        "feed returned no lead ids: auth personal feed empty; "
        f"anon status={anon_st} err={anon_err}; skills fallbacks exhausted. "
        "Hint: premium acc needs user_tags km>0 or explicit ?skills= on feed."
    )


def _poll_draft(
    api_url: str,
    *,
    token: str,
    lead_id: int,
    deadline: float,
) -> tuple[str, dict[str, Any] | None, float, int | None, str | None]:
    url = f"{api_url.rstrip('/')}/v1/me/leads/{lead_id}/draft"
    wait_ms = 0.0
    last_status: int | None = None
    last_err: str | None = None
    last_body: dict[str, Any] | None = None
    while time.perf_counter() < deadline:
        ms, status, body, err = _http_json("GET", url, token=token, timeout=30.0)
        wait_ms += ms
        last_status, last_err, last_body = status, err, body
        if status == 429:
            return "rate_limit", body, wait_ms, status, err
        if status and status >= 500:
            return "server_error", body, wait_ms, status, err
        st = (body or {}).get("status", "")
        if st == "ready":
            return "ready", body, wait_ms, status, err
        if st == "failed":
            return "failed", body, wait_ms, status, err
        time.sleep(_POLL_INTERVAL_SEC)
    return "timeout", last_body, wait_ms, last_status, last_err


def run_one_draft(api_url: str, *, token: str, lead_id: int) -> DraftBurstRow:
    timings = PhaseTimingsMs()
    t_total = time.perf_counter()

    feed_url = f"{api_url.rstrip('/')}/v1/feed?limit=20"
    timings.feed, feed_st, _, _ = _http_json("GET", feed_url, token=token, timeout=20.0)
    if feed_st != 200:
        return DraftBurstRow(
            lead_id=lead_id,
            status=feed_st,
            draft_status="feed_fail",
            error=f"feed HTTP {feed_st}",
            server_error=bool(feed_st and feed_st >= 500),
            timings=timings,
        )

    expand_url = f"{api_url.rstrip('/')}/v1/leads/{lead_id}"
    timings.expand, expand_st, expand_body, expand_err = _http_json(
        "GET", expand_url, token=token, timeout=20.0
    )
    if expand_st != 200:
        timings.total = (time.perf_counter() - t_total) * 1000.0
        return DraftBurstRow(
            lead_id=lead_id,
            status=expand_st,
            draft_status="expand_fail",
            error=f"expand HTTP {expand_st} {expand_err}",
            server_error=bool(expand_st and expand_st >= 500),
            timings=timings,
        )

    tools_before = expand_body.get("tools_required") if expand_body else None
    if isinstance(tools_before, list) and tools_before:
        timings.tools = 0.0
    else:
        timings.tools = 0.0

    post_url = f"{api_url.rstrip('/')}/v1/me/leads/{lead_id}/draft"
    post_ms, post_st, post_body, post_err = _http_json(
        "POST", post_url, token=token, timeout=30.0, data=b"{}"
    )
    timings.draft_wait += post_ms

    if post_st == 429:
        timings.total = (time.perf_counter() - t_total) * 1000.0
        return DraftBurstRow(
            lead_id=lead_id,
            status=post_st,
            draft_status="rate_limit",
            error=post_err or "429",
            rate_limited=True,
            timings=timings,
        )
    if post_st and post_st >= 500:
        timings.total = (time.perf_counter() - t_total) * 1000.0
        return DraftBurstRow(
            lead_id=lead_id,
            status=post_st,
            draft_status="server_error",
            error=post_err or str(post_st),
            server_error=True,
            timings=timings,
        )

    st = (post_body or {}).get("status", "")
    if st == "ready":
        body = post_body
        poll_ms = 0.0
        draft_status = "ready"
    else:
        draft_status, body, poll_ms, poll_st, poll_err = _poll_draft(
            api_url,
            token=token,
            lead_id=lead_id,
            deadline=time.perf_counter() + _DRAFT_TIMEOUT_SEC,
        )
        timings.draft_wait += poll_ms
        if draft_status == "rate_limit":
            timings.total = (time.perf_counter() - t_total) * 1000.0
            return DraftBurstRow(
                lead_id=lead_id,
                status=poll_st,
                draft_status="rate_limit",
                error=poll_err or "429",
                rate_limited=True,
                timings=timings,
            )
        if draft_status == "server_error":
            timings.total = (time.perf_counter() - t_total) * 1000.0
            return DraftBurstRow(
                lead_id=lead_id,
                status=poll_st,
                draft_status="server_error",
                error=poll_err or str(poll_st),
                server_error=True,
                timings=timings,
            )

    timings.total = (time.perf_counter() - t_total) * 1000.0
    reply = ((body or {}).get("reply_draft") or "").strip()
    tools = (body or {}).get("tools_required") or []
    if not isinstance(tools, list):
        tools = []
    if not tools_before and tools:
        timings.tools = min(timings.draft_wait, timings.draft_wait * 0.35)

    smell: str | None = None
    if reply:
        try:
            from l3_human_style import reply_ai_smell_reason

            smell = reply_ai_smell_reason(reply)
        except Exception:
            smell = None

    return DraftBurstRow(
        lead_id=lead_id,
        status=post_st,
        draft_status=draft_status,
        error=(body or {}).get("error") if draft_status == "failed" else None,
        reply_len=len(reply),
        tools_count=len(tools),
        smell=smell,
        timings=timings,
    )


def run_draft_burst(
    *,
    api_url: str,
    token: str | None = None,
    max_leads: int = DRAFT_BURST_MAX,
    concurrency: int = 4,
) -> dict[str, Any]:
    """Run up to max_leads draft requests; return summary + rows."""
    tok = (token or "").strip() or _load_token()
    if not tok:
        return {
            "skipped": True,
            "reason": "RAWLEAD_PREPROD_ACCESS_TOKEN missing",
            "pass": False,
        }

    try:
        lead_ids = fetch_feed_lead_ids(api_url, token=tok, limit=max_leads)
    except RuntimeError as exc:
        return {
            "skipped": True,
            "reason": str(exc),
            "pass": False,
        }

    rows: list[DraftBurstRow] = []
    workers = max(1, min(concurrency, len(lead_ids), 8))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(run_one_draft, api_url, token=tok, lead_id=lid): lid
            for lid in lead_ids[:max_leads]
        }
        for fut in as_completed(futures):
            rows.append(fut.result())

    totals = [r.timings.total for r in rows if r.timings.total > 0]
    draft_waits = [r.timings.draft_wait for r in rows if r.timings.draft_wait > 0]
    server_errors = sum(1 for r in rows if r.server_error)
    rate_limits = sum(1 for r in rows if r.rate_limited)
    ready = sum(1 for r in rows if r.draft_status == "ready" and r.reply_len >= 20)
    p95_draft = percentile(totals, 95)
    err_rate = server_errors / len(rows) if rows else 1.0
    draft_pass = err_rate == 0 and (p95_draft is None or p95_draft < 90_000)

    timing_agg: dict[str, dict[str, float | None]] = {}
    for key, vals in (
        ("feed", [r.timings.feed for r in rows]),
        ("expand", [r.timings.expand for r in rows]),
        ("tools", [r.timings.tools for r in rows]),
        ("draft_wait", draft_waits),
        ("total", totals),
    ):
        timing_agg[key] = {
            "p50_ms": round(percentile(vals, 50) or 0, 1) if vals else None,
            "p95_ms": round(percentile(vals, 95) or 0, 1) if vals else None,
        }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_url": api_url.rstrip("/"),
        "max_leads": max_leads,
        "concurrency": workers,
        "attempted": len(rows),
        "ready": ready,
        "server_errors": server_errors,
        "rate_limits": rate_limits,
        "error_rate_5xx": round(err_rate, 4),
        "p95_draft_ms": round(p95_draft, 1) if p95_draft is not None else None,
        "timings_agg": timing_agg,
        "note_l2_l3": "shared_l2/l3 not split at API — see draft_wait_ms",
        "pass": draft_pass,
        "rows": [r.to_dict() for r in rows],
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="O129 controlled draft burst")
    parser.add_argument("--api-url", default="https://api.rawlead.ru")
    parser.add_argument("--max-leads", type=int, default=DRAFT_BURST_MAX)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument(
        "--output",
        type=Path,
        default=_ROOT / "data" / "preprod_draft_burst.json",
    )
    args = parser.parse_args()

    summary = run_draft_burst(
        api_url=args.api_url,
        max_leads=args.max_leads,
        concurrency=args.concurrency,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary.get("skipped"):
        return 2
    return 0 if summary.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
