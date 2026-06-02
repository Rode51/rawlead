"""O72e-4/5 — QA prompt loop: regen → judge → (optional) LLM patch → deploy.

O72e-5 Plan A→B:
  Phase A ($0): unittest + bench_audit.py
  Phase B quick (~$0.2–0.5): --quick-test (bench 5 regen+judge, no patch)
  Phase B final (~$3–6): --full (regen 50 + judge 40+40, no patch)

Usage (owner):
  .venv\\Scripts\\python.exe scripts\\qa_prompt_loop.py --profile site --quick-test --skip-deploy
  .venv\\Scripts\\python.exe scripts\\qa_prompt_loop.py --profile site --full --skip-deploy
  .venv\\Scripts\\python.exe scripts\\qa_prompt_loop.py --profile site --apply --llm-edit-prompt

Gate (exit 0): L2 combined ≥4.0 · send_as_is ≥50% · L1 l1_usable ≥70%
Logs: data/qa_prompt_loop_<ts>.json · data/qa_prompt_loop_<ts>.md
Patches: data/qa_prompt_patches/iter_<N>.md

LLM editor: google/gemini-2.5-flash (не Sonnet на L1 ingest).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
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
    _extract_json_object,
    _openrouter_chat,
    analyze_lead_tools,
    analyze_lite,
    resolve_l1_primary_category,
    sanitize_l1_category,
)
from config import Config, apply_profile_argv, load_config, load_radar_env
from pg_storage import neon_ai_verdict
from public_feed import public_feed_source_sql

from preprod_ai_prod_audit import (  # noqa: E402
    _JUDGE_L1_USABLE_MIN,
    _JUDGE_L2_COMBINED_MIN,
    _JUDGE_L2_SEND_MIN,
    _O72E_JUDGE_SINCE_DEFAULT,
    _fetch_empty_l1,
    _fetch_leads_by_ids,
    fetch_fresh_l1_gate_leads,
    _filter_fresh_for_judge,
    _judge_l1_summary,
    _judge_l2_summary,
    _parse_judge_since,
    _run_judge_l1,
    _run_judge_l2,
    _stratified_sample,
    build_sample_and_audit,
)
from regen_shared_reply_drafts import fetch_regen_candidates, run_regen  # noqa: E402

QA_LOOP_MAX = 5
REGEN_LIMIT = 50
JUDGE_L2_LIMIT = 40
JUDGE_L1_LIMIT = 40
MAX_PATCH_GROWTH = 800
LLM_EDITOR_MODEL = "google/gemini-2.5-flash"
AI_ANALYZE_PATH = _ROOT / "src" / "ai_analyze.py"
DEPLOY_SCRIPT = _ROOT / "scripts" / "deploy-o79-o72e-vps.py"
BENCH_FIXTURE = _ROOT / "tests" / "fixtures" / "o72e_bench_leads.json"
QUICK_TEST_LIMIT = 5

PATCHABLE_BLOCKS: dict[str, re.Pattern[str]] = {
    "_LITE_SYSTEM_HEAD": re.compile(
        r'(_LITE_SYSTEM_HEAD = """)(.*?)("""\s*\n)',
        re.DOTALL,
    ),
    "_SHARED_REPLY_CORE": re.compile(
        r'(_SHARED_REPLY_CORE = """)(.*?)("""\s*\n)',
        re.DOTALL,
    ),
    "_TOOLS_ONLY_SYSTEM": re.compile(
        r'(_TOOLS_ONLY_SYSTEM = """)(.*?)("""\s*\n)',
        re.DOTALL,
    ),
}

_LLM_EDITOR_SYSTEM = """Ты — редактор system-промптов RawLead (L1/L2). Получишь текущий блок и top fix от LLM-judge.

Верни один JSON без markdown:
block — имя блока (как во входе)
content — **полный новый текст** блока (без обёртки triple-quotes)
rationale — 1–2 предложения на русском

Правила:
- Максимум +800 символов к текущему блоку; не раздувай.
- Сохрани JSON-формат выхода модели (поля feed_visible/task_summary/… или reply_draft/tools_required).
- **Запрещено** в shared/cabinet reply: цена, срок, бюджет, «от X ₽» в reply_draft.
- **Запрещено** упоминать Cursor, Gemini, ChatGPT, нейросеть, промпт, RawLead stack (neon, telethon).
- Не ослабляй запреты «без срока/цены» и «ЗАПРЕЩЕНО: … Gemini».
- Усиливай конкретику из ТЗ (2–3 нишевых термина), send_as_is — главная цель L2.
- L1: dev/design/marketing/text, не выдумывать бюджет, email-рассылки → marketing.
- Не трогай _PREMIUM_SPLIT — его нет во входе; правь только переданный блок."""

_REQUIRED_SHARED_BANS = (
    "без срока",
    "Gemini",
    "Cursor",
    "ЗАПРЕЩЕНО",
)

_FORBIDDEN_PROMPT_ADDITIONS = (
    re.compile(r"ценов(?:ое|ые)\s+предложени", re.I),
    re.compile(r"оценк[ау]\s+срок", re.I),
    re.compile(r"бюджет.*reply_draft", re.I),
    re.compile(r"reply_draft.*(?:цена|бюджет|срок)", re.I),
    re.compile(r"добав(?:ь|ить)\s+.*(?:цен|бюджет|срок)", re.I),
)

_O72E3_UNIT_TESTS = (
    "tests.test_preprod_ai_prod_audit.TestPreprodAiProdAudit.test_o72e3_worst_term_groups_defined",
    "tests.test_preprod_ai_prod_audit.TestPreprodAiProdAudit.test_o72e3_worst_good_drafts_pass_term_gate",
    "tests.test_preprod_ai_prod_audit.TestPreprodAiProdAudit.test_o72e3_worst_bad_drafts_fail_term_gate",
)


def _ts_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def read_block(path: Path, block_name: str) -> str:
    text = path.read_text(encoding="utf-8")
    pat = PATCHABLE_BLOCKS.get(block_name)
    if not pat:
        raise ValueError(f"unknown block {block_name}")
    m = pat.search(text)
    if not m:
        raise ValueError(f"block {block_name} not found in {path}")
    return m.group(2)


def write_block(path: Path, block_name: str, new_content: str) -> str:
    text = path.read_text(encoding="utf-8")
    pat = PATCHABLE_BLOCKS[block_name]
    m = pat.search(text)
    if not m:
        raise ValueError(f"block {block_name} not found")
    old = m.group(2)
    updated = pat.sub(lambda mo: mo.group(1) + new_content + mo.group(3), text, count=1)
    if updated == text:
        raise ValueError(f"block {block_name} replace failed")
    path.write_text(updated, encoding="utf-8")
    return old


def _gate_pass(l2: dict[str, Any], l1: dict[str, Any]) -> bool:
    return (
        l2.get("avg_combined_3", 0) >= _JUDGE_L2_COMBINED_MIN
        and l2.get("send_as_is_pct", 0) >= _JUDGE_L2_SEND_MIN * 100
        and l1.get("l1_usable_pct", 0) >= _JUDGE_L1_USABLE_MIN * 100
    )


def _pick_patch_block(l2: dict[str, Any], l1: dict[str, Any]) -> str:
    l1_fail = l1.get("l1_usable_pct", 0) < _JUDGE_L1_USABLE_MIN * 100
    l2_fail = (
        l2.get("avg_combined_3", 0) < _JUDGE_L2_COMBINED_MIN
        or l2.get("send_as_is_pct", 0) < _JUDGE_L2_SEND_MIN * 100
    )
    if l1_fail and not l2_fail:
        return "_LITE_SYSTEM_HEAD"
    if l2_fail and not l1_fail:
        return "_SHARED_REPLY_CORE"
    if l1_fail and l2_fail:
        # alternate by worse relative gap
        l1_gap = _JUDGE_L1_USABLE_MIN * 100 - l1.get("l1_usable_pct", 0)
        send_gap = _JUDGE_L2_SEND_MIN * 100 - l2.get("send_as_is_pct", 0)
        comb_gap = (_JUDGE_L2_COMBINED_MIN - l2.get("avg_combined_3", 0)) * 20
        if l1_gap >= max(send_gap, comb_gap):
            return "_LITE_SYSTEM_HEAD"
        return "_SHARED_REPLY_CORE"
    return "_SHARED_REPLY_CORE"


def _top_fixes(l2: dict[str, Any], l1: dict[str, Any], block: str) -> list[str]:
    if block == "_LITE_SYSTEM_HEAD":
        return list(l1.get("l1_prompt_recommendations", [])[:5])
    if block == "_TOOLS_ONLY_SYSTEM":
        return list(l2.get("prompt_recommendations", [])[:5])
    return list(l2.get("prompt_recommendations", [])[:5])


def _validate_patch(block: str, old: str, new: str) -> list[str]:
    errs: list[str] = []
    if len(new) - len(old) > MAX_PATCH_GROWTH:
        errs.append(f"growth {len(new) - len(old)} > {MAX_PATCH_GROWTH}")
    if block in ("_SHARED_REPLY_CORE",):
        for req in _REQUIRED_SHARED_BANS:
            if req not in new:
                errs.append(f"missing required ban fragment: {req!r}")
        for pat in _FORBIDDEN_PROMPT_ADDITIONS:
            if pat.search(new):
                errs.append(f"forbidden prompt pattern: {pat.pattern}")
    if re.search(r"\b(?:используй|применяй)\s+cursor\b", new, re.I):
        errs.append("encourages Cursor in prompt")
    return errs


def _run_unittest_guardrails() -> tuple[bool, str]:
    cmds = [
        [_ROOT / ".venv" / "Scripts" / "python.exe", "-m", "unittest", *_O72E3_UNIT_TESTS],
        [_ROOT / ".venv" / "Scripts" / "python.exe", "-m", "unittest", "tests.test_preprod_ai_prod_audit"],
    ]
    py = sys.executable
    outputs: list[str] = []
    for cmd in cmds:
        run_cmd = [str(c) if not isinstance(c, Path) else str(c) for c in cmd]
        if not Path(run_cmd[0]).exists():
            run_cmd[0] = py
        proc = subprocess.run(
            run_cmd,
            cwd=_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        outputs.append(proc.stdout + proc.stderr)
        if proc.returncode != 0:
            return False, "\n".join(outputs)[-4000:]
    return True, "ok"


def _llm_edit_block(
    cfg: Config,
    *,
    block_name: str,
    current: str,
    fixes: list[str],
    metrics: dict[str, Any],
) -> tuple[str, str]:
    user = (
        f"block: {block_name}\n\n"
        f"Текущие метрики judge:\n{json.dumps(metrics, ensure_ascii=False, indent=2)}\n\n"
        "Top fix от judge:\n"
        + "\n".join(f"{i + 1}. {f}" for i, f in enumerate(fixes))
        + f"\n\nТекущий блок ({len(current)} симв.):\n---\n{current}\n---\n"
    )
    raw = _openrouter_chat(
        cfg,
        model=LLM_EDITOR_MODEL,
        system=_LLM_EDITOR_SYSTEM,
        user=user,
        timeout_sec=90.0,
        json_mode=True,
    )
    data = _extract_json_object(raw or "")
    content = str(data.get("content", "")).strip()
    rationale = str(data.get("rationale", "")).strip()
    if not content:
        raise AiAnalyzeError("LLM editor returned empty content")
    if str(data.get("block", block_name)).strip() not in (block_name, ""):
        raise AiAnalyzeError(f"LLM editor changed block name to {data.get('block')!r}")
    return content, rationale


def _deploy_vps() -> tuple[bool, str]:
    if not DEPLOY_SCRIPT.is_file():
        return False, f"missing {DEPLOY_SCRIPT}"
    proc = subprocess.run(
        [sys.executable, str(DEPLOY_SCRIPT)],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, out[-3000:]


def _load_bench_anchor_ids() -> list[int]:
    if not BENCH_FIXTURE.is_file():
        raise SystemExit(f"FAIL: missing bench fixture {BENCH_FIXTURE} — run export_o72e_bench_leads.py")
    doc = json.loads(BENCH_FIXTURE.read_text(encoding="utf-8"))
    ids = [int(x) for x in doc.get("anchor_ids") or []]
    if len(ids) < QUICK_TEST_LIMIT:
        ids = sorted({int(l["lead_id"]) for l in doc.get("leads") or [] if l.get("bench_anchor")})
    return ids[:QUICK_TEST_LIMIT]


def _run_regen_ids(cfg: Config, lead_ids: list[int], *, apply: bool) -> dict[str, Any]:
    with psycopg.connect(cfg.database_url) as conn:
        leads = _fetch_leads_by_ids(conn, lead_ids)
    if not leads:
        raise SystemExit(f"No regen candidates for ids {lead_ids}")
    print(f"Regen {len(leads)} bench leads (apply={apply}) …", flush=True)
    return run_regen(cfg, leads, apply=apply, sleep_sec=1.5, reject_cliche=True)


def _run_judge_on_leads(
    cfg: Config,
    leads: list[dict],
    *,
    l2_limit: int,
    l1_limit: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    results, auto_summary = build_sample_and_audit(leads)
    print(f"Judge L2 limit={l2_limit} L1 limit={l1_limit} on {len(results)} leads …", flush=True)
    judge_l2_rows = _run_judge_l2(cfg, results, limit=l2_limit)
    judge_l1_rows = _run_judge_l1(cfg, results, limit=l1_limit)
    l2 = _judge_l2_summary(judge_l2_rows)
    l1 = _judge_l1_summary(judge_l1_rows)
    return l2, l1, auto_summary


def _run_regen(cfg: Config, *, judge_since: datetime, apply: bool) -> dict[str, Any]:
    src_sql, src_params = public_feed_source_sql()
    with psycopg.connect(cfg.database_url) as conn:
        leads = fetch_regen_candidates(
            conn,
            limit=REGEN_LIMIT,
            src_sql=src_sql,
            src_params=src_params,
            since=judge_since,
        )
    if not leads:
        raise SystemExit(
            f"No regen candidates since {judge_since.date()} "
            "(нужны is_visible + task_summary + reply_draft; см. FOR_YOU § O72e gate)"
        )
    print(f"Regen {len(leads)} leads (apply={apply}) …", flush=True)
    return run_regen(cfg, leads, apply=apply, sleep_sec=1.5, reject_cliche=True)


def _run_judge(
    cfg: Config, *, judge_since: datetime
) -> tuple[dict[str, Any], dict[str, Any], list[dict], list[dict], dict[str, Any]]:
    src_sql, src_params = public_feed_source_sql()
    since_sql = " AND created_at >= %s"
    since_params = [judge_since]
    with psycopg.connect(cfg.database_url) as conn:
        main_sample = _stratified_sample(
            conn,
            n=150,
            src_sql=src_sql,
            src_params=src_params,
            since_sql=since_sql,
            since_params=since_params,
        )
        empty_l1 = _fetch_empty_l1(
            conn,
            limit=25,
            src_sql=src_sql,
            src_params=src_params,
            since_sql=since_sql,
            since_params=since_params,
        )
    seen: set[int] = set()
    merged: list[dict] = []
    for batch in (empty_l1, main_sample):
        for lead in batch:
            if lead["lead_id"] not in seen:
                seen.add(lead["lead_id"])
                merged.append(lead)

    results, auto_summary = build_sample_and_audit(merged)
    fresh = _filter_fresh_for_judge(results, since=judge_since)
    print(f"Judge L2 limit={JUDGE_L2_LIMIT} L1 limit={JUDGE_L1_LIMIT} on {len(fresh)} fresh …", flush=True)
    judge_l2_rows = _run_judge_l2(cfg, fresh, limit=JUDGE_L2_LIMIT)
    judge_l1_rows = _run_judge_l1(cfg, fresh, limit=JUDGE_L1_LIMIT)
    l2 = _judge_l2_summary(judge_l2_rows)
    l1 = _judge_l1_summary(judge_l1_rows)
    return l2, l1, judge_l2_rows, judge_l1_rows, auto_summary


def _render_md(run: dict[str, Any]) -> str:
    lines = [
        "# O72e-4 QA prompt loop",
        "",
        f"- **Time:** {run['generated_at']}",
        f"- **Profile:** {run.get('profile')}",
        f"- **Mode:** {run.get('mode')}",
        f"- **Gate:** {'✅ PASS' if run.get('gate_pass') else '❌ FAIL'}",
        "",
    ]
    for it in run.get("iterations", []):
        lines.extend(
            [
                f"## Iteration {it['iteration']}",
                "",
                f"- combined: **{it['l2'].get('avg_combined_3')}** · "
                f"send: **{it['l2'].get('send_as_is_pct')}%** · "
                f"L1 usable: **{it['l1'].get('l1_usable_pct')}%** · "
                f"gate: {'PASS' if it.get('gate_pass') else 'FAIL'}",
            ]
        )
        if it.get("patch"):
            p = it["patch"]
            lines.append(
                f"- patch: `{p.get('block')}` +{p.get('growth', 0)} chars → "
                f"`{p.get('patch_file', '—')}`"
            )
        lines.append("")
    return "\n".join(lines)


def _save_patch_md(
    path: Path,
    *,
    iteration: int,
    block: str,
    old: str,
    new: str,
    fixes: list[str],
    rationale: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = [
        f"# QA prompt patch iter {iteration}",
        "",
        f"- **Block:** `{block}`",
        f"- **Growth:** +{len(new) - len(old)} chars ({len(old)} → {len(new)})",
        "",
        "## Judge top fixes",
        "",
    ]
    for i, f in enumerate(fixes, 1):
        body.append(f"{i}. {f}")
    body.extend(["", "## Rationale", "", rationale or "—", "", "## Diff summary", ""])
    if old != new:
        body.append("```diff")
        body.append(f"- (old {len(old)} chars)")
        body.append(f"+ (new {len(new)} chars)")
        body.append("```")
    body.extend(["", "## New block", "", "```", new, "```", ""])
    path.write_text("\n".join(body), encoding="utf-8")


def _one_iteration(
    cfg: Config,
    *,
    iteration: int,
    judge_since: datetime,
    apply_regen: bool,
    llm_edit: bool,
    deploy: bool,
) -> dict[str, Any]:
    t0 = time.time()
    regen_summary = _run_regen(cfg, judge_since=judge_since, apply=apply_regen)
    l2, l1, _, _, auto_summary = _run_judge(cfg, judge_since=judge_since)
    gate = _gate_pass(l2, l1)
    entry: dict[str, Any] = {
        "iteration": iteration,
        "duration_sec": round(time.time() - t0, 1),
        "regen": {
            "ok": regen_summary.get("ok"),
            "fail": regen_summary.get("fail"),
            "changed": regen_summary.get("changed"),
        },
        "l2": l2,
        "l1": l1,
        "auto_audit": {
            "draft_only_pass_pct": auto_summary.get("draft_only_pass_pct"),
            "tools_pass_pct": auto_summary.get("tools_pass_pct"),
        },
        "gate_pass": gate,
    }
    print(
        f"Iter {iteration}: combined={l2.get('avg_combined_3')} "
        f"send={l2.get('send_as_is_pct')}% "
        f"L1 usable={l1.get('l1_usable_pct')}% "
        f"({'PASS' if gate else 'FAIL'})",
        flush=True,
    )

    if gate or not llm_edit:
        return entry

    block = _pick_patch_block(l2, l1)
    fixes = _top_fixes(l2, l1, block)
    if not fixes:
        print(f"Iter {iteration}: no judge fixes for {block} — skip patch", flush=True)
        entry["patch"] = {"skipped": True, "reason": "no_fixes"}
        return entry

    current = read_block(AI_ANALYZE_PATH, block)
    metrics = {
        "l2_combined": l2.get("avg_combined_3"),
        "send_as_is_pct": l2.get("send_as_is_pct"),
        "l1_usable_pct": l1.get("l1_usable_pct"),
    }
    try:
        new_content, rationale = _llm_edit_block(
            cfg, block_name=block, current=current, fixes=fixes, metrics=metrics
        )
    except (AiAnalyzeError, Exception) as exc:  # noqa: BLE001
        entry["patch"] = {"error": str(exc)[:300]}
        print(f"Iter {iteration}: LLM edit failed: {exc}", flush=True)
        return entry

    val_errs = _validate_patch(block, current, new_content)
    if val_errs:
        entry["patch"] = {"error": "; ".join(val_errs), "block": block}
        print(f"Iter {iteration}: patch validation failed: {val_errs}", flush=True)
        return entry

    patch_path = _ROOT / "data" / "qa_prompt_patches" / f"iter_{iteration}.md"
    _save_patch_md(
        patch_path,
        iteration=iteration,
        block=block,
        old=current,
        new=new_content,
        fixes=fixes,
        rationale=rationale,
    )

    old_written = write_block(AI_ANALYZE_PATH, block, new_content)
    ok_tests, test_out = _run_unittest_guardrails()
    if not ok_tests:
        write_block(AI_ANALYZE_PATH, block, old_written)
        entry["patch"] = {
            "block": block,
            "reverted": True,
            "reason": "unittest_guardrail",
            "test_output": test_out[-1500:],
            "patch_file": str(patch_path.relative_to(_ROOT)),
        }
        print(f"Iter {iteration}: guardrails FAIL — reverted {block}", flush=True)
        return entry

    entry["patch"] = {
        "block": block,
        "growth": len(new_content) - len(old_written),
        "patch_file": str(patch_path.relative_to(_ROOT)),
        "rationale": rationale[:300],
    }
    print(f"Iter {iteration}: patched {block} (+{entry['patch']['growth']} chars)", flush=True)

    if deploy:
        dep_ok, dep_out = _deploy_vps()
        entry["deploy"] = {"ok": dep_ok, "log_tail": dep_out[-800:]}
        if not dep_ok:
            print(f"Iter {iteration}: VPS deploy failed — see log", flush=True)
        else:
            print(f"Iter {iteration}: VPS deploy OK", flush=True)

    return entry


def _replay_l1_tools(cfg: Config, leads: list[dict[str, Any]]) -> dict[str, Any]:
    """O72e-8: replay L1 + tools on sample before regen+judge."""
    ok_l1 = fail_l1 = ok_tools = fail_tools = 0
    details: list[dict[str, Any]] = []
    with psycopg.connect(cfg.database_url) as conn:
        for lead in leads:
            lead_id = int(lead["lead_id"])
            title = lead.get("title") or ""
            body = lead.get("body") or ""
            snippet = body.strip() or title
            budget = lead.get("budget_text") or ""
            url = lead.get("url") or ""
            errors: list[str] = []
            lite = analyze_lite(
                cfg,
                title=title,
                budget_text=budget,
                snippet=snippet,
                url=url,
                errors=errors,
                log_prefix=f"replay-l1:{lead_id}:",
            )
            entry: dict[str, Any] = {"lead_id": lead_id}
            if lite is None:
                fail_l1 += 1
                entry["l1"] = "fail"
                entry["error"] = "; ".join(errors)[:200]
                details.append(entry)
                continue
            ok_l1 += 1
            category = resolve_l1_primary_category(
                lite.primary_category,
                lite.lead_tags,
                title=title,
                snippet=snippet,
            )
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE leads
                    SET ai_verdict = %s,
                        task_summary = %s,
                        lead_tags = %s::jsonb,
                        ai_reasons = %s::jsonb,
                        category = %s
                    WHERE id = %s
                    """,
                    (
                        neon_ai_verdict(lite),
                        lite.task_summary,
                        json.dumps(list(lite.lead_tags), ensure_ascii=False),
                        json.dumps(list(lite.ai_reasons), ensure_ascii=False),
                        category,
                        lead_id,
                    ),
                )
            conn.commit()
            entry["l1"] = "ok"
            entry["feed_visible"] = lite.feed_visible
            entry["category"] = category
            entry["lead_tags"] = list(lite.lead_tags)

            tools = analyze_lead_tools(
                cfg,
                title=title,
                budget_text=budget,
                description=body,
                lite=lite,
                errors=errors,
                log_prefix=f"replay-tools:{lead_id}:",
            )
            if tools:
                ok_tools += 1
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE leads SET tools_required = %s::jsonb WHERE id = %s",
                        (json.dumps(list(tools), ensure_ascii=False), lead_id),
                    )
                conn.commit()
                entry["tools"] = list(tools)
            else:
                fail_tools += 1
                entry["tools"] = "fail"
            details.append(entry)
            time.sleep(1.0)
    return {
        "l1_ok": ok_l1,
        "l1_fail": fail_l1,
        "tools_ok": ok_tools,
        "tools_fail": fail_tools,
        "details": details,
    }


