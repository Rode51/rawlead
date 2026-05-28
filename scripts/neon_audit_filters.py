"""§ NEON-AUDIT-FILTERS: выборка отказов L1 и сверка с pre-L1 filter skip.

  .venv\\Scripts\\python.exe scripts\\neon_audit_filters.py --profile site
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    enc = getattr(_stream, "encoding", None) or ""
    if enc.lower() != "utf-8":
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import apply_profile_argv, load_config, load_radar_env
from pg_storage import pg_storage_from_config
from public_feed import public_feed_sources

_SKIP_FILTER_RE = re.compile(r"skip:filter", re.IGNORECASE)
_L1_VERDICT_RE = re.compile(r"L1\s+\w+:\w+.*→", re.IGNORECASE)


def _sample_leads(pg, *, verdict: str, days: int, limit: int) -> list[dict]:
    sources = sorted(public_feed_sources())
    if not sources:
        return []
    rows: list[dict] = []
    with pg.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT title, ai_score, ai_reasons, source, is_visible
                FROM leads
                WHERE ai_verdict = %s
                  AND source = ANY(%s)
                  AND created_at >= NOW() - make_interval(days => %s)
                ORDER BY RANDOM()
                LIMIT %s
                """,
                (verdict, sources, int(days), int(limit)),
            )
            for title, score, reasons, source, visible in cur.fetchall():
                if isinstance(reasons, str):
                    try:
                        reasons = json.loads(reasons)
                    except json.JSONDecodeError:
                        reasons = [reasons]
                rows.append(
                    {
                        "title": str(title or "")[:120],
                        "score": score,
                        "reasons": list(reasons or [])[:3],
                        "source": source,
                        "is_visible": bool(visible),
                    }
                )
    return rows


def _count_verdicts(pg, *, days: int) -> Counter:
    sources = sorted(public_feed_sources())
    counts: Counter = Counter()
    if not sources:
        return counts
    with pg.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ai_verdict, COUNT(*)
                FROM leads
                WHERE ai_verdict IS NOT NULL
                  AND source = ANY(%s)
                  AND created_at >= NOW() - make_interval(days => %s)
                GROUP BY ai_verdict
                """,
                (sources, int(days)),
            )
            for verdict, n in cur.fetchall():
                counts[str(verdict)] = int(n)
    return counts


def _scan_log_skip_filter(log_path: Path, *, tail_lines: int = 50000) -> tuple[int, int]:
    """(skip:filter count, L1 verdict lines) in tail of radar log."""
    if not log_path.is_file():
        return 0, 0
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0, 0
    lines = text.splitlines()[-tail_lines:]
    skip_n = sum(1 for ln in lines if _SKIP_FILTER_RE.search(ln))
    l1_n = sum(1 for ln in lines if _L1_VERDICT_RE.search(ln))
    return skip_n, l1_n


def _print_samples(label: str, samples: list[dict]) -> None:
    print(f"\n=== {label} ({len(samples)}) ===")
    for i, row in enumerate(samples, 1):
        reasons = "; ".join(row["reasons"]) if row["reasons"] else "—"
        print(
            f"{i:2}. [{row['source']}] score={row['score']} "
            f"visible={row['is_visible']} | {row['title']}"
        )
        print(f"    reasons: {reasons}")


def main() -> int:
    parser = argparse.ArgumentParser(description="NEON-AUDIT-FILTERS report")
    parser.add_argument("--profile", choices=("site", "legacy"), default="site")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--sample", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.profile:
        sys.argv = [sys.argv[0], "--profile", args.profile.strip()] + [
            a for a in sys.argv[1:] if a not in ("--profile", args.profile.strip())
        ]
    apply_profile_argv()
    load_radar_env()
    random.seed(args.seed)

    cfg = load_config()
    pg = pg_storage_from_config(cfg)
    if pg is None or not pg.enabled:
        print("DATABASE_URL не задан", file=sys.stderr)
        return 1

    print(f"[neon_audit_filters] profile={args.profile} days={args.days}")
    counts = _count_verdicts(pg, days=args.days)
    for verdict in ("Брать", "МИМО", "Сомнительно", "Пропущено"):
        if verdict in counts:
            print(f"  {verdict}: {counts[verdict]}")

    take = _sample_leads(pg, verdict="Брать", days=args.days, limit=args.sample)
    skip = _sample_leads(pg, verdict="МИМО", days=args.days, limit=args.sample)
    _print_samples("Брать (random)", take)
    _print_samples("МИМО (random)", skip)

    log_path = cfg.radar_log_path
    skip_log, l1_log = _scan_log_skip_filter(log_path)
    print(f"\n=== Log tail ({log_path.name}) ===")
    print(f"  skip:filter lines: {skip_log}")
    print(f"  L1 verdict lines: {l1_log}")
    if skip_log and l1_log:
        ratio = skip_log / max(l1_log, 1)
        print(f"  pre-L1 filter / L1 ratio: {ratio:.2f}")

    print("\n=== Спорные (5 случайных МИМО с score>=50) ===")
    with pg.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT title, ai_score, ai_reasons
                FROM leads
                WHERE ai_verdict = 'МИМО'
                  AND ai_score >= 50
                  AND source = ANY(%s)
                  AND created_at >= NOW() - make_interval(days => %s)
                ORDER BY RANDOM()
                LIMIT 5
                """,
                (sorted(public_feed_sources()), int(args.days)),
            )
            rows = cur.fetchall()
    for title, score, reasons in rows:
        if isinstance(reasons, str):
            try:
                reasons = json.loads(reasons)
            except json.JSONDecodeError:
                reasons = [reasons]
        rs = "; ".join(list(reasons or [])[:2])
        print(f"  score={score} | {str(title or '')[:100]} | {rs}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
