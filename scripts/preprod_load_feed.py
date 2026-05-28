"""§ PRE-PROD-STRESS t2 (альтернатива k6): нагрузка read-only API на Python.

  .venv\\Scripts\\python.exe scripts\\preprod_load_feed.py
  .venv\\Scripts\\python.exe scripts\\preprod_load_feed.py --api-url https://api.rawlead.ru --workers 50 --duration 300
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
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

ENDPOINTS = (
    "/health",
    "/v1/feed?limit=20",
    "/v1/skills/catalog",
)


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = int(round((pct / 100.0) * (len(ordered) - 1)))
    return ordered[max(0, min(idx, len(ordered) - 1))]


def _fetch(url: str, timeout: float) -> tuple[float, int | None, str | None]:
    t0 = time.perf_counter()
    try:
        req = Request(url, headers={"User-Agent": "RawLeadPreprodLoad/1.0"})
        with urlopen(req, timeout=timeout) as resp:
            resp.read(4096)
            ms = (time.perf_counter() - t0) * 1000.0
            return ms, resp.status, None
    except HTTPError as exc:
        ms = (time.perf_counter() - t0) * 1000.0
        return ms, exc.code, str(exc.reason)
    except URLError as exc:
        ms = (time.perf_counter() - t0) * 1000.0
        return ms, None, str(exc.reason)


def _worker(
    api_base: str,
    stop_at: float,
    timeout: float,
    feed_latencies: list[float],
    all_latencies: list[float],
    errors: list[str],
    lock: threading.Lock,
) -> None:
    while time.perf_counter() < stop_at:
        for path in ENDPOINTS:
            if time.perf_counter() >= stop_at:
                break
            url = f"{api_base}{path}"
            ms, status, err = _fetch(url, timeout)
            with lock:
                all_latencies.append(ms)
                if path.startswith("/v1/feed"):
                    feed_latencies.append(ms)
                if status != 200:
                    errors.append(f"{path} status={status} err={err}")
            time.sleep(0.05)


def main() -> int:
    parser = argparse.ArgumentParser(description="PRE-PROD API load (Python)")
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--workers", type=int, default=50)
    parser.add_argument("--duration", type=int, default=300, help="секунды")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument(
        "--output",
        type=Path,
        default=_ROOT / "data" / "preprod_load_summary.json",
    )
    args = parser.parse_args()

    api_base = args.api_url.rstrip("/")
    feed_latencies: list[float] = []
    all_latencies: list[float] = []
    errors: list[str] = []
    lock = threading.Lock()
    stop_at = time.perf_counter() + args.duration

    print(f"load: {args.workers} workers × {args.duration}s → {api_base}")
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(
                _worker,
                api_base,
                stop_at,
                args.timeout,
                feed_latencies,
                all_latencies,
                errors,
                lock,
            )
            for _ in range(args.workers)
        ]
        for fut in as_completed(futures):
            fut.result()

    total = len(all_latencies)
    err_rate = len(errors) / total if total else 1.0
    p50_feed = _percentile(feed_latencies, 50)
    p95_feed = _percentile(feed_latencies, 95)
    s3_pass = p95_feed is not None and p95_feed < 2000 and err_rate < 0.01

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_url": api_base,
        "workers": args.workers,
        "duration_sec": args.duration,
        "requests_total": total,
        "feed_requests": len(feed_latencies),
        "errors_count": len(errors),
        "error_rate": round(err_rate, 4),
        "p50_feed_ms": round(p50_feed, 1) if p50_feed is not None else None,
        "p95_feed_ms": round(p95_feed, 1) if p95_feed is not None else None,
        "p50_all_ms": round(_percentile(all_latencies, 50) or 0, 1),
        "p95_all_ms": round(_percentile(all_latencies, 95) or 0, 1),
        "s3_pass": s3_pass,
        "sample_errors": errors[:10],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if s3_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
