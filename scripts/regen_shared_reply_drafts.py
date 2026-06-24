"""O72d: перегенерация shared reply_draft в prod Postgres (visible leads, gemini-2.5-pro).

  .venv\\Scripts\\python.exe scripts\\regen_shared_reply_drafts.py --profile site --dry-run --limit 5
  .venv\\Scripts\\python.exe scripts\\regen_shared_reply_drafts.py --profile site --apply --limit 80
  .venv\\Scripts\\python.exe scripts\\regen_shared_reply_drafts.py --profile site --apply --lead-ids 7051,7019

После regen — judge:
  .venv\\Scripts\\python.exe scripts\\preprod_ai_prod_audit.py --profile site --judge --judge-limit 40
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

import psycopg

from ai_analyze import (
    AiAnalyzeError,
    AiLiteAnalysis,
    analyze_shared_reply_draft,
    reply_draft_cliche_warn,
    _validate_reply_draft_maybe,
    _validate_reply_draft_take,
)
from config import Config, apply_profile_argv, load_config, load_radar_env
from public_feed import public_feed_source_sql
from reply_draft_strip import strip_reply_draft_price_deadline

from preprod_ai_prod_audit import (  # noqa: E402
    _SELECT_COLS,
    _fetch_leads_by_ids,
    _filter_fresh_for_judge,
    _norm_verdict,
    _parse_judge_since,
    _row_to_lead,
    _stratified_sample,
)

_SKIP_VERDICTS = frozenset({"мимо", "пропустить", "skip"})
_REGEN_VERDICTS = frozenset({"брать", "брат", "take", "сомнительно", "maybe", "ok"})


def _lite_from_lead(lead: dict[str, Any]) -> AiLiteAnalysis:
    from lead_category import CATEGORIES

    v_norm = _norm_verdict(lead.get("ai_verdict") or "")
    cat_raw = (lead.get("category") or "").strip()
    primary_category = cat_raw if cat_raw in CATEGORIES else ""
    return AiLiteAnalysis(
        feed_visible=v_norm not in _SKIP_VERDICTS,
        task_summary=(lead.get("task_summary") or "").strip(),
        lead_tags=tuple(lead.get("lead_tags") or ()),
        ai_reasons=tuple(lead.get("ai_reasons") or ()),
        primary_category=primary_category,
    )


def _too_vague_draft(draft: str) -> str | None:
    low = draft.casefold()
    if "обсуд" in low and "?" not in draft:
        return "vague:discuss_without_question"
    if low.count("подходящ") >= 2 or "оптимальн" in low and "?" not in draft:
        return "vague:generic_offer"
    return None


def _validate_draft(verdict: str, draft: str) -> str:
    v = _norm_verdict(verdict)
    if v == "брать":
        return _validate_reply_draft_take(draft)
    if v == "сомнительно":
        return _validate_reply_draft_maybe(draft)
    raise AiAnalyzeError(f"skip verdict {verdict!r}")


def regen_one_lead(
    cfg: Config,
    lead: dict[str, Any],
    *,
    max_attempts: int = 4,
    reject_cliche: bool = True,
    log_prefix: str = "",
) -> dict[str, Any]:
    """Generate shared draft; returns result dict (no DB write)."""
    lead_id = int(lead["lead_id"])
    verdict = lead.get("ai_verdict") or ""
    v_norm = _norm_verdict(verdict)
    if v_norm in _SKIP_VERDICTS:
        return {"lead_id": lead_id, "status": "skip_verdict", "verdict": v_norm}

    if not (lead.get("task_summary") or "").strip():
        return {"lead_id": lead_id, "status": "skip_empty_l1"}

    lite = _lite_from_lead(lead)
    tools = list(lead.get("tools_required") or [])
    prefix = log_prefix or f"regen:{lead_id}:"
    ai_errors: list[str] = []
    old_draft = (lead.get("reply_draft") or "").strip()

    for attempt in range(max(1, max_attempts)):
        raw = analyze_shared_reply_draft(
            cfg,
            title=lead.get("title") or "",
            budget_text=lead.get("budget_text") or "",
            lite=lite,
            tools_required=tools,
            description=lead.get("body") or "",
            source=lead.get("source") or "",
            url=lead.get("url") or "",
            errors=ai_errors,
            log_prefix=prefix,
            timeout_sec=90.0,
        )
        if not raw:
            if not ai_errors:
                ai_errors.append(f"attempt {attempt + 1}: analyze_shared returned empty")
            time.sleep(min(2 ** attempt, 8))
            continue
        draft = strip_reply_draft_price_deadline(raw.strip())
        try:
            draft = _validate_draft(verdict, draft)
        except AiAnalyzeError as exc:
            ai_errors.append(str(exc))
            time.sleep(min(2 ** attempt, 8))
            continue
        cliche = reply_draft_cliche_warn(draft)
        if reject_cliche and cliche:
            ai_errors.append(cliche)
            time.sleep(min(2 ** attempt, 8))
            continue
        vague = _too_vague_draft(draft)
        if reject_cliche and vague:
            ai_errors.append(vague)
            time.sleep(min(2 ** attempt, 8))
            continue
        return {
            "lead_id": lead_id,
            "status": "ok",
            "reply_draft": draft,
            "reply_draft_old": old_draft[:200],
            "reply_draft_new": draft[:200],
            "old_len": len(old_draft),
            "new_len": len(draft),
            "changed": draft != old_draft,
            "cliche_warn": cliche,
            "attempts": attempt + 1,
        }

    detail = "; ".join(ai_errors) if ai_errors else "no draft from model"
    return {"lead_id": lead_id, "status": "fail", "error": detail}


def _persist_reply_draft(conn: psycopg.Connection, lead_id: int, draft: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE leads SET reply_draft = %s WHERE id = %s",
            (draft, lead_id),
        )
    conn.commit()


def fetch_regen_candidates(
    conn: psycopg.Connection,
    *,
    limit: int,
    src_sql: str,
    src_params: list[Any],
    since: datetime | None = None,
) -> list[dict[str, Any]]:
    """Stratified visible leads with L1+verdict suitable for shared L2 regen."""
    since_sql, since_params = "", []
    if since is not None:
        from preprod_ai_prod_audit import _since_sql

        since_sql, since_params = _since_sql(since)
    pool = _stratified_sample(
        conn,
        n=limit,
        src_sql=src_sql,
        src_params=src_params,
        pool_size=3000,
        since_sql=since_sql,
        since_params=since_params,
        require_reply_draft=False,
    )
    out: list[dict[str, Any]] = []
    for lead in pool:
        v = _norm_verdict(lead.get("ai_verdict") or "")
        if v not in _REGEN_VERDICTS:
            continue
        if not (lead.get("task_summary") or "").strip():
            continue
        lead["sample_bucket"] = lead.get("sample_bucket", "regen")
        out.append(lead)
        if len(out) >= limit:
            break
    return out


def run_regen(
    cfg: Config,
    leads: list[dict[str, Any]],
    *,
    apply: bool,
    sleep_sec: float,
    reject_cliche: bool,
) -> dict[str, Any]:
    if not cfg.database_url.strip():
        raise SystemExit("DATABASE_URL empty — set in .env / .env.site")

    ok = fail = skip = 0
    changed = 0
    results: list[dict[str, Any]] = []

    with psycopg.connect(cfg.database_url) as conn:
        for i, lead in enumerate(leads):
            print(f"[{i + 1}/{len(leads)}] lead #{lead['lead_id']} …", flush=True)
            res = regen_one_lead(
                cfg,
                lead,
                reject_cliche=reject_cliche,
                log_prefix=f"regen:{lead['lead_id']}:",
            )
            results.append(res)
            st = res.get("status")
            if st == "ok":
                ok += 1
                if res.get("changed"):
                    changed += 1
                if apply and res.get("reply_draft"):
                    _persist_reply_draft(conn, int(res["lead_id"]), res["reply_draft"])
                print(f"  ok changed={res.get('changed')}", flush=True)
            elif st in ("skip_verdict", "skip_empty_l1"):
                skip += 1
                print(f"  skip {st}", flush=True)
            else:
                fail += 1
                print(f"  fail: {res.get('error', '')[:100]}", flush=True)

            if sleep_sec > 0 and i + 1 < len(leads):
                time.sleep(sleep_sec)

    return {
        "total": len(leads),
        "ok": ok,
        "fail": fail,
        "skip": skip,
        "changed": changed,
        "apply": apply,
        "model": cfg.ai_model_shared_draft,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="O72d regen shared reply_draft in prod Postgres")
    parser.add_argument("--profile", default="site", choices=("site", "legacy"))
    parser.add_argument("--limit", type=int, default=80, help="50–100 recommended")
    parser.add_argument("--lead-ids", default="", help="comma-separated lead ids")
    parser.add_argument("--apply", action="store_true", help="write to Postgres (default: dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="explicit dry-run (default)")
    parser.add_argument("--sleep", type=float, default=1.5, help="pause between OpenRouter calls")
    parser.add_argument(
        "--allow-cliche",
        action="store_true",
        help="save drafts even if cliche warn (default: retry until clean)",
    )
    parser.add_argument(
        "--since",
        default="",
        help="O72e-3: only leads with created_at on/after YYYY-MM-DD",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=_ROOT / "data" / "regen_shared_reply_drafts.json",
    )
    args = parser.parse_args()
    apply_profile_argv(["--profile", args.profile])
    load_radar_env()
    cfg = load_config()

    if not cfg.ai_active:
        print("FAIL: AI inactive (OPENROUTER_API_KEY?)")
        return 1

    src_sql, src_params = public_feed_source_sql()
    lead_ids = [int(x.strip()) for x in args.lead_ids.split(",") if x.strip()]

    with psycopg.connect(cfg.database_url) as conn:
        if lead_ids:
            leads = _fetch_leads_by_ids(conn, lead_ids)
        else:
            leads = fetch_regen_candidates(
                conn, limit=max(1, args.limit), src_sql=src_sql, src_params=src_params
            )

    if not leads:
        print("No leads to regen")
        return 1

    if args.since.strip():
        since = _parse_judge_since(args.since.strip())
        before = len(leads)
        leads = _filter_fresh_for_judge(leads, since=since)
        print(f"since {args.since.strip()}: {len(leads)}/{before} leads")

    if not leads:
        print("No leads after --since filter")
        return 1

    apply = bool(args.apply)

    print(
        f"O72d regen: {len(leads)} leads · model={cfg.ai_model_shared_draft} · "
        f"{'APPLY' if apply else 'DRY-RUN'}"
    )
    summary = run_regen(
        cfg,
        leads,
        apply=apply,
        sleep_sec=max(0.0, float(args.sleep)),
        reject_cliche=not args.allow_cliche,
    )
    summary["generated_at"] = datetime.now(timezone.utc).isoformat()
    summary["profile"] = args.profile
    summary["limit"] = args.limit

    out_path = args.json_out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        f"done: ok={summary['ok']} fail={summary['fail']} skip={summary['skip']} "
        f"changed={summary['changed']} -> {out_path}"
    )
    fails = [r for r in summary["results"] if r.get("status") == "fail"][:5]
    for r in fails:
        print(f"  fail #{r['lead_id']}: {r.get('error', '')[:120]}")

    return 0 if summary["fail"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
