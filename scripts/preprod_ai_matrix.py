"""§ PRE-PROD-STRESS t1: матрица L1/L2 по 4 category → JSON отчёт.

Запуск (site, нужен OpenRouter в .env.site):

  .venv\\Scripts\\python.exe scripts\\preprod_ai_matrix.py --profile site
  .venv\\Scripts\\python.exe scripts\\preprod_ai_matrix.py --profile site --shared-draft
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

from ai_analyze import (
    AiAnalysis,
    AiLiteAnalysis,
    analyze_lite,
    analyze_premium,
    analyze_shared_reply_draft,
)
from config import apply_profile_argv, load_config, load_radar_env
from preprod_fixtures import CATEGORIES, PREPROD_LEAD_FIXTURES, PreprodLeadFixture

_SKILLS_MISMATCH_FIXTURE = PreprodLeadFixture(
    id="skills-mismatch-node",
    category="dev",
    title="Backend Node.js (NestJS) для CS-маркетплейса",
    budget_text="150 000 ₽",
    snippet=(
        "Node.js (NestJS / Express), React frontend. Steam API, P2P-маркет скинов. "
        "PostgreSQL, Redis. REST + WebSocket."
    ),
    url="https://www.fl.ru/projects/skills-mismatch-node/",
)
# VPS Postgres acc1 — см. docs/ops/PREPROD_ACCOUNTS.md (Neon legacy: 895912a1-…)
_PREPROD_TEST_TG_USER_ID = 8233488286
_PREPROD_TEST_USER_ID = "7a83dbd8-ab41-4350-a183-38370d5b5c1c"


def _is_transient_db_error(exc: BaseException) -> bool:
    msg = str(exc).casefold()
    return any(
        token in msg
        for token in (
            "server closed the connection",
            "connection unexpectedly",
            "connection reset",
            "connection refused",
            "could not connect",
            "timeout expired",
        )
    )


def _ensure_preprod_test_user(cur, preferred_user_id: str) -> str:
    """Resolve acc1 on VPS Postgres; upsert if missing (FK user_tags_user_id_fkey)."""
    cur.execute("SELECT id::text FROM users WHERE tg_user_id = %s", (_PREPROD_TEST_TG_USER_ID,))
    row = cur.fetchone()
    if row:
        return str(row[0])

    cur.execute("SELECT id::text FROM users WHERE id = %s::uuid", (preferred_user_id,))
    row = cur.fetchone()
    if row:
        return str(row[0])

    cur.execute(
        """
        INSERT INTO users (id, tg_user_id, tg_username, tg_first_name)
        VALUES (%s::uuid, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        (preferred_user_id, _PREPROD_TEST_TG_USER_ID, "preprod_acc1", "Preprod Acc1"),
    )
    cur.execute("SELECT id::text FROM users WHERE id = %s::uuid", (preferred_user_id,))
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"preprod user upsert failed for {preferred_user_id}")
    return str(row[0])


# O168 g3: ondemand L2 = up to 2×90s OR attempts + outer retry (match_push._analyze_shared_ondemand)
_SKILLS_MISMATCH_MAX_MS = 300_000


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


def _run_fixture_shared_draft(cfg, fixture: PreprodLeadFixture) -> dict:
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

    t1 = time.perf_counter()
    reply_draft = ""
    if lite is not None:
        draft = analyze_shared_reply_draft(
            cfg,
            title=fixture.title,
            budget_text=fixture.budget_text,
            lite=lite,
            tools_required=[],
            errors=errors,
            log_prefix=f"{fixture.id}:",
            timeout_sec=90.0,
        )
        reply_draft = (draft or "").strip()
    shared_ms = int((time.perf_counter() - t1) * 1000)

    task_summary = (lite.task_summary if lite else "") or ""

    return {
        "fixture_id": fixture.id,
        "category": fixture.category,
        "title": fixture.title,
        "lite_ok": lite is not None,
        "shared_draft_ok": bool(reply_draft),
        "lite_ms": lite_ms,
        "shared_draft_ms": shared_ms,
        "task_summary_nonempty": bool(task_summary.strip()),
        "reply_draft_nonempty": bool(reply_draft),
        "errors": errors,
        "lite": _analysis_to_dict(lite),
        "reply_draft": reply_draft or None,
    }


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


def _build_shared_draft_summary(results: list[dict]) -> dict:
    by_cat: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "total": 0,
            "lite_ok": 0,
            "shared_draft_ok": 0,
            "empty_reply_draft": 0,
        }
    )
    for row in results:
        cat = row["category"]
        by_cat[cat]["total"] += 1
        if row["lite_ok"]:
            by_cat[cat]["lite_ok"] += 1
        if row["shared_draft_ok"]:
            by_cat[cat]["shared_draft_ok"] += 1
        if row["lite_ok"] and not row["reply_draft_nonempty"]:
            by_cat[cat]["empty_reply_draft"] += 1

    draft_ok = sum(1 for r in results if r["reply_draft_nonempty"])
    s1_pass = draft_ok >= 11

    return {
        "total": len(results),
        "lite_ok": sum(1 for r in results if r["lite_ok"]),
        "shared_draft_ok": draft_ok,
        "empty_reply_draft": sum(
            1 for r in results if r["lite_ok"] and not r["reply_draft_nonempty"]
        ),
        "by_category": dict(by_cat),
        "s1_pass": s1_pass,
        "mode": "shared_draft",
    }


