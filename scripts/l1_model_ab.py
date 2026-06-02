"""O72e-9: A/B L1 models on bench + gate worst leads (offline replay, heuristic score).

  .venv\\Scripts\\python.exe scripts\\l1_model_ab.py --profile site
  .venv\\Scripts\\python.exe scripts\\l1_model_ab.py --profile site --limit 24

Writes data/l1_model_ab_<ts>.json · no Sonnet judge.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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

from ai_analyze import analyze_lite, resolve_l1_primary_category  # noqa: E402
from config import Config, apply_profile_argv, load_config, load_radar_env  # noqa: E402

BENCH_FIXTURE = _ROOT / "tests" / "fixtures" / "o72e_bench_leads.json"

# Gate 063753Z worst L1 + O72e-8 bench anchors (≥24 ids)
DEFAULT_WORST_IDS = (
    9928,
    9924,
    9913,
    9911,
    9909,
    9881,
    9849,
    9835,
    9833,
    9831,
    9320,
    8774,
    8752,
    8736,
    8702,
    9520,
    9404,
    8836,
    8726,
    8776,
    8704,
    8925,
    8720,
    8734,
    8782,
    8915,
)

L1_MODELS: tuple[tuple[str, str], ...] = (
    ("baseline", "google/gemini-2.5-flash-lite"),
    ("B", "qwen/qwen-3.5-flash-02-23"),
    ("C", "mistralai/mistral-small-3.2-24b-instruct"),
    ("D", "openai/gpt-4o-mini"),
)
# E: only if all B/C/D <60% heuristic — run with --include-flash
L1_MODEL_E = ("E", "google/gemini-2.5-flash")
_MODEL_BY_NAME = dict(L1_MODELS)

_CATEGORY_EXPECT: dict[int, str] = {
    8726: "marketing",
    8776: "dev",
    8836: "dev",
    8774: "dev",
    8752: "dev",
    8736: "dev",
    8702: "dev",
    8704: "design",
    8925: "dev",
    9928: "dev",
    9924: "design",
    9913: "dev",
    9909: "marketing",
    9881: "design",
    9849: "dev",
    9835: "text",
    9833: "dev",
    9831: "design",
    9911: "design",
}


def _ts_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_leads(limit: int) -> list[dict[str, Any]]:
    if not BENCH_FIXTURE.is_file():
        raise SystemExit(f"Missing {BENCH_FIXTURE}")
    doc = json.loads(BENCH_FIXTURE.read_text(encoding="utf-8"))
    by_id = {int(l["lead_id"]): l for l in doc.get("leads") or []}
    ids: list[int] = []
    for lid in DEFAULT_WORST_IDS:
        if lid in by_id and lid not in ids:
            ids.append(lid)
        if len(ids) >= limit:
            break
    for l in doc.get("leads") or []:
        lid = int(l["lead_id"])
        if lid not in ids:
            ids.append(lid)
        if len(ids) >= limit:
            break
    return [by_id[i] for i in ids if i in by_id]


def _score_row(
    lead: dict[str, Any],
    *,
    feed_visible: bool,
    task_summary: str,
    category: str,
    lead_tags: tuple[str, ...],
) -> dict[str, Any]:
    lead_id = int(lead["lead_id"])
    expected = _CATEGORY_EXPECT.get(lead_id)
    cat_ok = expected is None or category == expected
    summary_ok = bool(task_summary.strip()) and len(task_summary.strip()) >= 20
    tags_ok = bool(lead_tags) if feed_visible else True
    heuristic_usable = feed_visible and summary_ok and cat_ok and tags_ok
    return {
        "lead_id": lead_id,
        "feed_visible": feed_visible,
        "category": category,
        "category_ok": cat_ok,
        "summary_ok": summary_ok,
        "lead_tags": list(lead_tags),
        "task_summary": task_summary[:200],
        "heuristic_usable": heuristic_usable,
    }


def _run_model(cfg: Config, model: str, leads: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    ok = 0
    for lead in leads:
        title = lead.get("title") or ""
        body = lead.get("body") or ""
        snippet = body.strip() or title
        errors: list[str] = []
        lite = analyze_lite(
            cfg,
            title=title,
            budget_text=lead.get("budget_text") or "",
            snippet=snippet,
            url=lead.get("url") or "",
            errors=errors,
            model=model,
            log_prefix=f"ab:{lead['lead_id']}:",
        )
        if lite is None:
            rows.append(
                {
                    "lead_id": lead["lead_id"],
                    "error": "; ".join(errors)[:200],
                    "heuristic_usable": False,
                }
            )
            time.sleep(0.5)
            continue
        category = resolve_l1_primary_category(
            lite.primary_category,
            lite.lead_tags,
            title=title,
            snippet=snippet,
        )
        row = _score_row(
            lead,
            feed_visible=lite.feed_visible,
            task_summary=lite.task_summary,
            category=category,
            lead_tags=lite.lead_tags,
        )
        rows.append(row)
        if row["heuristic_usable"]:
            ok += 1
        time.sleep(0.8)
    pct = round(ok / len(leads) * 100, 1) if leads else 0.0
    cat_ok_n = sum(1 for r in rows if r.get("category_ok"))
    cat_pct = round(cat_ok_n / len(leads) * 100, 1) if leads else 0.0
    return {
        "model": model,
        "scored": len(rows),
        "heuristic_usable_pct": pct,
        "heuristic_usable_ok": ok,
        "category_ok_pct": cat_pct,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="O72e-9 L1 model A/B")
    parser.add_argument("--profile", default="site", choices=("site", "legacy"))
    parser.add_argument("--limit", type=int, default=24, help="min 24 lead ids")
    parser.add_argument(
        "--include-flash",
        action="store_true",
        help="add gemini-2.5-flash (E) if B/C/D <60%%",
    )
    args = parser.parse_args()
    apply_profile_argv(args.profile)
    load_radar_env()
    cfg = load_config()

    if not cfg.ai_active:
        print("AI_ENABLED=0 — set OpenRouter in .env.site", file=sys.stderr)
        return 1

    leads = _load_leads(max(24, args.limit))
    models = list(L1_MODELS)
    print(f"L1 A/B on {len(leads)} leads × {len(models)} models …", flush=True)

    results: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": args.profile,
        "lead_ids": [l["lead_id"] for l in leads],
        "models": {},
    }
    best_name = ""
    best_pct = -1.0
    for name, model in models:
        print(f"  → {name} ({model}) …", flush=True)
        block = _run_model(cfg, model, leads)
        results["models"][name] = block
        pct = block["heuristic_usable_pct"]
        print(
            f"     heuristic_usable={pct}% cat_ok={block.get('category_ok_pct')}% "
            f"({block['heuristic_usable_ok']}/{len(leads)})",
            flush=True,
        )
        if pct > best_pct:
            best_pct = pct
            best_name = name

    if args.include_flash and best_pct < 60.0:
        name, model = L1_MODEL_E
        print(f"  → {name} ({model}) [E fallback] …", flush=True)
        block = _run_model(cfg, model, leads)
        results["models"][name] = block
        pct = block["heuristic_usable_pct"]
        print(f"     heuristic_usable={pct}%", flush=True)
        if pct > best_pct:
            best_pct = pct
            best_name = name

    results["winner_heuristic"] = {
        "name": best_name,
        "model": _MODEL_BY_NAME.get(best_name, ""),
        "heuristic_usable_pct": best_pct,
    }
    results["recommendation"] = (
        f"Set OPENROUTER_MODEL_SUMMARY={results['winner_heuristic']['model']}"
        if best_name
        else ""
    )

    out = _ROOT / "data" / f"l1_model_ab_{_ts_slug()}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Winner (heuristic): {best_name} {best_pct}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
