"""O99: перегенерация personal reply_draft в user_lead_replies (L3 uniquify).

  .venv\\Scripts\\python.exe scripts\\regen_personal_reply_drafts.py --profile site --dry-run --limit 30
  .venv\\Scripts\\python.exe scripts\\regen_personal_reply_drafts.py --profile site --apply --since 2026-06-01

После regen personal + shared — judge L3 честно по БД.
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

from ai_analyze import rephrase_reply_draft_per_user
from config import Config, apply_profile_argv, load_config, load_radar_env
from l3_human_style import l3_too_similar, reply_ai_smell_reason
from public_feed import public_feed_source_sql
from reply_draft_strip import strip_reply_draft_price_deadline

from preprod_ai_prod_audit import (  # noqa: E402
    _filter_fresh_for_judge,
    _parse_judge_since,
    _stratified_sample,
)


def fetch_personal_regen_pairs(
    conn: psycopg.Connection,
    *,
    limit: int,
    src_sql: str,
    src_params: list[Any],
    since=None,
) -> list[dict[str, Any]]:
    """user_lead_replies + fresh shared reply_draft on lead."""
    since_sql, since_params = "", []
    if since is not None:
        from preprod_ai_prod_audit import _since_sql

        since_sql, since_params = _since_sql(since)
    leads = _stratified_sample(
        conn,
        n=limit * 3,
        src_sql=src_sql,
        src_params=src_params,
        pool_size=3000,
        since_sql=since_sql,
        since_params=since_params,
    )
    if since is not None:
        leads = _filter_fresh_for_judge(leads, since=since)
    lead_ids = [int(l["lead_id"]) for l in leads if l.get("lead_id")]
    if not lead_ids:
        return []

    sql = """
        SELECT ulr.user_id::text, ulr.lead_id, ulr.reply_draft AS personal_old,
               COALESCE(l.reply_draft, '') AS shared
        FROM user_lead_replies ulr
        JOIN leads l ON l.id = ulr.lead_id
        WHERE ulr.deleted_at IS NULL
          AND ulr.lead_id = ANY(%s)
          AND length(trim(ulr.reply_draft)) > 20
          AND length(trim(COALESCE(l.reply_draft, ''))) > 30
        ORDER BY ulr.created_at DESC
    """
    with conn.cursor() as cur:
        cur.execute(sql, (lead_ids,))
        rows = cur.fetchall()

    shared_by_lead = {int(l["lead_id"]): (l.get("reply_draft") or "").strip() for l in leads}
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for row in rows:
        uid, lid = str(row[0]), int(row[1])
        key = (uid, lid)
        if key in seen:
            continue
        shared = (shared_by_lead.get(lid) or (row[3] or "")).strip()
        if not shared:
            continue
        seen.add(key)
        out.append(
            {
                "user_id": uid,
                "lead_id": lid,
                "shared": shared,
                "personal_old": (row[2] or "").strip(),
            }
        )
        if len(out) >= limit:
            break
    return out


def _persist_personal(conn: psycopg.Connection, user_id: str, lead_id: int, draft: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE user_lead_replies
            SET reply_draft = %s, created_at = NOW(), deleted_at = NULL
            WHERE user_id = %s::uuid AND lead_id = %s
            """,
            (draft, user_id, lead_id),
        )
    conn.commit()


