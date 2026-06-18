"""O220-L1-RETAG-PILOT: re-L1 on 40 visible old leads (10×4 niches) — tags only.

  .venv\\Scripts\\python.exe scripts\\o220_l1_retag_pilot.py --profile site --dry-run
  .venv\\Scripts\\python.exe scripts\\o220_l1_retag_pilot.py --profile site --apply
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
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

from ai_analyze import analyze_lite  # noqa: E402
from config import apply_profile_argv, load_config, load_radar_env, radar_profile  # noqa: E402
from pg_storage import NeonLeadRow, pg_storage_from_config  # noqa: E402
from rank import parse_lead_tags  # noqa: E402

PILOT_CATEGORIES: tuple[str, ...] = ("dev", "design", "marketing", "text")
PER_CATEGORY = 10
REPORT_PATH = _ROOT / "data" / "o220_l1_retag_pilot.json"
GATE_AVG_TAGS = 2.5
GATE_PCT_GE2 = 0.80
GATE_JUDGE_L1_USABLE = 0.70


def _listing_from_row(row: NeonLeadRow):
    return row.to_listing()


def _tags_from_raw(raw) -> list[str]:
    return parse_lead_tags(raw)


def _bucket_counts(rows: list[NeonLeadRow]) -> dict[str, int]:
    counts: dict[str, int] = {c: 0 for c in PILOT_CATEGORIES}
    for row in rows:
        cat = (row.category or "").strip().lower()
        if cat in counts:
            counts[cat] += 1
    return counts


def summarize_by_niche(leads: list[dict]) -> dict[str, dict]:
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for lead in leads:
        cat = (lead.get("category") or "").strip().lower()
        by_cat[cat].append(lead)

    summary: dict[str, dict] = {}
    for cat in PILOT_CATEGORIES:
        bucket = by_cat.get(cat, [])
        n = len(bucket)
        if n == 0:
            summary[cat] = {
                "count": 0,
                "avg_tags_before": 0.0,
                "avg_tags_after": 0.0,
                "pct_ge2_after": 0.0,
            }
            continue
        avg_before = sum(lead["tag_count_before"] for lead in bucket) / n
        avg_after = sum(lead["tag_count_after"] for lead in bucket) / n
        ge2 = sum(1 for lead in bucket if lead["tag_count_after"] >= 2) / n
        summary[cat] = {
            "count": n,
            "avg_tags_before": round(avg_before, 2),
            "avg_tags_after": round(avg_after, 2),
            "pct_ge2_after": round(ge2, 2),
        }
    return summary


def evaluate_gate(summary: dict[str, dict], *, judge_l1_usable: float | None = None) -> dict:
    niche_pass = all(
        summary.get(cat, {}).get("avg_tags_after", 0) >= GATE_AVG_TAGS
        or summary.get(cat, {}).get("pct_ge2_after", 0) >= GATE_PCT_GE2
        for cat in PILOT_CATEGORIES
        if summary.get(cat, {}).get("count", 0) > 0
    )
    global_ge2 = 0.0
    total = sum(s.get("count", 0) for s in summary.values())
    if total > 0:
        weighted = sum(
            s.get("pct_ge2_after", 0) * s.get("count", 0)
            for s in summary.values()
        )
        global_ge2 = weighted / total

    judge_ok = True
    if judge_l1_usable is not None:
        judge_ok = judge_l1_usable >= GATE_JUDGE_L1_USABLE

    passed = niche_pass and judge_ok
    return {
        "avg_tags_ge_2_5_per_niche_or_pct_ge2": niche_pass,
        "global_pct_ge2_after": round(global_ge2, 2),
        "judge_l1_usable_threshold": GATE_JUDGE_L1_USABLE,
        "judge_l1_usable": judge_l1_usable,
        "judge_ok": judge_ok,
        "passed": passed,
        "note": "Run preprod_ai_prod_audit --judge --judge-l1 to fill judge_l1_usable",
    }


def l1_prompt_fix_samples(leads: list[dict], *, max_samples: int = 5) -> list[dict]:
    """Thin-tag failures for Lead/PM prompt tuning."""
    bad = [
        lead
        for lead in leads
        if lead.get("tag_count_after", 0) < 2
    ]
    bad.sort(key=lambda x: x.get("tag_count_after", 0))
    out = []
    for lead in bad[:max_samples]:
        out.append(
            {
                "id": lead["id"],
                "category": lead["category"],
                "title": lead.get("title", "")[:120],
                "tags_before": lead.get("tags_before", []),
                "tags_after": lead.get("tags_after", []),
                "task_summary_after": lead.get("task_summary_after", ""),
            }
        )
    return out


def judge_command(lead_ids: list[int]) -> str:
    ids_csv = ",".join(str(i) for i in lead_ids)
    return (
        f".venv\\Scripts\\python.exe scripts\\preprod_ai_prod_audit.py "
        f"--profile site --lead-ids {ids_csv} --judge --judge-l1 --judge-l1-limit {len(lead_ids)}"
    )


def build_report(
    *,
    mode: str,
    leads: list[dict],
    bucket_short: dict[str, int] | None = None,
    judge_l1_usable: float | None = None,
) -> dict:
    summary = summarize_by_niche(leads)
    gate = evaluate_gate(summary, judge_l1_usable=judge_l1_usable)
    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "lead_ids": [lead["id"] for lead in leads],
        "leads": leads,
        "summary": {"by_niche": summary},
        "gate": gate,
    }
    if bucket_short:
        report["bucket_short"] = bucket_short
    if not gate["passed"] and mode == "apply":
        report["l1_prompt_fix"] = l1_prompt_fix_samples(leads)
    return report


def _write_report(report: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Report: {REPORT_PATH}")


def main() -> int:
    parser = argparse.ArgumentParser(description="O220-L1 retag pilot (40 leads)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Print selection only")
    mode.add_argument("--apply", action="store_true", help="Run analyze_lite + safe DB update")
    parser.add_argument("--profile", default="", help="site (default: env)")
    parser.add_argument(
        "--per-category",
        type=int,
        default=PER_CATEGORY,
        help=f"Leads per niche (default {PER_CATEGORY})",
    )
    args, _rest = parser.parse_known_args()

    if args.profile:
        sys.argv = [sys.argv[0], "--profile", args.profile.strip()] + [
            a for a in sys.argv[1:] if a not in ("--profile", args.profile.strip())
        ]
    apply_profile_argv()
    load_radar_env()

    if radar_profile() != "site":
        print("o220_l1_retag_pilot: только RADAR_PROFILE=site", file=sys.stderr)
        return 2

    cfg = load_config()
    pg = pg_storage_from_config(cfg)
    if pg is None or not pg.enabled:
        print("DATABASE_URL не задан", file=sys.stderr)
        return 1

    errors: list[str] = []
    rows = pg.fetch_retag_pilot_leads(
        per_category=args.per_category,
        categories=PILOT_CATEGORIES,
        errors=errors,
    )
    bucket_counts = _bucket_counts(rows)
    for cat, n in bucket_counts.items():
        if n < args.per_category:
            print(f"  bucket short: {cat}={n} (want {args.per_category})")

    tags_before_map = pg.fetch_lead_tags_by_ids(
        [r.lead_id for r in rows],
        errors=errors,
    )

    lead_records: list[dict] = []
    for row in rows:
        tags_before = tags_before_map.get(row.lead_id, [])
        rec = {
            "id": row.lead_id,
            "source": row.source,
            "external_id": row.external_id,
            "category": row.category,
            "title": row.title[:120],
            "tags_before": tags_before,
            "tag_count_before": len(tags_before),
            "tags_after": tags_before,
            "tag_count_after": len(tags_before),
            "category_after": row.category,
            "task_summary_after": "",
        }
        lead_records.append(rec)

        if args.dry_run:
            print(
                f"  id={row.lead_id} cat={row.category} "
                f"tags={tags_before!r} title={row.title[:60]!r}"
            )

    if args.dry_run:
        report = build_report(
            mode="dry-run",
            leads=lead_records,
            bucket_short={
                cat: bucket_counts[cat]
                for cat in PILOT_CATEGORIES
                if bucket_counts[cat] < args.per_category
            }
            or None,
        )
        _write_report(report)
        print(f"Selected: {len(rows)} leads")
        if errors:
            for e in errors:
                print(f"  err: {e}")
        return 0 if not errors else 1

    ok = 0
    for row, rec in zip(rows, lead_records):
        project = _listing_from_row(row)
        snippet = (project.listing_snippet or project.title or "").strip()
        log_prefix = f"o220:retag:id={row.lead_id}:"
        lite = analyze_lite(
            cfg,
            title=project.title,
            budget_text=project.budget_text,
            snippet=snippet,
            url=project.url,
            errors=errors,
            log_prefix=log_prefix,
        )
        pg.update_lite_retag_pilot(
            row.lead_id,
            project,
            lite=lite,
            errors=errors,
            body_snippet=snippet,
        )
        tags_after = list(lite.lead_tags) if lite else []
        rec["tags_after"] = tags_after
        rec["tag_count_after"] = len(tags_after)
        rec["category_after"] = (
            lite.primary_category if lite and lite.primary_category else row.category
        )
        rec["task_summary_after"] = lite.task_summary if lite else ""
        ok += 1
        print(f"  L1 id={row.lead_id} tags={len(tags_after)} cat={rec['category_after']}")

    report = build_report(
        mode="apply",
        leads=lead_records,
        bucket_short={
            cat: bucket_counts[cat]
            for cat in PILOT_CATEGORIES
            if bucket_counts[cat] < args.per_category
        }
        or None,
    )
    _write_report(report)

    lead_ids = [r.lead_id for r in rows]
    print(f"Готово: L1={ok} errors={len(errors)}")
    print("\n--- Judge (owner copy-paste) ---")
    print(judge_command(lead_ids))

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
