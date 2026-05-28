"""§ PRE-PROD-STRESS t1: матрица L1/L2 по 4 category → JSON отчёт.

Запуск (site, нужен OpenRouter в .env.site):

  .venv\\Scripts\\python.exe scripts\\preprod_ai_matrix.py --profile site
  .venv\\Scripts\\python.exe scripts\\preprod_ai_matrix.py --profile site --dry-run
  .venv\\Scripts\\python.exe scripts\\preprod_ai_matrix.py --profile site --category dev --limit 1
"""

from __future__ import annotations

import argparse
import json
import sys
import time
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
sys.path.insert(0, str(_ROOT / "scripts"))

from ai_analyze import AiAnalysis, AiLiteAnalysis, analyze_lite, analyze_premium
from config import apply_profile_argv, load_config, load_radar_env
from preprod_fixtures import CATEGORIES, PREPROD_LEAD_FIXTURES, PreprodLeadFixture


def _analysis_to_dict(obj: AiLiteAnalysis | AiAnalysis | None) -> dict | None:
    if obj is None:
        return None
    data: dict = {
        "verdict": obj.verdict,
        "lead_tags": list(obj.lead_tags),
    }
    if isinstance(obj, AiLiteAnalysis):
        data["task_summary"] = obj.task_summary
        data["ai_reasons"] = list(obj.ai_reasons)
        data["pending_tags"] = list(obj.pending_tags)
    else:
        data["work_summary"] = obj.work_summary
        data["approach"] = obj.approach
        data["reply_draft"] = obj.reply_draft
        data["tools_required"] = list(obj.tools_required)
        data["money"] = obj.money
        data["risks"] = obj.risks
    return data


def _run_fixture(cfg, fixture: PreprodLeadFixture) -> dict:
    errors: list[str] = []
    t0 = time.perf_counter()
    lite = analyze_lite(
        cfg,
        title=fixture.title,
        budget_text=fixture.budget_text,
        snippet=fixture.snippet,
        url=fixture.url,
        errors=errors,
        log_prefix=f"{fixture.id}:",
    )
    lite_ms = int((time.perf_counter() - t0) * 1000)

    description = f"{fixture.title}\n\n{fixture.snippet}"
    t1 = time.perf_counter()
    premium = analyze_premium(
        cfg,
        title=fixture.title,
        budget_text=fixture.budget_text,
        description=description,
        url=fixture.url,
        lite=lite,
        errors=errors,
        log_prefix=f"{fixture.id}:",
    )
    premium_ms = int((time.perf_counter() - t1) * 1000)

    reply_draft = (premium.reply_draft if premium else "") or ""
    task_summary = (lite.task_summary if lite else "") or ""

    return {
        "fixture_id": fixture.id,
        "category": fixture.category,
        "title": fixture.title,
        "lite_ok": lite is not None,
        "premium_ok": premium is not None,
        "lite_ms": lite_ms,
        "premium_ms": premium_ms,
        "task_summary_nonempty": bool(task_summary.strip()),
        "reply_draft_nonempty": bool(reply_draft.strip()),
        "tools_required_count": len(premium.tools_required) if premium else 0,
        "errors": errors,
        "lite": _analysis_to_dict(lite),
        "premium": _analysis_to_dict(premium),
    }


def _build_summary(results: list[dict]) -> dict:
    by_cat: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "total": 0,
            "lite_ok": 0,
            "premium_ok": 0,
            "empty_reply_draft": 0,
            "empty_task_summary": 0,
        }
    )
    for row in results:
        cat = row["category"]
        by_cat[cat]["total"] += 1
        if row["lite_ok"]:
            by_cat[cat]["lite_ok"] += 1
        if row["premium_ok"]:
            by_cat[cat]["premium_ok"] += 1
        if row["premium_ok"] and not row["reply_draft_nonempty"]:
            by_cat[cat]["empty_reply_draft"] += 1
        if row["lite_ok"] and not row["task_summary_nonempty"]:
            by_cat[cat]["empty_task_summary"] += 1

    s1_pass = all(
        by_cat[cat]["total"] >= 3
        and by_cat[cat]["lite_ok"] >= 3
        and by_cat[cat]["premium_ok"] >= 3
        and by_cat[cat]["empty_reply_draft"] == 0
        for cat in CATEGORIES
    )

    return {
        "total": len(results),
        "lite_ok": sum(1 for r in results if r["lite_ok"]),
        "premium_ok": sum(1 for r in results if r["premium_ok"]),
        "empty_reply_draft": sum(
            1 for r in results if r["premium_ok"] and not r["reply_draft_nonempty"]
        ),
        "by_category": dict(by_cat),
        "s1_pass": s1_pass,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PRE-PROD AI matrix (L1 + L2)")
    parser.add_argument("--profile", default="site", choices=("site", "legacy"))
    parser.add_argument("--dry-run", action="store_true", help="только фикстуры, без OpenRouter")
    parser.add_argument("--category", action="append", dest="categories")
    parser.add_argument("--limit", type=int, default=0, help="макс. фикстур (0 = все)")
    parser.add_argument(
        "--output",
        type=Path,
        default=_ROOT / "data" / "preprod_ai_report.json",
    )
    args = parser.parse_args()
    apply_profile_argv(["--profile", args.profile])

    fixtures = list(PREPROD_LEAD_FIXTURES)
    if args.categories:
        allowed = {c.strip().casefold() for c in args.categories}
        fixtures = [f for f in fixtures if f.category.casefold() in allowed]
    if args.limit > 0:
        fixtures = fixtures[: args.limit]

    if args.dry_run:
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "profile": args.profile,
            "dry_run": True,
            "fixtures": [f.to_dict() for f in fixtures],
            "summary": {"total": len(fixtures), "s1_pass": len(fixtures) >= 12},
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"dry-run: {len(fixtures)} fixtures → {args.output}")
        return 0

    load_radar_env()
    cfg = load_config()
    if not cfg.ai_active:
        print("AI_ENABLED=0 или нет ключа OpenRouter — матрица невозможна.", file=sys.stderr)
        return 2

    results = [_run_fixture(cfg, fx) for fx in fixtures]
    summary = _build_summary(results)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": args.profile,
        "models": {
            "lite": cfg.ai_model_summary,
            "premium": cfg.ai_model_premium,
        },
        "summary": summary,
        "results": results,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"matrix: {summary['lite_ok']}/{summary['total']} L1, "
          f"{summary['premium_ok']}/{summary['total']} L2 → {args.output}")
    print(f"S1: {'PASS' if summary['s1_pass'] else 'FAIL'} "
          f"(empty reply_draft: {summary['empty_reply_draft']})")
    return 0 if summary["s1_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