def run_regen_personal(
    cfg: Config,
    pairs: list[dict[str, Any]],
    *,
    apply: bool,
    sleep_sec: float,
    force: bool = False,
) -> dict[str, Any]:
    ok = fail = skip = 0
    changed = 0
    results: list[dict[str, Any]] = []

    with psycopg.connect(cfg.database_url) as conn:
        for i, row in enumerate(pairs):
            uid, lid = row["user_id"], row["lead_id"]
            shared = row["shared"]
            old = row["personal_old"]
            print(f"[{i + 1}/{len(pairs)}] user={uid[:8]}… lead #{lid}", flush=True)

            stale = (
                reply_ai_smell_reason(old) is not None
                or l3_too_similar(shared, old)
                or "заинтересов" in old.casefold()
            )
            if not force and not stale:
                skip += 1
                print("  skip: already fresh", flush=True)
                results.append({"lead_id": lid, "user_id": uid, "status": "skip_fresh"})
                continue

            errors: list[str] = []
            from ai_analyze import rephrase_reply_draft_per_user_model

            personal = rephrase_reply_draft_per_user(
                cfg,
                base_reply_draft=shared,
                user_id=uid,
                lead_id=lid,
                timeout_sec=60.0,
                errors=errors,
                log_prefix=f"regen-l3:{lid}:",
                model_override=rephrase_reply_draft_per_user_model(cfg),
            )
            if not personal:
                fail += 1
                detail = "; ".join(errors) if errors else "rephrase returned None"
                from ai_analyze import rephrase_reply_draft_per_user_model

                model = rephrase_reply_draft_per_user_model(cfg) or "?"
                print(
                    f"  fail model={model} shared_len={len(shared)} "
                    f"old_len={len(old)}: {detail[:200]}",
                    flush=True,
                )
                results.append(
                    {
                        "lead_id": lid,
                        "user_id": uid,
                        "status": "fail",
                        "error": detail,
                        "model": model,
                    }
                )
                continue

            personal = strip_reply_draft_price_deadline(personal.strip())
            is_changed = personal != old
            if apply:
                _persist_personal(conn, uid, lid, personal)
            ok += 1
            if is_changed:
                changed += 1
            print(f"  ok changed={is_changed}", flush=True)
            results.append(
                {
                    "lead_id": lid,
                    "user_id": uid,
                    "status": "ok",
                    "changed": is_changed,
                    "personal_new": personal[:200],
                }
            )
            if sleep_sec > 0 and i + 1 < len(pairs):
                time.sleep(sleep_sec)

    return {
        "total": len(pairs),
        "ok": ok,
        "fail": fail,
        "skip": skip,
        "changed": changed,
        "apply": apply,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="O99 regen personal reply_draft (L3)")
    parser.add_argument("--profile", default="site", choices=("site", "legacy"))
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--lead-ids", default="", help="comma-separated lead ids (bench L3)")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--force",
        action="store_true",
        help="regen even if smell/similar check passes (bench refresh)",
    )
    parser.add_argument("--sleep", type=float, default=1.0)
    parser.add_argument("--since", default="2026-06-01")
    parser.add_argument(
        "--json-out",
        type=Path,
        default=_ROOT / "data" / "regen_personal_reply_drafts.json",
    )
    args = parser.parse_args()
    apply_profile_argv(["--profile", args.profile])
    load_radar_env()
    cfg = load_config()

    if not cfg.ai_active:
        print("FAIL: AI inactive")
        return 1

    since = _parse_judge_since(args.since.strip()) if args.since.strip() else None
    src_sql, src_params = public_feed_source_sql()
    lead_ids = [int(x.strip()) for x in args.lead_ids.split(",") if x.strip().isdigit()]

    with psycopg.connect(cfg.database_url) as conn:
        if lead_ids:
            from preprod_ai_prod_audit import _fetch_leads_by_ids

            pairs = []
            for lead in _fetch_leads_by_ids(conn, lead_ids):
                shared = (lead.get("reply_draft") or "").strip()
                if len(shared) < 30:
                    continue
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT user_id::text, reply_draft
                        FROM user_lead_replies
                        WHERE lead_id = %s AND deleted_at IS NULL
                        ORDER BY created_at DESC
                        LIMIT 1
                        """,
                        (int(lead["lead_id"]),),
                    )
                    row = cur.fetchone()
                if not row:
                    continue
                pairs.append(
                    {
                        "user_id": str(row[0]),
                        "lead_id": int(lead["lead_id"]),
                        "shared": shared,
                        "personal_old": (row[1] or "").strip(),
                    }
                )
        else:
            pairs = fetch_personal_regen_pairs(
                conn,
                limit=max(1, args.limit),
                src_sql=src_sql,
                src_params=src_params,
                since=since,
            )

    if not pairs:
        print("No user_lead_replies pairs to regen")
        return 1

    print(f"O99 regen L3: {len(pairs)} pairs · {'APPLY' if args.apply else 'DRY-RUN'}")
    summary = run_regen_personal(
        cfg,
        pairs,
        apply=bool(args.apply),
        sleep_sec=max(0.0, args.sleep),
        force=bool(args.force),
    )
    summary["generated_at"] = datetime.now(timezone.utc).isoformat()

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"done: ok={summary['ok']} fail={summary['fail']} skip={summary['skip']} "
        f"changed={summary['changed']} -> {args.json_out}"
    )
    return 0 if summary["fail"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