def _run_skills_mismatch(cfg) -> dict:
    """S1-b / S6-b: Node lead + user tag yii2 — draft по ТЗ, без Yii2/опыт."""
    import os

    import psycopg
    from l3_human_style import reply_ai_smell_reason
    from match_push import generate_and_store_lead_draft

    errors: list[str] = []
    user_id = os.environ.get("PREPROD_TEST_USER_ID", _PREPROD_TEST_USER_ID).strip()
    fx = _SKILLS_MISMATCH_FIXTURE
    db_url = cfg.database_url.strip()
    if not db_url:
        return {
            "scenario": "skills_mismatch",
            "pass": False,
            "error": "DATABASE_URL missing",
            "summary": {"pass": False},
        }

    lead_id: int | None = None
    ext_id = f"skills-mismatch-{int(time.time())}"
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            user_id = _ensure_preprod_test_user(cur, user_id)
            cur.execute("DELETE FROM user_tags WHERE user_id = %s::uuid", (user_id,))
            cur.execute(
                "INSERT INTO user_tags (user_id, tag) VALUES (%s::uuid, %s)",
                (user_id, "yii2"),
            )
            cur.execute(
                """
                INSERT INTO leads (
                    source, external_id, title, body, url, budget_text,
                    lead_tags, tools_required, is_visible, category, task_summary, reply_draft
                )
                VALUES ('fl', %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, TRUE, 'dev', %s, '')
                RETURNING id
                """,
                (
                    ext_id,
                    fx.title,
                    f"{fx.title}\n\n{fx.snippet}",
                    fx.url,
                    fx.budget_text,
                    '["nodejs","nestjs","react"]',
                    '["nodejs","nestjs","postgresql","redis"]',
                    "Node.js backend NestJS и React frontend для маркетплейса.",
                ),
            )
            row = cur.fetchone()
            if not row:
                return {
                    "scenario": "skills_mismatch",
                    "pass": False,
                    "error": "lead insert failed",
                    "summary": {"pass": False},
                }
            lead_id = int(row[0])
        conn.commit()

    t0 = time.perf_counter()
    result = None
    last_exc: Exception | None = None
    for attempt in range(2):
        try:
            result = generate_and_store_lead_draft(
                cfg,
                user_id=user_id,
                lead_id=int(lead_id),
                log_prefix="skills_mismatch:",
                enforce_rate_limit=False,
            )
            break
        except Exception as exc:
            last_exc = exc
            if attempt == 0 and _is_transient_db_error(exc):
                time.sleep(3)
                continue
            return {
                "scenario": "skills_mismatch",
                "pass": False,
                "lead_id": lead_id,
                "error": str(exc),
                "summary": {"pass": False, "errors": [str(exc)]},
            }
    if result is None:
        exc = last_exc or RuntimeError("draft generation failed")
        return {
            "scenario": "skills_mismatch",
            "pass": False,
            "lead_id": lead_id,
            "error": str(exc),
            "summary": {"pass": False, "errors": [str(exc)]},
        }
    total_ms = int((time.perf_counter() - t0) * 1000)

    draft = (result.reply_draft or "").strip()
    lower = draft.casefold()
    bad_stack = any(x in lower for x in ("yii2", "yii 2", "fontlab"))
    smell = reply_ai_smell_reason(draft) if draft else "empty"
    node_in_tz = "node" in lower or "nestjs" in lower
    ok = (
        bool(draft)
        and not bad_stack
        and smell is None
        and node_in_tz
        and total_ms < _SKILLS_MISMATCH_MAX_MS
    )

    return {
        "scenario": "skills_mismatch",
        "pass": ok,
        "lead_id": lead_id,
        "user_id": user_id,
        "user_tags": ["yii2"],
        "reply_draft": draft[:500] if draft else None,
        "timings_ms": {"total": total_ms},
        "checks": {
            "non_empty": bool(draft),
            "no_yii2_fontlab": not bad_stack,
            "no_smell": smell is None,
            "node_from_tz": node_in_tz,
            "under_budget": total_ms < _SKILLS_MISMATCH_MAX_MS,
        },
        "smell": smell,
        "errors": errors,
        "summary": {"pass": ok},
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
        "--shared-draft",
        action="store_true",
        help="O71: analyze_shared_reply_draft (site path, pro model)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_ROOT / "data" / "preprod_ai_report.json",
    )
    parser.add_argument(
        "--scenario",
        default="matrix",
        choices=("matrix", "skills_mismatch"),
        help="matrix = 4×category L1+L2; skills_mismatch = S1-b edge case",
    )
    args = parser.parse_args()
    apply_profile_argv(["--profile", args.profile])

    if args.scenario == "skills_mismatch":
        load_radar_env()
        cfg = load_config()
        if not cfg.ai_active:
            print("AI_ENABLED=0 — skills_mismatch невозможен.", file=sys.stderr)
            return 2
        report = _run_skills_mismatch(cfg)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("pass") else 1

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

    if args.shared_draft:
        results = [_run_fixture_shared_draft(cfg, fx) for fx in fixtures]
        summary = _build_shared_draft_summary(results)
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "profile": args.profile,
            "mode": "shared_draft",
            "models": {
                "lite": cfg.ai_model_summary,
                "shared_draft": cfg.ai_model_shared_draft,
            },
            "summary": summary,
            "results": results,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            f"shared-draft matrix: {summary['lite_ok']}/{summary['total']} L1, "
            f"{summary['shared_draft_ok']}/{summary['total']} draft → {args.output}"
        )
        print(
            f"S1: {'PASS' if summary['s1_pass'] else 'FAIL'} "
            f"(empty reply_draft: {summary['empty_reply_draft']}, need ≥11/12)"
        )
        return 0 if summary["s1_pass"] else 1

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
