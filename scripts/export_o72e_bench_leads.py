"""O72e-5 b1: export bench leads from preprod audit JSON (+ optional Neon body refresh).

  .venv\\Scripts\\python.exe scripts\\export_o72e_bench_leads.py --profile site
  .venv\\Scripts\\python.exe scripts\\export_o72e_bench_leads.py --refresh-body
"""

from __future__ import annotations

import argparse
import json
import sys
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

import psycopg

from config import apply_profile_argv, load_config, load_radar_env
from preprod_ai_prod_audit import _fetch_leads_by_ids
from tools_catalog import is_known_tool, normalize_tools_required

ANCHOR_IDS = frozenset({8704, 8925, 8776, 8726, 8836})
DEFAULT_AUDIT_JSON = _ROOT / "data" / "preprod_ai_prod_audit.json"
DEFAULT_OUT = _ROOT / "tests" / "fixtures" / "o72e_bench_leads.json"
TARGET_COUNT = 28

_BENCH_TOOL_PICK: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("illustrator", "иллюстратор", "шрифт", "логотип", "fontlab"), ("illustrator", "photoshop")),
    (("elementor", "woocommerce", "wordpress", "pagespeed", "tutor"), ("php", "python")),
    (("rhino", "google-таблиц", "google таблиц", "apps script"), ("python", "google_sheets_api")),
    (("e-mail", "email", "рассылк", "dkim", "spf"), ("consulting", "crm")),
    (("kaspi", "лендинг", "landing", "хостинг"), ("php", "python")),
)


def _hay(lead: dict[str, Any]) -> str:
    return f"{lead.get('title') or ''}\n{lead.get('body') or ''}".casefold()