def _replay_l1_tools_bench(cfg: Config, leads: list[dict[str, Any]]) -> dict[str, Any]:
    return _replay_l1_tools(cfg, leads)


def _one_shot_regen_judge(
    cfg: Config,
    *,
    mode: str,
    judge_since: datetime,
    bench_ids: list[int] | None = None,
) -> dict[str, Any]:
    t0 = time.time()
    if bench_ids:
        with psycopg.connect(cfg.database_url) as conn:
            judged_leads = _fetch_leads_by_ids(conn, bench_ids)
        replay_summary = _replay_l1_tools_bench(cfg, judged_leads)
        print(
            f"Replay L1+tools: l1={replay_summary['l1_ok']}/{len(judged_leads)} "
            f"tools={replay_summary['tools_ok']}/{len(judged_leads)}",
            flush=True,
        )
        regen_summary = _run_regen_ids(cfg, bench_ids, apply=True)
        with psycopg.connect(cfg.database_url) as conn:
            judged_leads = _fetch_leads_by_ids(conn, bench_ids)
        l2_limit = l1_limit = len(judged_leads)
    else:
        src_sql, src_params = public_feed_source_sql()
        with psycopg.connect(cfg.database_url) as conn:
            regen_candidates = fetch_regen_candidates(
                conn,
                limit=REGEN_LIMIT,
                src_sql=src_sql,
                src_params=src_params,
                since=judge_since,
            )
            if not regen_candidates:
                regen_candidates = fetch_fresh_l1_gate_leads(
                    conn,
                    limit=REGEN_LIMIT,
                    src_sql=src_sql,
                    src_params=src_params,
                    since=judge_since,
                )
                if regen_candidates:
                    print(
                        f"Fresh L1 pool {len(regen_candidates)} "
                        f"(без reply_draft — regen создаст draft перед judge)",
                        flush=True,
                    )
        if not regen_candidates:
            raise SystemExit(
                f"No gate leads since {judge_since.date()} "
                "(нужны visible + L1 task_summary; проверь радар VPS)"
            )
        replay_summary = _replay_l1_tools(cfg, regen_candidates)
        print(
            f"Replay L1+tools: l1={replay_summary['l1_ok']}/{len(regen_candidates)} "
            f"tools={replay_summary['tools_ok']}/{len(regen_candidates)}",
            flush=True,
        )
        lead_ids = [int(l["lead_id"]) for l in regen_candidates]
        with psycopg.connect(cfg.database_url) as conn:
            regen_candidates = _fetch_leads_by_ids(conn, lead_ids)
        regen_summary = run_regen(cfg, regen_candidates, apply=True, sleep_sec=1.5, reject_cliche=True)
        with psycopg.connect(cfg.database_url) as conn:
            judged_leads = _fetch_leads_by_ids(conn, lead_ids)
        l2, l1, auto_summary = _run_judge_on_leads(
            cfg,
            judged_leads,
            l2_limit=min(JUDGE_L2_LIMIT, len(judged_leads)),
            l1_limit=min(JUDGE_L1_LIMIT, len(judged_leads)),
        )
        gate = _gate_pass(l2, l1)
        return {
            "iteration": 1,
            "duration_sec": round(time.time() - t0, 1),
            "replay_l1_tools": replay_summary,
            "regen": regen_summary,
            "l2": l2,
            "l1": l1,
            "auto_audit": {
                "draft_only_pass_pct": auto_summary.get("draft_only_pass_pct"),
                "tools_pass_pct": auto_summary.get("tools_pass_pct"),
            },
            "gate_pass": gate,
            "mode": mode,
        }

    l2, l1, auto_summary = _run_judge_on_leads(
        cfg, judged_leads, l2_limit=l2_limit, l1_limit=l1_limit
    )
    gate = _gate_pass(l2, l1)
    return {
        "iteration": 1,
        "duration_sec": round(time.time() - t0, 1),
        "replay_l1_tools": replay_summary if bench_ids else None,
        "regen": regen_summary,
        "bench_ids": bench_ids,
        "l2": l2,
        "l1": l1,
        "auto_audit": {
            "draft_only_pass_pct": auto_summary.get("draft_only_pass_pct"),
            "tools_pass_pct": auto_summary.get("tools_pass_pct"),
        },
        "gate_pass": gate,
        "mode": mode,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="O72e-4/5 QA prompt loop")
    parser.add_argument("--profile", default="site", choices=("site", "legacy"))
    parser.add_argument("--dry-run", action="store_true", help="one iteration: regen+judge, no patch")
    parser.add_argument(
        "--full",
        action="store_true",
        help="O72e-5 phase B final: regen 50 + judge 40+40, no LLM patch",
    )
    parser.add_argument(
        "--quick-test",
        action="store_true",
        help="O72e-5 phase B quick: regen+judge bench 5 anchors only, no LLM patch",
    )
    parser.add_argument("--apply", action="store_true", help="full loop with patch on FAIL")
    parser.add_argument(
        "--llm-edit-prompt",
        action="store_true",
        help="on FAIL: LLM patch prompt blocks (requires --apply; default off)",
    )
    parser.add_argument(
        "--judge-since",
        default=_O72E_JUDGE_SINCE_DEFAULT,
        help="only leads ingested on/after date",
    )
    parser.add_argument("--max-iter", type=int, default=QA_LOOP_MAX)
    parser.add_argument(
        "--skip-deploy",
        action="store_true",
        help="do not run VPS deploy after patch (debug only)",
    )
    args = parser.parse_args()

    mode_flags = sum(bool(x) for x in (args.dry_run, args.full, args.quick_test, args.apply))
    if mode_flags != 1:
        print("FAIL: specify exactly one of --dry-run, --full, --quick-test, --apply", file=sys.stderr)
        return 2
    if args.llm_edit_prompt and not args.apply:
        print("FAIL: --llm-edit-prompt requires --apply", file=sys.stderr)
        return 2
    if args.llm_edit_prompt and (args.full or args.quick_test):
        print("FAIL: --llm-edit-prompt incompatible with --full / --quick-test", file=sys.stderr)
        return 2

    apply_profile_argv(["--profile", args.profile])
    load_radar_env()
    cfg = load_config()
    if not cfg.database_url.strip():
        print("FAIL: DATABASE_URL empty", file=sys.stderr)
        return 2
    if not cfg.ai_active:
        print("FAIL: AI inactive (OPENROUTER_API_KEY?)", file=sys.stderr)
        return 2

    judge_since = _parse_judge_since(args.judge_since)

    if args.quick_test or args.full:
        mode = "quick-test" if args.quick_test else "full"
        bench_ids = _load_bench_anchor_ids() if args.quick_test else None
        print(
            f"O72e-5 QA · mode={mode} · judge_since={judge_since.date()} · "
            f"{'bench=' + ','.join(map(str, bench_ids)) if bench_ids else f'regen={REGEN_LIMIT}'}",
            flush=True,
        )
        entry = _one_shot_regen_judge(
            cfg, mode=mode, judge_since=judge_since, bench_ids=bench_ids
        )
        gate_pass = bool(entry.get("gate_pass"))
        run_doc: dict[str, Any] = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "profile": args.profile,
            "mode": mode,
            "judge_since": judge_since.date().isoformat(),
            "iterations": [entry],
            "gate_pass": gate_pass,
            "iterations_run": 1,
        }
        slug = _ts_slug()
        json_path = _ROOT / "data" / f"qa_prompt_loop_{slug}.json"
        md_path = _ROOT / "data" / f"qa_prompt_loop_{slug}.md"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(run_doc, ensure_ascii=False, indent=2), encoding="utf-8")
        md_path.write_text(_render_md(run_doc), encoding="utf-8")
        print(f"Log → {json_path}")
        l2, l1 = entry["l2"], entry["l1"]
        print(
            f"combined={l2.get('avg_combined_3')} send={l2.get('send_as_is_pct')}% "
            f"L1 usable={l1.get('l1_usable_pct')}% ({'PASS' if gate_pass else 'FAIL'})"
        )
        return 0 if gate_pass else 1

    max_iter = 1 if args.dry_run else min(max(1, args.max_iter), QA_LOOP_MAX)
    llm_edit = bool(args.apply and args.llm_edit_prompt)
    deploy = llm_edit and not args.skip_deploy

    mode = "dry-run" if args.dry_run else ("apply+llm" if llm_edit else "apply")
    print(
        f"O72e-4 QA loop · mode={mode} · max_iter={max_iter} · "
        f"judge_since={judge_since.date()} · editor={LLM_EDITOR_MODEL}",
        flush=True,
    )
    if deploy:
        print("Deploy: after each patch → VPS (deploy-o79-o72e-vps.py)", flush=True)

    run_doc: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": args.profile,
        "mode": mode,
        "judge_since": judge_since.date().isoformat(),
        "regen_limit": REGEN_LIMIT,
        "judge_l2_limit": JUDGE_L2_LIMIT,
        "judge_l1_limit": JUDGE_L1_LIMIT,
        "llm_editor_model": LLM_EDITOR_MODEL,
        "max_iter": max_iter,
        "iterations": [],
    }

    gate_pass = False
    for i in range(1, max_iter + 1):
        try:
            entry = _one_iteration(
                cfg,
                iteration=i,
                judge_since=judge_since,
                apply_regen=True,
                llm_edit=llm_edit,
                deploy=deploy,
            )
        except KeyboardInterrupt:
            print("\nStopped by owner (Ctrl+C)", flush=True)
            run_doc["stopped"] = "keyboard_interrupt"
            break
        run_doc["iterations"].append(entry)
        gate_pass = bool(entry.get("gate_pass"))
        if gate_pass:
            break
        if args.dry_run:
            break
        if i >= max_iter:
            print(f"Escalation: {max_iter} iterations without PASS", flush=True)

    run_doc["gate_pass"] = gate_pass
    run_doc["iterations_run"] = len(run_doc["iterations"])

    slug = _ts_slug()
    json_path = _ROOT / "data" / f"qa_prompt_loop_{slug}.json"
    md_path = _ROOT / "data" / f"qa_prompt_loop_{slug}.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(run_doc, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_render_md(run_doc), encoding="utf-8")
    print(f"Log → {json_path}")
    print(f"Md  → {md_path}")

    if gate_pass:
        print("O72e-4 GATE: PASS")
        return 0
    print("O72e-4 GATE: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
