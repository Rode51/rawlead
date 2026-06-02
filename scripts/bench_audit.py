"""O72e-5 b3: auto-audit bench fixture (no OpenRouter judge).

  .venv\\Scripts\\python.exe scripts\\bench_audit.py --fixtures tests/fixtures/o72e_bench_leads.json

Exit 0 iff all anchor leads pass draft_only + tools.
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
sys.path.insert(0, str(_ROOT / "scripts"))

from preprod_ai_prod_audit import audit_lead, build_sample_and_audit  # noqa: E402

DEFAULT_FIXTURES = _ROOT / "tests" / "fixtures" / "o72e_bench_leads.json"


def _load_leads(path: Path) -> tuple[list[int], list[dict[str, Any]]]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    anchor_ids = [int(x) for x in doc.get("anchor_ids") or []]
    leads = list(doc.get("leads") or [])
    if not anchor_ids:
        anchor_ids = sorted({int(l["lead_id"]) for l in leads if l.get("bench_anchor")})
    return anchor_ids, leads


def run_bench(path: Path) -> tuple[bool, dict[str, Any]]:
    path = path.resolve()
    anchor_ids, leads = _load_leads(path)
    results, summary = build_sample_and_audit(leads)
    by_id = {int(r["lead_id"]): r for r in results}

    anchor_rows: list[dict[str, Any]] = []
    anchor_pass = 0
    for lid in anchor_ids:
        row = by_id.get(lid)
        if not row:
            anchor_rows.append({"lead_id": lid, "missing": True, "pass": False})
            continue
        ok = bool(row.get("draft_only_pass")) and bool(row.get("tools_pass"))
        if ok:
            anchor_pass += 1
        anchor_rows.append(
            {
                "lead_id": lid,
                "draft_only_pass": row.get("draft_only_pass"),
                "tools_pass": row.get("tools_pass"),
                "fails": row.get("fails") or [],
                "pass": ok,
            }
        )

    gate = anchor_pass == len(anchor_ids) and len(anchor_ids) >= 5
    report = {
        "fixtures": str(path.relative_to(_ROOT.resolve())).replace("\\", "/"),
        "total": summary.get("total"),
        "draft_only_pass_pct": summary.get("draft_only_pass_pct"),
        "tools_pass_pct": summary.get("tools_pass_pct"),
        "anchor_ids": anchor_ids,
        "anchor_pass": f"{anchor_pass}/{len(anchor_ids)}",
        "anchor_gate": gate,
        "anchors": anchor_rows,
    }
    return gate, report


def main() -> int:
    parser = argparse.ArgumentParser(description="O72e-5 bench auto-audit")
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    args = parser.parse_args()
    if not args.fixtures.is_file():
        print(f"FAIL: missing {args.fixtures}", file=sys.stderr)
        return 2

    gate, report = run_bench(args.fixtures)
    print(
        f"Bench {report['fixtures']}: draft={report['draft_only_pass_pct']}% "
        f"tools={report['tools_pass_pct']}% · anchors {report['anchor_pass']}"
    )
    for row in report["anchors"]:
        mark = "OK" if row.get("pass") else "FAIL"
        if row.get("missing"):
            print(f"  #{row['lead_id']}: MISSING")
            continue
        print(
            f"  #{row['lead_id']}: {mark} "
            f"draft={row.get('draft_only_pass')} tools={row.get('tools_pass')}"
        )
        if not row.get("pass") and row.get("fails"):
            print(f"    fails: {', '.join(row['fails'][:3])}")

    if gate:
        print("O72e-5 bench GATE: PASS (anchors 5/5)")
        return 0
    print("O72e-5 bench GATE: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