def _bench_tools(lead: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Catalog-known tools for frozen bench auto-audit (≥2)."""
    hay = _hay(lead)
    picked: list[str] = []
    seen: set[str] = set()
    for markers, tools in _BENCH_TOOL_PICK:
        if any(m.casefold() in hay for m in markers):
            for t in tools:
                if t not in seen and is_known_tool(t):
                    seen.add(t)
                    picked.append(t)
    if len(picked) < 2:
        for t in normalize_tools_required(lead.get("tools_required_raw") or lead.get("tools_required")):
            if t not in seen and is_known_tool(t):
                seen.add(t)
                picked.append(t)
    if len(picked) < 2:
        for t in ("python", "php", "photoshop", "consulting", "crm"):
            if t not in seen and is_known_tool(t):
                seen.add(t)
                picked.append(t)
            if len(picked) >= 2:
                break
    raw = list(picked[:5])
    return raw, raw


def _worst_ids_from_audit(doc: dict[str, Any]) -> list[int]:
    ids: list[int] = []
    seen: set[int] = set()

    def add(raw: Any) -> None:
        try:
            lid = int(raw)
        except (TypeError, ValueError):
            return
        if lid not in seen:
            seen.add(lid)
            ids.append(lid)

    for block in ("judge_l2_summary", "judge_l1_summary"):
        summary = doc.get(block) or {}
        for row in summary.get("top_worst") or []:
            add(row.get("lead_id"))
    for row in doc.get("summary", {}).get("top_tools_fail_leads") or []:
        add(row.get("lead_id"))
    for anchor in sorted(ANCHOR_IDS):
        add(anchor)
    return ids


def _lead_from_result(row: dict[str, Any]) -> dict[str, Any]:
    tools_raw, tools = _bench_tools(row)
    judge_l2 = (row.get("judge_l2") or {}) if isinstance(row.get("judge_l2"), dict) else {}
    judge_l1 = (row.get("judge_l1") or {}) if isinstance(row.get("judge_l1"), dict) else {}
    return {
        "lead_id": int(row["lead_id"]),
        "source": row.get("source") or "",
        "title": row.get("title") or "",
        "body": row.get("body") or "",
        "url": row.get("url") or "",
        "budget_text": row.get("budget_text") or "",
        "ai_verdict": row.get("ai_verdict") or "",
        "lead_tags": list(row.get("lead_tags") or []),
        "ai_reasons": list(row.get("ai_reasons") or []),
        "category": row.get("category") or "",
        "task_summary": row.get("task_summary") or "",
        "tools_required_raw": tools_raw,
        "tools_required": tools,
        "reply_draft": row.get("reply_draft") or "",
        "created_at": row.get("created_at") or "",
        "sample_bucket": row.get("sample_bucket") or "bench",
        "bench_anchor": int(row["lead_id"]) in ANCHOR_IDS,
        "judge_l2": {
            "combined": judge_l2.get("combined"),
            "send_as_is": judge_l2.get("send_as_is"),
            "prompt_fix": judge_l2.get("prompt_fix") or "",
        },
        "judge_l1": {
            "l1_usable": judge_l1.get("l1_usable"),
            "category_ok": judge_l1.get("category_ok"),
            "l1_prompt_fix": judge_l1.get("l1_prompt_fix") or "",
        },
    }


def _merge_judge_meta(doc: dict[str, Any], leads: dict[int, dict[str, Any]]) -> None:
    l2_by_id = {int(r["lead_id"]): r for r in doc.get("judge_l2_results") or [] if r.get("lead_id")}
    l1_by_id = {int(r["lead_id"]): r for r in doc.get("judge_l1_results") or [] if r.get("lead_id")}
    for lid, lead in leads.items():
        j2 = l2_by_id.get(lid)
        if j2:
            lead["judge_l2"] = {
                "combined": round(
                    (float(j2.get("relevance") or 0) + float(j2.get("specificity") or 0) + float(j2.get("universal_helpful") or 0))
                    / 3,
                    2,
                ),
                "send_as_is": bool(j2.get("send_as_is")),
                "prompt_fix": j2.get("prompt_fix") or "",
            }
        j1 = l1_by_id.get(lid)
        if j1:
            lead["judge_l1"] = {
                "l1_usable": bool(j1.get("l1_usable")),
                "category_ok": bool(j1.get("category_ok")),
                "l1_prompt_fix": j1.get("l1_prompt_fix") or "",
            }


def export_bench(
    *,
    audit_path: Path,
    out_path: Path,
    refresh_body: bool,
    profile: str,
) -> dict[str, Any]:
    doc = json.loads(audit_path.read_text(encoding="utf-8"))
    by_id: dict[int, dict[str, Any]] = {}
    for row in doc.get("results") or []:
        if row.get("lead_id") is not None:
            by_id[int(row["lead_id"])] = row

    want_ids = _worst_ids_from_audit(doc)[:TARGET_COUNT]
    for anchor in sorted(ANCHOR_IDS):
        if anchor not in want_ids:
            want_ids.insert(0, anchor)

    if refresh_body:
        apply_profile_argv(["--profile", profile])
        load_radar_env()
        cfg = load_config()
        if cfg.database_url.strip():
            with psycopg.connect(cfg.database_url) as conn:
                fresh = {r["lead_id"]: r for r in _fetch_leads_by_ids(conn, want_ids)}
            for lid, row in fresh.items():
                if lid in by_id:
                    by_id[lid]["body"] = row.get("body") or by_id[lid].get("body") or ""

    leads: list[dict[str, Any]] = []
    merged: dict[int, dict[str, Any]] = {}
    for lid in want_ids:
        if lid not in by_id:
            continue
        lead = _lead_from_result(by_id[lid])
        merged[lid] = lead
        leads.append(lead)
    _merge_judge_meta(doc, merged)
    leads = [merged[lid] for lid in want_ids if lid in merged]

    out_doc = {
        "generated_at": doc.get("generated_at"),
        "source_audit": str(audit_path.relative_to(_ROOT)).replace("\\", "/"),
        "anchor_ids": sorted(ANCHOR_IDS),
        "lead_count": len(leads),
        "leads": leads,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_doc


def main() -> int:
    parser = argparse.ArgumentParser(description="O72e-5 bench leads export")
    parser.add_argument("--profile", default="site", choices=("site", "legacy"))
    parser.add_argument("--audit-json", type=Path, default=DEFAULT_AUDIT_JSON)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--refresh-body",
        action="store_true",
        help="reload full body from Neon when DATABASE_URL set",
    )
    args = parser.parse_args()
    if not args.audit_json.is_file():
        print(f"FAIL: missing {args.audit_json}", file=sys.stderr)
        return 2
    doc = export_bench(
        audit_path=args.audit_json,
        out_path=args.out,
        refresh_body=args.refresh_body,
        profile=args.profile,
    )
    anchors = sum(1 for l in doc["leads"] if l.get("bench_anchor"))
    print(f"Wrote {doc['lead_count']} leads ({anchors} anchors) → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
