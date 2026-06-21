"""§ O72: prod sample audit — reply_draft, tools_required, L1 task_summary.

Фаза 1 (auto-metrics, без OpenRouter):
  .venv\\Scripts\\python.exe scripts\\preprod_ai_prod_audit.py --profile site
  .venv\\Scripts\\python.exe scripts\\preprod_ai_prod_audit.py --profile site --limit 150

Фаза 2 (O72e LLM judge L1+L2+L3, OPENROUTER_MODEL_JUDGE — только свежие лиды):
  .venv\\Scripts\\python.exe scripts\\preprod_ai_prod_audit.py --profile site --judge --judge-limit 71 --judge-l1 --judge-l1-limit 71
  .venv\\Scripts\\python.exe scripts\\preprod_ai_prod_audit.py --profile site --judge --judge-l1 --judge-l3 --judge-l3-limit 25 --judge-since 2026-06-01
  .venv\\Scripts\\python.exe scripts\\preprod_ai_prod_audit.py --profile site --lead-ids 7051,7019
  O115 TG pilot (10 ids, не смешивать с FL):
  .venv\\Scripts\\python.exe scripts\\preprod_ai_prod_audit.py --profile site --source-like tg:%% --limit 10 --judge --judge-limit 10 --judge-l1 --judge-l1-limit 10
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
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

import psycopg

from ai_analyze import (
    AiAnalyzeError,
    _extract_json_object,
    _openrouter_chat,
    _validate_reply_draft_maybe,
    _validate_reply_draft_take,
    reply_draft_cliche_warn,
    reply_draft_sentence_warn,
)
from config import apply_profile_argv, load_config, load_radar_env
from lead_category import CATEGORIES
from public_feed import public_feed_source_sql
from rank import normalize_tags
from ai_reasons import parse_ai_reasons_raw
from skills_catalog import CANONICAL_TAGS, resolve_canonical_tag
from tools_catalog import (
    is_known_tool,
    normalize_tools_required,
    tools_from_tz_text,
    vendor_lock_tools,
)

_SELECT_COLS = """
    id, source, title, body, url, budget_text,
    ai_score, ai_verdict, lead_tags, ai_reasons, created_at, category,
    task_summary, tools_required, reply_draft
"""

_SKIP_VERDICTS = frozenset({"мимо", "пропустить", "skip"})
_TAKE_VERDICTS = frozenset({"брать", "брат", "take", "ok"})
_MAYBE_VERDICTS = frozenset({"сомнительно", "maybe"})
_O72E_JUDGE_SINCE_DEFAULT = "2026-06-01"
_JUDGE_L2_COMBINED_MIN = 4.0
_JUDGE_L2_SEND_MIN = 0.7
_JUDGE_L1_USABLE_MIN = 0.7
_JUDGE_L1_COMPLEXITY_OK_MIN = 3.0
_JUDGE_L1_COMPLEXITY_OK_PCT_MIN = 0.7
_JUDGE_L3_COMBINED_MIN = 3.8
_JUDGE_L3_SEND_MIN = 0.5
_JUDGE_L3_UNIQUENESS_MIN = 3.0
_JUDGE_L3_FORBIDDEN_LEAK_MAX_PCT = 0.1
_AUDIT_L3_USER_IDS = (
    "00000000-0000-0000-0000-00000000a101",
    "00000000-0000-0000-0000-00000000a102",
)
_FORBIDDEN_L3_RE = re.compile(
    r"\b(cursor|chatgpt|gemini|openrouter|нейросет|нейросеть|"
    r"искусственн\w+\s+интеллект|(?<!\w)ии(?!\w)|(?<!\w)ai(?!\w)|агент|промпт)\b",
    re.I,
)

_JUDGE_L2_SYSTEM = """Ты — аудитор качества универсальных фриланс-откликов RawLead (shared draft, O57).
Оцени reply_draft относительно заказа (title, body, task_summary, tools_required).

Верни один JSON-объект без markdown:
relevance — 1–5 (отклик про этот заказ, не шаблон)
specificity — 1–5 (конкретные шаги/детали из ТЗ, не вода)
universal_helpful — 1–5 (универсален для типового исполнителя, но полезен — не «готов всё»)
tools_match — «да» | «нет» | «частично» (tools_required согласованы с текстом отклика и ТЗ)
send_as_is — true | false (реальный фрилансер отправил бы as-is)
reason — одно предложение на русском
prompt_fix — если send_as_is=false: один абзац — паттерн для правки shared-draft / L2 промпта, иначе ""
"""

_JUDGE_L1_SYSTEM = """Ты — аудитор L1-разбора заказа RawLead (карточка в ленте: task_summary, feed_visible, теги, complexity).
Оцени, правильно ли ИИ понял заказ по title/body и насколько верна оценка сложности (complexity 1–4).

Шкала complexity L1: 1 — скрипт·1 файл·~1 вечер · 2 — типовой проект, ясное ТЗ · 3 — несколько систем/монолит с нормальным ТЗ · 4 — нет нормального ТЗ/«сделайте красиво»/риск на исполнителе.

Верни один JSON-объект без markdown:
context_understanding — 1–5 (summary и теги отражают title/body)
category_ok — true | false (dev/design/marketing/text не перепутаны; поле category в карточке = primary_category L1)
l1_usable — true | false (можно доверять карточке без перечитывания биржи)
expected_complexity — целое 1–4 (какой уровень ты бы поставил по title/body по шкале L1)
complexity_rating — 1–4 (точность L1: 4 = L1 совпал с expected, 3 = ошибка на 1, 2 = на 2, 1 = полный промах)
complexity_ok — true | false (L1 complexity совпал с expected или отличается не более чем на 1)
reason — одно предложение на русском
l1_prompt_fix — если l1_usable=false: что править в L1 промпте (_LITE_SYSTEM), иначе ""
complexity_prompt_fix — если complexity_ok=false: паттерн для _LITE_SYSTEM (шкала complexity), иначе ""
"""

_JUDGE_L3_SYSTEM = """Ты — аудитор L3 RawLead (per-user personal reply, O89 uniquify).
Сравни shared_reply_draft (общий L2 на лид) и personal_reply_draft (версия для конкретного user_id).

Оценивай «живость» как на FL.ru/Kwork: коротко, по делу, без канцелярита («реализую модуль», «профессиональный подход»).

Верни один JSON-объект без markdown:
meaning_preserved — 1–5 (ключевой смысл и шаги shared сохранены)
uniqueness — 1–5 (personal заметно другой текст и порядок фраз, не синоним-замена shared)
human_tone — 1–5 (звучит как живой фрилансер, не как ИИ/шаблон)
order_fit — 1–5 (personal по-прежнему про этот заказ)
send_as_is — true | false (реальный фрилансер отправил бы personal, не shared)
forbidden_leak — true | false (в personal есть Cursor/ИИ/нейросеть/ChatGPT/Gemini/AI/агент/промпт)
reason — одно предложение на русском
prompt_fix — если send_as_is=false, human_tone≤3, uniqueness≤2 или forbidden_leak=true: паттерн для L3 human prompt, иначе ""
"""


def _parse_judge_since(raw: str) -> datetime:
    text = (raw or "").strip() or _O72E_JUDGE_SINCE_DEFAULT
    try:
        parsed = date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"--judge-since: invalid date {text!r}, use YYYY-MM-DD") from exc
    return datetime(parsed.year, parsed.month, parsed.day, tzinfo=timezone.utc)


def _since_sql(since: datetime | None) -> tuple[str, list[Any]]:
    if since is None:
        return "", []
    return " AND created_at >= %s", [since]


def _lead_created_at(lead: dict[str, Any]) -> datetime | None:
    raw = lead.get("created_at")
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    text = str(raw).strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _filter_fresh_for_judge(
    leads: list[dict[str, Any]],
    *,
    since: datetime,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for lead in leads:
        created = _lead_created_at(lead)
        if created is not None and created >= since:
            out.append(lead)
    return out


def _norm_verdict(raw: str) -> str:
    v = (raw or "").strip().casefold()
    if v in _SKIP_VERDICTS:
        return "мимо"
    if v in _MAYBE_VERDICTS:
        return "сомнительно"
    if v in _TAKE_VERDICTS:
        return "брать"
    return v


def _parse_string_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    items: list[str] = []
    if isinstance(raw, list):
        items = [str(t).strip() for t in raw if str(t).strip()]
    elif isinstance(raw, str) and raw.strip():
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                items = [str(t).strip() for t in data if str(t).strip()]
            else:
                items = [raw.strip()]
        except json.JSONDecodeError:
            items = [raw.strip()]
    return items


def _parse_tools_raw(raw: Any) -> list[str]:
    if raw is None:
        return []
    items: list[str] = []
    if isinstance(raw, list):
        items = [str(t) for t in raw if str(t).strip()]
    elif isinstance(raw, str) and raw.strip():
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                items = [str(t) for t in data if str(t).strip()]
            else:
                items = [raw.strip()]
        except json.JSONDecodeError:
            items = [raw.strip()]
    expanded: list[str] = []
    for item in items:
        for part in re.split(r"[,;/|]+", item):
            s = part.strip()
            if s:
                expanded.append(s)
    return normalize_tags(expanded)[:8]


def _parse_tools(raw: Any) -> list[str]:
    return list(normalize_tools_required(_parse_tools_raw(raw)))


def _hinted_tools(title: str, body: str, *extra: str) -> set[str]:
    return set(tools_from_tz_text(title, body, *extra))


def _json_datetime(raw: Any) -> str:
    if isinstance(raw, datetime):
        return raw.isoformat()
    return str(raw or "")


def _row_to_lead(row: tuple[Any, ...]) -> dict[str, Any]:
    cat_raw = (row[11] or "other").strip() or "other"
    category = cat_raw if cat_raw in CATEGORIES else "other"
    ai_reasons, complexity = parse_ai_reasons_raw(row[9])
    return {
        "lead_id": int(row[0]),
        "source": row[1] or "",
        "title": row[2] or "",
        "body": row[3] or "",
        "url": row[4] or "",
        "budget_text": row[5] or "",
        "ai_verdict": row[7] or "",
        "lead_tags": normalize_tags(_parse_string_list(row[8]))[:6],
        "ai_reasons": ai_reasons[:5],
        "complexity": complexity,
        "category": category,
        "task_summary": (row[12] or "").strip(),
        "tools_required_raw": _parse_tools_raw(row[13]),
        "tools_required": _parse_tools(row[13]),
        "reply_draft": (row[14] or "").strip(),
        "created_at": _json_datetime(row[10]),
        "sample_bucket": "main",
    }


def _fetch_leads_by_ids(conn: psycopg.Connection, lead_ids: list[int]) -> list[dict[str, Any]]:
    if not lead_ids:
        return []
    sql = f"SELECT {_SELECT_COLS} FROM leads WHERE id = ANY(%s)"
    with conn.cursor() as cur:
        cur.execute(sql, (lead_ids,))
        rows = cur.fetchall()
    by_id = {int(r[0]): _row_to_lead(r) for r in rows}
    out: list[dict[str, Any]] = []
    for lid in lead_ids:
        if lid in by_id:
            lead = dict(by_id[lid])
            lead["sample_bucket"] = "owner_ids"
            out.append(lead)
    return out


def _source_like_sql(source_like: str) -> tuple[str, list[Any]]:
    text = (source_like or "").strip()
    if not text:
        return "", []
    return " AND source LIKE %s ", [text]


def _fetch_empty_l1(
    conn: psycopg.Connection,
    *,
    limit: int,
    src_sql: str,
    src_params: list[Any],
    since_sql: str = "",
    since_params: list[Any] | None = None,
    source_like_sql: str = "",
    source_like_params: list[Any] | None = None,
) -> list[dict]:
    since_params = since_params or []
    source_like_params = source_like_params or []
    sql = f"""
        SELECT {_SELECT_COLS}
        FROM leads
        WHERE is_visible = TRUE
          {src_sql}
          {source_like_sql}
          {since_sql}
          AND COALESCE(NULLIF(TRIM(task_summary), ''), '') = ''
        ORDER BY id DESC
        LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(
            sql,
            [*src_params, *source_like_params, *since_params, limit],
        )
        rows = cur.fetchall()
    out = [_row_to_lead(r) for r in rows]
    for lead in out:
        lead["sample_bucket"] = "empty_l1"
    return out


def fetch_fresh_l1_gate_leads(
    conn: psycopg.Connection,
    *,
    limit: int,
    src_sql: str,
    src_params: list[Any],
    since: datetime,
) -> list[dict[str, Any]]:
    """Visible fresh leads with L1 (task_summary), без требования reply_draft — для O72e full gate."""
    since_sql, since_params = _since_sql(since)
    sql = f"""
        SELECT {_SELECT_COLS}
        FROM leads
        WHERE is_visible = TRUE
          {src_sql}
          {since_sql}
          AND COALESCE(NULLIF(TRIM(task_summary), ''), '') <> ''
          AND LOWER(TRIM(COALESCE(ai_verdict, ''))) NOT IN ('мимо', 'пропустить', 'skip', '')
        ORDER BY id DESC
        LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, [*src_params, *since_params, limit])
        rows = cur.fetchall()
    out = [_row_to_lead(r) for r in rows]
    for lead in out:
        lead["sample_bucket"] = "fresh_l1_gate"
    return out


def _stratified_sample(
    conn: psycopg.Connection,
    *,
    n: int,
    src_sql: str,
    src_params: list[Any],
    pool_size: int = 2500,
    since_sql: str = "",
    since_params: list[Any] | None = None,
    source_like_sql: str = "",
    source_like_params: list[Any] | None = None,
    require_reply_draft: bool = True,
) -> list[dict]:
    since_params = since_params or []
    source_like_params = source_like_params or []
    draft_sql = (
        "AND COALESCE(NULLIF(TRIM(reply_draft), ''), '') <> ''"
        if require_reply_draft
        else ""
    )
    sql = f"""
        SELECT {_SELECT_COLS}
        FROM leads
        WHERE is_visible = TRUE
          {src_sql}
          {source_like_sql}
          {since_sql}
          {draft_sql}
        ORDER BY id DESC
        LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(
            sql,
            [*src_params, *source_like_params, *since_params, pool_size],
        )
        rows = cur.fetchall()

    pool = [_row_to_lead(r) for r in rows]
    buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for lead in pool:
        cat = lead["category"] if lead["category"] in CATEGORIES else "other"
        buckets[(cat, lead["source"] or "?")].append(lead)

    if not buckets:
        return []

    per_bucket = max(1, n // len(buckets))
    picked: list[dict] = []
    seen: set[int] = set()
    for key in sorted(buckets.keys()):
        for lead in buckets[key][:per_bucket]:
            if lead["lead_id"] not in seen:
                seen.add(lead["lead_id"])
                picked.append(lead)
    # top-up from pool if under n
    for lead in pool:
        if len(picked) >= n:
            break
        if lead["lead_id"] not in seen:
            seen.add(lead["lead_id"])
            picked.append(lead)
    return picked[:n]


def audit_lead(lead: dict[str, Any]) -> dict[str, Any]:
    fails: list[str] = []
    warns: list[str] = []
    verdict = _norm_verdict(lead["ai_verdict"])
    task_summary = lead["task_summary"]
    reply_draft = lead["reply_draft"]
    tools = lead["tools_required"]
    bucket = lead.get("sample_bucket", "main")
    audit_l2 = bucket != "empty_l1"
    audit_tools = audit_l2 and bool(reply_draft)

    if verdict != "мимо" and not task_summary:
        fails.append("L1:empty_task_summary")

    if audit_l2 and verdict in ("брать", "сомнительно"):
        if not reply_draft:
            fails.append("L2:empty_reply_draft")
        else:
            try:
                if verdict == "брать":
                    _validate_reply_draft_take(reply_draft)
                else:
                    _validate_reply_draft_maybe(reply_draft)
            except AiAnalyzeError as exc:
                fails.append(f"L2:{exc}")
            v_label = "Брать" if verdict == "брать" else "Сомнительно"
            sw = reply_draft_sentence_warn(v_label, reply_draft)
            if sw:
                warns.append(sw)
            cw = reply_draft_cliche_warn(reply_draft)
            if cw:
                warns.append(cw)
    elif audit_l2 and verdict == "мимо" and reply_draft:
        warns.append("warn:reply_draft_nonempty_for_mimo")

    if audit_tools:
        from ai_analyze import _effective_tools_for_audit
        from tools_catalog import map_tool_to_generic

        stored_tools = lead["tools_required"]
        tools = _effective_tools_for_audit(
            stored_tools,
            title=lead["title"],
            description=lead["body"],
            task_summary=task_summary,
            lead_tags=lead.get("lead_tags") or [],
        )
        lock_src = lead.get("tools_required_raw")
        if lock_src is None:
            lock_src = stored_tools
        locked = vendor_lock_tools(
            lock_src if isinstance(lock_src, (list, tuple)) else _parse_tools_raw(lock_src)
        )
        if locked:
            fails.append(f"tools:vendor_lock:{','.join(locked[:5])}")

        if len(tools) < 2:
            fails.append("tools:min_2_required")
        elif len(tools) > 8:
            fails.append("tools:max_8_exceeded")

        if len(tools) != len(set(t.lower() for t in tools)):
            fails.append("tools:duplicates")

        invalid_tools = [
            str(t).strip()
            for t in stored_tools
            if str(t).strip() and not is_known_tool(map_tool_to_generic(str(t).strip()))
        ]
        if invalid_tools:
            fails.append(f"tools:not_in_catalog:{','.join(invalid_tools[:5])}")

    if audit_tools and verdict == "брать":
        hinted = _hinted_tools(
            lead["title"],
            lead["body"],
            lead.get("task_summary") or "",
        )
        if hinted and not tools:
            fails.append(f"tools:empty_but_desc_hints:{','.join(sorted(hinted)[:5])}")
        elif hinted and tools:
            resolved = {resolve_canonical_tag(t) for t in tools}
            missing = sorted(h for h in hinted if h not in resolved)
            if missing:
                warns.append(f"warn:tools_missing_hints:{','.join(missing[:5])}")

    draft_fails = [f for f in fails if f.startswith(("L1:", "L2:"))]
    tools_fails = [f for f in fails if f.startswith("tools:")]
    draft_only_pass = not draft_fails
    tools_pass = not tools_fails
    auto_pass = draft_only_pass and tools_pass
    return {
        **lead,
        "verdict_norm": verdict,
        "fails": fails,
        "draft_fails": draft_fails,
        "tools_fails": tools_fails,
        "warns": warns,
        "draft_only_pass": draft_only_pass,
        "tools_pass": tools_pass,
        "auto_pass": auto_pass,
    }


def _build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    l2_rows = [
        r for r in results
        if r.get("sample_bucket") != "empty_l1" and (r.get("reply_draft") or "").strip()
    ]
    l1_empty_rows = [r for r in results if r.get("sample_bucket") == "empty_l1"]
    total = len(l2_rows)
    passed = sum(1 for r in l2_rows if r["auto_pass"])
    draft_passed = sum(1 for r in l2_rows if r["draft_only_pass"])
    tools_passed = sum(1 for r in l2_rows if r["tools_pass"])
    by_fail_type: Counter[str] = Counter()
    by_draft_fail_type: Counter[str] = Counter()
    by_tools_fail_type: Counter[str] = Counter()
    for r in results:
        if r.get("sample_bucket") == "empty_l1":
            continue
        for f in r["fails"]:
            key = f.split(":", 2)[0] + (":" + f.split(":", 2)[1] if ":" in f else "")
            if f.startswith("tools:not_in_catalog"):
                key = "tools:not_in_catalog"
            elif f.startswith("tools:empty_but_desc_hints"):
                key = "tools:empty_but_desc_hints"
            by_fail_type[key] += 1
            if f.startswith(("L1:", "L2:")):
                dk = f.split(":", 2)[0] + (":" + f.split(":", 2)[1] if ":" in f else "")
                by_draft_fail_type[dk] += 1
            elif f.startswith("tools:"):
                by_tools_fail_type[key] += 1

    by_cat: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "pass": 0, "draft_pass": 0})
    by_source: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "pass": 0, "draft_pass": 0})
    for r in l2_rows:
        cat = r["category"]
        src = r["source"] or "?"
        by_cat[cat]["total"] += 1
        by_source[src]["total"] += 1
        if r["auto_pass"]:
            by_cat[cat]["pass"] += 1
            by_source[src]["pass"] += 1
        if r["draft_only_pass"]:
            by_cat[cat]["draft_pass"] += 1
            by_source[src]["draft_pass"] += 1

    worst = sorted(
        [r for r in l2_rows if not r["draft_only_pass"]],
        key=lambda x: (len(x["draft_fails"]), x["lead_id"]),
        reverse=True,
    )[:10]

    tools_worst = sorted(
        [r for r in l2_rows if not r["tools_pass"]],
        key=lambda x: (len(x["tools_fails"]), x["lead_id"]),
        reverse=True,
    )[:10]

    l1_missing = sum(
        1 for r in l1_empty_rows if any(f.startswith("L1:") for f in r["fails"])
    )
    rate = (passed / total) if total else 0.0
    draft_rate = (draft_passed / total) if total else 0.0
    tools_rate = (tools_passed / total) if total else 0.0
    return {
        "total": total,
        "merged_total": len(results),
        "l1_empty_sample": len(l1_empty_rows),
        "l1_empty_fail": l1_missing,
        "draft_only_pass": draft_passed,
        "draft_only_fail": total - draft_passed,
        "draft_only_pass_rate": round(draft_rate, 4),
        "draft_only_pass_pct": round(draft_rate * 100, 1),
        "accept_draft_95pct": draft_rate >= 0.95 if total else False,
        "tools_pass": tools_passed,
        "tools_fail": total - tools_passed,
        "tools_pass_rate": round(tools_rate, 4),
        "tools_pass_pct": round(tools_rate * 100, 1),
        "auto_pass": passed,
        "auto_fail": total - passed,
        "auto_pass_rate": round(rate, 4),
        "auto_pass_pct": round(rate * 100, 1),
        "accept_85pct": rate >= 0.85 if total else False,
        "fail_types": dict(by_fail_type.most_common(20)),
        "draft_fail_types": dict(by_draft_fail_type.most_common(20)),
        "tools_fail_types": dict(by_tools_fail_type.most_common(20)),
        "by_category": dict(by_cat),
        "by_source": dict(by_source),
        "top_fail_leads": [
            {
                "lead_id": r["lead_id"],
                "title": r["title"][:80],
                "fails": r["draft_fails"],
                "source": r["source"],
                "category": r["category"],
                "sample_bucket": r.get("sample_bucket"),
            }
            for r in worst
        ],
        "top_tools_fail_leads": [
            {
                "lead_id": r["lead_id"],
                "title": r["title"][:80],
                "fails": r["tools_fails"],
                "source": r["source"],
                "category": r["category"],
                "sample_bucket": r.get("sample_bucket"),
            }
            for r in tools_worst
        ],
    }


def _judge_model(cfg) -> str:
    return (cfg.ai_model_judge or "").strip() or "anthropic/claude-sonnet-4"


def _l2_judge_targets(leads: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    """O200: stratified L2 judge — ~limit/4 per dev/design/marketing/text when possible."""
    with_draft = [r for r in leads if (r.get("reply_draft") or "").strip()]
    per_cat = max(1, limit // len(CATEGORIES))
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for lead in with_draft:
        cat = (lead.get("category") or "other").strip() or "other"
        if cat in CATEGORIES:
            buckets[cat].append(lead)
    picked: list[dict[str, Any]] = []
    seen: set[int] = set()
    for cat in CATEGORIES:
        for lead in buckets.get(cat, [])[:per_cat]:
            lid = int(lead["lead_id"])
            if lid not in seen:
                seen.add(lid)
                picked.append(lead)
    for lead in with_draft:
        if len(picked) >= limit:
            break
        lid = int(lead["lead_id"])
        if lid not in seen:
            seen.add(lid)
            picked.append(lead)
    return picked[:limit]


def _l1_judge_targets(leads: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    seen: set[int] = set()
    out: list[dict[str, Any]] = []
    for lead in leads:
        if lead.get("sample_bucket") == "empty_l1" and lead["lead_id"] not in seen:
            seen.add(lead["lead_id"])
            out.append(lead)
    for lead in leads:
        if len(out) >= limit:
            break
        if (lead.get("task_summary") or "").strip() and lead["lead_id"] not in seen:
            seen.add(lead["lead_id"])
            out.append(lead)
    for lead in leads:
        if len(out) >= limit:
            break
        if lead["lead_id"] not in seen:
            seen.add(lead["lead_id"])
            out.append(lead)
    return out[:limit]


def _run_judge_l2(cfg, leads: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    if not cfg.ai_active:
        return []
    model = _judge_model(cfg)
    judged: list[dict[str, Any]] = []
    targets = _l2_judge_targets(leads, limit=limit)
    for lead in targets:
        cat = (lead.get("category") or "other").strip() or "other"
        user = (
            f"Заголовок: {lead['title']}\n"
            f"Описание:\n{lead['body'][:3000]}\n\n"
            f"primary_category: {cat}\n"
            f"task_summary: {lead['task_summary']}\n"
            f"tools_required: {', '.join(lead['tools_required']) or '—'}\n\n"
            f"reply_draft:\n{lead['reply_draft']}\n"
        )
        entry: dict[str, Any] = {"lead_id": lead["lead_id"], "model": model, "category": cat}
        try:
            raw = _openrouter_chat(
                cfg,
                model=model,
                system=_JUDGE_L2_SYSTEM,
                user=user,
                timeout_sec=60.0,
                json_mode=True,
            )
            data = _extract_json_object(raw or "")
            entry.update(
                relevance=int(data.get("relevance", 0)),
                specificity=int(data.get("specificity", 0)),
                universal_helpful=int(data.get("universal_helpful", 0)),
                tools_match=str(data.get("tools_match", "")),
                send_as_is=bool(data.get("send_as_is")),
                reason=str(data.get("reason", ""))[:300],
                prompt_fix=str(data.get("prompt_fix", ""))[:500],
            )
        except Exception as exc:  # noqa: BLE001 — audit script
            entry["error"] = str(exc)[:200]
        judged.append(entry)
        time.sleep(0.5)
    return judged


def _run_judge_l1(cfg, leads: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    if not cfg.ai_active:
        return []
    model = _judge_model(cfg)
    judged: list[dict[str, Any]] = []
    for lead in _l1_judge_targets(leads, limit=limit):
        user = (
            f"Заголовок: {lead['title']}\n"
            f"Описание:\n{lead['body'][:3000]}\n\n"
            f"primary_category (L1/DB): {lead['category']}\n"
            f"feed_visible: {'true' if _norm_verdict(lead['ai_verdict']) != 'мимо' else 'false'}\n"
            f"task_summary: {lead['task_summary'] or '—'}\n"
            f"lead_tags: {', '.join(lead.get('lead_tags') or []) or '—'}\n"
            f"ai_reasons: {' | '.join(lead.get('ai_reasons') or []) or '—'}\n"
            f"complexity (L1): {lead.get('complexity') if lead.get('complexity') is not None else '—'}\n"
        )
        entry: dict[str, Any] = {"lead_id": lead["lead_id"], "model": model}
        try:
            raw = _openrouter_chat(
                cfg,
                model=model,
                system=_JUDGE_L1_SYSTEM,
                user=user,
                timeout_sec=60.0,
                json_mode=True,
            )
            data = _extract_json_object(raw or "")
            complexity_rating = int(data.get("complexity_rating", 0))
            complexity_ok = bool(data.get("complexity_ok"))
            expected_cx = int(data.get("expected_complexity", 0) or 0)
            l1_cx = lead.get("complexity")
            if (
                isinstance(l1_cx, int)
                and 1 <= l1_cx <= 4
                and 1 <= expected_cx <= 4
                and abs(l1_cx - expected_cx) <= 1
            ):
                complexity_ok = True
            elif not complexity_ok and complexity_rating >= 3:
                complexity_ok = True
            entry.update(
                expected_complexity=expected_cx or None,
                context_understanding=int(data.get("context_understanding", 0)),
                category_ok=bool(data.get("category_ok")),
                l1_usable=bool(data.get("l1_usable")),
                complexity_rating=complexity_rating,
                complexity_ok=complexity_ok,
                reason=str(data.get("reason", ""))[:300],
                l1_prompt_fix=str(data.get("l1_prompt_fix", ""))[:500],
                complexity_prompt_fix=str(data.get("complexity_prompt_fix", ""))[:500],
            )
        except Exception as exc:  # noqa: BLE001 — audit script
            entry["error"] = str(exc)[:200]
        judged.append(entry)
        time.sleep(0.5)
    return judged


def _drafts_too_similar(shared: str, personal: str) -> bool:
    a = re.sub(r"\s+", " ", (shared or "").strip().casefold())
    b = re.sub(r"\s+", " ", (personal or "").strip().casefold())
    if not a or not b:
        return True
    return a == b or (len(a) > 40 and a in b) or (len(b) > 40 and b in a)


def _fetch_l3_pairs_from_db(
    conn: psycopg.Connection,
    lead_ids: list[int],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    if not lead_ids:
        return []
    sql = """
        SELECT ulr.user_id::text, ulr.lead_id, ulr.reply_draft,
               COALESCE(l.reply_draft, ''), l.title, l.body,
               COALESCE(l.task_summary, ''), l.tools_required
        FROM user_lead_replies ulr
        JOIN leads l ON l.id = ulr.lead_id
        WHERE ulr.deleted_at IS NULL
          AND ulr.lead_id = ANY(%s)
          AND length(trim(ulr.reply_draft)) > 30
          AND length(trim(COALESCE(l.reply_draft, ''))) > 30
        ORDER BY ulr.created_at DESC
        LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, (lead_ids, max(1, limit)))
        rows = cur.fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        shared = (row[3] or "").strip()
        personal = (row[2] or "").strip()
        if _drafts_too_similar(shared, personal):
            continue
        out.append(
            {
                "user_id": str(row[0]),
                "lead_id": int(row[1]),
                "personal_reply": personal,
                "shared_reply": shared,
                "title": row[4] or "",
                "body": row[5] or "",
                "task_summary": row[6] or "",
                "tools_required": _parse_tools(row[7]),
                "source": "db",
            }
        )
    return out


def _build_l3_judge_targets(
    cfg,
    conn: psycopg.Connection,
    leads: list[dict[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    from ai_analyze import rephrase_reply_draft_per_user

    lead_ids = [int(l["lead_id"]) for l in leads if l.get("lead_id")]
    targets = _fetch_l3_pairs_from_db(conn, lead_ids, limit=limit)
    seen = {(t["user_id"], t["lead_id"]) for t in targets}
    if len(targets) >= limit:
        return targets[:limit]

    errors: list[str] = []
    for lead in leads:
        if len(targets) >= limit:
            break
        shared = (lead.get("reply_draft") or "").strip()
        if len(shared) < 40 or _norm_verdict(lead.get("ai_verdict", "")) == "мимо":
            continue
        for user_id in _AUDIT_L3_USER_IDS:
            if len(targets) >= limit:
                break
            key = (user_id, lead["lead_id"])
            if key in seen:
                continue
            personal = rephrase_reply_draft_per_user(
                cfg,
                base_reply_draft=shared,
                user_id=user_id,
                lead_id=int(lead["lead_id"]),
                errors=errors,
                log_prefix=f"judge-l3:{lead['lead_id']}:",
            )
            if not personal or _drafts_too_similar(shared, personal):
                continue
            seen.add(key)
            targets.append(
                {
                    "user_id": user_id,
                    "lead_id": int(lead["lead_id"]),
                    "personal_reply": personal.strip(),
                    "shared_reply": shared,
                    "title": lead.get("title") or "",
                    "body": lead.get("body") or "",
                    "task_summary": lead.get("task_summary") or "",
                    "tools_required": lead.get("tools_required") or [],
                    "source": "synthetic",
                }
            )
            time.sleep(0.3)
    return targets[:limit]


def _run_judge_l3(cfg, targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not cfg.ai_active or not targets:
        return []
    model = _judge_model(cfg)
    judged: list[dict[str, Any]] = []
    for row in targets:
        user = (
            f"user_id: {row['user_id']}\n"
            f"lead_id: {row['lead_id']}\n"
            f"source: {row.get('source', 'db')}\n\n"
            f"Заголовок: {row['title']}\n"
            f"Описание:\n{(row['body'] or '')[:2500]}\n\n"
            f"task_summary: {row.get('task_summary') or '—'}\n"
            f"tools_required: {', '.join(row.get('tools_required') or []) or '—'}\n\n"
            f"shared_reply_draft:\n{row['shared_reply']}\n\n"
            f"personal_reply_draft:\n{row['personal_reply']}\n"
        )
        entry: dict[str, Any] = {
            "lead_id": row["lead_id"],
            "user_id": row["user_id"],
            "source": row.get("source", "db"),
            "model": model,
            "shared_reply": row.get("shared_reply", ""),
            "personal_reply": row.get("personal_reply", ""),
            "same_as_shared": _drafts_too_similar(
                row["shared_reply"], row["personal_reply"]
            ),
        }
        leak_auto = bool(_FORBIDDEN_L3_RE.search(row["personal_reply"] or ""))
        entry["forbidden_leak_auto"] = leak_auto
        try:
            raw = _openrouter_chat(
                cfg,
                model=model,
                system=_JUDGE_L3_SYSTEM,
                user=user,
                timeout_sec=60.0,
                json_mode=True,
            )
            data = _extract_json_object(raw or "")
            entry.update(
                meaning_preserved=int(data.get("meaning_preserved", 0)),
                uniqueness=int(data.get("uniqueness", 0)),
                human_tone=int(data.get("human_tone", 0) or data.get("uniqueness", 0)),
                order_fit=int(data.get("order_fit", 0)),
                send_as_is=bool(data.get("send_as_is")),
                forbidden_leak=bool(data.get("forbidden_leak")) or leak_auto,
                reason=str(data.get("reason", ""))[:300],
                prompt_fix=str(data.get("prompt_fix", ""))[:500],
            )
        except Exception as exc:  # noqa: BLE001 — audit script
            entry["error"] = str(exc)[:200]
        judged.append(entry)
        time.sleep(0.5)
    return judged


def _judge_l3_summary(judged: list[dict[str, Any]]) -> dict[str, Any]:
    ok = [
        j
        for j in judged
        if "error" not in j and j.get("meaning_preserved")
    ]
    if not ok:
        return {
            "count": len(judged),
            "scored": 0,
            "db_pairs": 0,
            "synthetic_pairs": 0,
            "avg_meaning": 0,
            "avg_uniqueness": 0,
            "avg_order_fit": 0,
            "avg_combined_3": 0,
            "send_as_is_pct": 0,
            "forbidden_leak_pct": 0,
            "accept_l3": False,
            "top_worst": [],
            "prompt_recommendations": [],
        }
    meaning = sum(j["meaning_preserved"] for j in ok) / len(ok)
    uniq = sum(j["uniqueness"] for j in ok) / len(ok)
    human = sum(j.get("human_tone", j.get("uniqueness", 0)) for j in ok) / len(ok)
    fit = sum(j["order_fit"] for j in ok) / len(ok)
    combined = (meaning + uniq + human + fit) / 4
    send_ok = sum(1 for j in ok if j.get("send_as_is")) / len(ok)
    leak = sum(1 for j in ok if j.get("forbidden_leak")) / len(ok)
    db_n = sum(1 for j in ok if j.get("source") == "db")
    syn_n = sum(1 for j in ok if j.get("source") == "synthetic")
    worst = sorted(
        ok,
        key=lambda x: (
            x.get("forbidden_leak", False),
            x["meaning_preserved"] + x["uniqueness"] + x.get("order_fit", 0),
        ),
    )[:10]
    patterns: list[str] = []
    for j in worst:
        if j.get("prompt_fix"):
            patterns.append(j["prompt_fix"])
    accept = (
        combined >= _JUDGE_L3_COMBINED_MIN
        and send_ok >= _JUDGE_L3_SEND_MIN
        and uniq >= _JUDGE_L3_UNIQUENESS_MIN
        and human >= _JUDGE_L3_UNIQUENESS_MIN
        and leak <= _JUDGE_L3_FORBIDDEN_LEAK_MAX_PCT
    )
    return {
        "count": len(judged),
        "scored": len(ok),
        "db_pairs": db_n,
        "synthetic_pairs": syn_n,
        "avg_meaning": round(meaning, 2),
        "avg_uniqueness": round(uniq, 2),
        "avg_human_tone": round(human, 2),
        "avg_order_fit": round(fit, 2),
        "avg_combined_3": round(combined, 2),
        "send_as_is_pct": round(send_ok * 100, 1),
        "forbidden_leak_pct": round(leak * 100, 1),
        "accept_l3": accept,
        "top_worst": worst,
        "prompt_recommendations": patterns[:10],
    }


_JUDGE_L2_SEND_MIN_PER_CAT = 0.70  # O200 owner gate (was 0.80 CAT-80 pilot)
_JUDGE_L2_SEND_FLOOR_PER_CAT = 0.50
_JUDGE_L2_CAT_MIN_N = 10


def _judge_l2_summary(judged: list[dict[str, Any]]) -> dict[str, Any]:
    ok = [
        j
        for j in judged
        if "error" not in j and j.get("relevance") and j.get("universal_helpful")
    ]
    if not ok:
        return {
            "count": len(judged),
            "scored": 0,
            "avg_relevance": 0,
            "avg_specificity": 0,
            "avg_universal_helpful": 0,
            "avg_combined_3": 0,
            "send_as_is_pct": 0,
            "accept_l2": False,
            "accept_l2_balanced": False,
            "gate_owner_send_min_pct": round(_JUDGE_L2_SEND_MIN_PER_CAT * 100, 0),
            "by_category": {},
            "worst_by_category": {},
            "top_worst": [],
            "prompt_recommendations": [],
        }
    rel = sum(j["relevance"] for j in ok) / len(ok)
    spec = sum(j["specificity"] for j in ok) / len(ok)
    univ = sum(j["universal_helpful"] for j in ok) / len(ok)
    combined = (rel + spec + univ) / 3
    send_ok = sum(1 for j in ok if j.get("send_as_is")) / len(ok)
    worst = sorted(
        ok,
        key=lambda x: (
            x["relevance"] + x["specificity"] + x.get("universal_helpful", 0),
            x["relevance"],
        ),
    )[:10]
    patterns: list[str] = []
    for j in worst:
        if j.get("prompt_fix"):
            patterns.append(j["prompt_fix"])

    # --- per-category breakdown ---
    by_cat: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "send_ok": 0, "rel_sum": 0, "spec_sum": 0, "univ_sum": 0}
    )
    for j in ok:
        cat = (j.get("category") or "other").strip() or "other"
        by_cat[cat]["count"] += 1
        by_cat[cat]["send_ok"] += 1 if j.get("send_as_is") else 0
        by_cat[cat]["rel_sum"] += j.get("relevance", 0)
        by_cat[cat]["spec_sum"] += j.get("specificity", 0)
        by_cat[cat]["univ_sum"] += j.get("universal_helpful", 0)

    by_category: dict[str, dict[str, Any]] = {}
    for cat, d in by_cat.items():
        n = d["count"]
        s_pct = round(d["send_ok"] / n * 100, 1) if n else 0.0
        comb = round(
            (d["rel_sum"] + d["spec_sum"] + d["univ_sum"]) / (3 * n), 2
        ) if n else 0.0
        by_category[cat] = {
            "count": n,
            "send_as_is_pct": s_pct,
            "combined": comb,
        }

    # balanced gate: overall pass AND each measured category (n≥10) ≥70%, none <50%
    accept_l2 = combined >= _JUDGE_L2_COMBINED_MIN and send_ok >= _JUDGE_L2_SEND_MIN
    balanced_fail = False
    for cat, d in by_category.items():
        if d["count"] < _JUDGE_L2_CAT_MIN_N:
            continue
        pct = d["send_as_is_pct"]
        if pct < _JUDGE_L2_SEND_FLOOR_PER_CAT * 100:
            balanced_fail = True
            break
        if pct < _JUDGE_L2_SEND_MIN_PER_CAT * 100:
            balanced_fail = True
            break
    accept_l2_balanced = accept_l2 and not balanced_fail

    worst_by_category: dict[str, list[dict[str, Any]]] = {}
    for cat in ("dev", "design", "marketing", "text", "other"):
        cat_rows = [j for j in ok if (j.get("category") or "other").strip() == cat]
        if not cat_rows:
            continue
        worst_by_category[cat] = sorted(
            cat_rows,
            key=lambda x: (
                x["relevance"] + x["specificity"] + x.get("universal_helpful", 0),
                x["relevance"],
            ),
        )[:3]

    return {
        "count": len(judged),
        "scored": len(ok),
        "avg_relevance": round(rel, 2),
        "avg_specificity": round(spec, 2),
        "avg_universal_helpful": round(univ, 2),
        "avg_combined_3": round(combined, 2),
        "send_as_is_pct": round(send_ok * 100, 1),
        "accept_l2": accept_l2,
        "accept_l2_balanced": accept_l2_balanced,
        "gate_owner_send_min_pct": round(_JUDGE_L2_SEND_MIN_PER_CAT * 100, 0),
        "by_category": by_category,
        "worst_by_category": worst_by_category,
        "top_worst": worst,
        "prompt_recommendations": patterns[:10],
    }


def _judge_l1_summary(judged: list[dict[str, Any]]) -> dict[str, Any]:
    ok = [
        j
        for j in judged
        if "error" not in j and j.get("context_understanding")
    ]
    if not ok:
        return {
            "count": len(judged),
            "scored": 0,
            "avg_context": 0,
            "l1_usable_pct": 0,
            "category_ok_pct": 0,
            "avg_complexity_rating": 0,
            "complexity_ok_pct": 0,
            "accept_l1": False,
            "accept_complexity": False,
            "top_worst": [],
            "l1_prompt_recommendations": [],
            "complexity_prompt_recommendations": [],
        }
    ctx = sum(j["context_understanding"] for j in ok) / len(ok)
    usable = sum(1 for j in ok if j.get("l1_usable")) / len(ok)
    cat_ok = sum(1 for j in ok if j.get("category_ok")) / len(ok)
    cx_ratings = [
        int(j.get("complexity_rating", 0))
        for j in ok
        if int(j.get("complexity_rating", 0)) >= 1
    ]
    avg_cx = sum(cx_ratings) / len(cx_ratings) if cx_ratings else 0.0
    cx_ok = sum(1 for j in ok if j.get("complexity_ok")) / len(ok)
    accept_cx = (
        cx_ok >= _JUDGE_L1_COMPLEXITY_OK_PCT_MIN
        or avg_cx >= _JUDGE_L1_COMPLEXITY_OK_MIN
    )
    worst = sorted(
        ok,
        key=lambda x: (
            x.get("complexity_ok", True),
            x["context_understanding"],
            x.get("category_ok", False),
        ),
    )[:10]
    patterns: list[str] = []
    cx_patterns: list[str] = []
    for j in worst:
        if j.get("l1_prompt_fix"):
            patterns.append(j["l1_prompt_fix"])
        if j.get("complexity_prompt_fix"):
            cx_patterns.append(j["complexity_prompt_fix"])
    return {
        "count": len(judged),
        "scored": len(ok),
        "avg_context": round(ctx, 2),
        "l1_usable_pct": round(usable * 100, 1),
        "category_ok_pct": round(cat_ok * 100, 1),
        "avg_complexity_rating": round(avg_cx, 2),
        "complexity_ok_pct": round(cx_ok * 100, 1),
        "accept_l1": usable >= _JUDGE_L1_USABLE_MIN,
        "accept_complexity": accept_cx,
        "top_worst": worst,
        "l1_prompt_recommendations": patterns[:10],
        "complexity_prompt_recommendations": cx_patterns[:10],
    }


def _render_judge_md(
    report: dict[str, Any],
    results: list[dict[str, Any]],
    *,
    judge_l2: list[dict[str, Any]] | None,
    judge_l1: list[dict[str, Any]] | None,
    judge_l3: list[dict[str, Any]] | None = None,
) -> str:
    by_id = {r["lead_id"]: r for r in results}
    parts = ["L1", "L2"]
    if judge_l3:
        parts.append("L3")
    lines = [
        f"# O72e — LLM judge ({' + '.join(parts)}, свежие лиды)",
        "",
        f"- **Time:** {report['generated_at']}",
        f"- **Profile:** {report.get('profile', 'site')}",
        f"- **Judge model:** {report.get('judge_model', '—')}",
        f"- **Judge since:** {report.get('judge_since', '—')}",
        "",
    ]

    if judge_l2 is not None and report.get("judge_l2_summary"):
        js = report["judge_l2_summary"]
        lines.extend(
            [
                "## L2 — reply_draft (главный gate)",
                "",
                f"- Scored: **{js.get('scored', 0)}/{js.get('count', 0)}**",
                f"- Avg relevance: **{js.get('avg_relevance', 0)}**/5",
                f"- Avg specificity: **{js.get('avg_specificity', 0)}**/5",
                f"- Avg universal_helpful: **{js.get('avg_universal_helpful', 0)}**/5",
                f"- Avg combined (3 метрики): **{js.get('avg_combined_3', 0)}**/5 "
                f"({'✅ ≥4.0' if js.get('avg_combined_3', 0) >= _JUDGE_L2_COMBINED_MIN else '❌ <4.0'})",
                f"- send_as_is: **{js.get('send_as_is_pct', 0)}%** "
                f"({'✅ ≥70%' if js.get('send_as_is_pct', 0) >= _JUDGE_L2_SEND_MIN * 100 else '❌ <70%'})",
                f"- **Accept L2:** {'✅ PASS' if js.get('accept_l2') else '❌ FAIL'}",
                f"- **Accept L2 balanced (O200 owner — each cat n≥{_JUDGE_L2_CAT_MIN_N} "
                f"→ send ≥{int(_JUDGE_L2_SEND_MIN_PER_CAT * 100)}%):** "
                f"{'✅ PASS' if js.get('accept_l2_balanced') else '❌ FAIL'}",
                "",
            ]
        )
        by_cat = js.get("by_category") or {}
        if by_cat:
            lines.extend(
                [
                    "### By category (send_as_is%)",
                    "",
                    "| Category | n | send_as_is% | combined | gate |",
                    "|----------|---|-------------|----------|------|",
                ]
            )
            for cat in ("dev", "design", "marketing", "text", "other"):
                d = by_cat.get(cat)
                if not d:
                    continue
                n = d["count"]
                s = d["send_as_is_pct"]
                comb = d["combined"]
                if n < _JUDGE_L2_CAT_MIN_N:
                    gate = f"⏳ n<{_JUDGE_L2_CAT_MIN_N}"
                elif s < _JUDGE_L2_SEND_FLOOR_PER_CAT * 100:
                    gate = "❌ <50% floor"
                elif s < _JUDGE_L2_SEND_MIN_PER_CAT * 100:
                    gate = f"❌ <{int(_JUDGE_L2_SEND_MIN_PER_CAT * 100)}%"
                else:
                    gate = f"✅ ≥{int(_JUDGE_L2_SEND_MIN_PER_CAT * 100)}%"
                lines.append(f"| {cat} | {n} | {s}% | {comb}/5 | {gate} |")
            lines.append("")
        worst_by_cat = js.get("worst_by_category") or {}
        if worst_by_cat:
            lines.extend(["### Worst 3 per category (L2)", ""])
            for cat in ("dev", "design", "marketing", "text", "other"):
                rows = worst_by_cat.get(cat) or []
                if not rows:
                    continue
                lines.append(f"#### {cat}")
                for j in rows:
                    lead = by_id.get(j["lead_id"], {})
                    title = (lead.get("title") or "")[:80]
                    draft = (lead.get("reply_draft") or "")[:300]
                    lines.append(
                        f"- **#{j['lead_id']}** {title!r} — "
                        f"rel={j.get('relevance')} spec={j.get('specificity')} "
                        f"univ={j.get('universal_helpful')} send={j.get('send_as_is')}"
                    )
                    if j.get("reason"):
                        lines.append(f"  - reason: {j.get('reason', '')}")
                    if draft:
                        lines.append(
                            f"  - draft: «{draft}…»"
                            if len(draft) >= 300
                            else f"  - draft: «{draft}»"
                        )
                    if j.get("prompt_fix"):
                        lines.append(f"  - fix: {j['prompt_fix']}")
                lines.append("")
        lines.extend(
            [
                "### Top prompt-fix patterns (L2)",
                "",
            ]
        )
        for i, p in enumerate(js.get("prompt_recommendations", [])[:5], 1):
            lines.append(f"{i}. {p}")
        lines.extend(["", "### Top-10 worst L2 (цитаты)", ""])
        for j in js.get("top_worst", [])[:10]:
            lead = by_id.get(j["lead_id"], {})
            title = (lead.get("title") or "")[:80]
            draft = (lead.get("reply_draft") or "")[:400]
            lines.append(f"- **#{j['lead_id']}** {title!r}")
            lines.append(
                f"  - scores: rel={j.get('relevance')} spec={j.get('specificity')} "
                f"univ={j.get('universal_helpful')} send={j.get('send_as_is')}"
            )
            lines.append(f"  - reason: {j.get('reason', '')}")
            if draft:
                lines.append(f"  - draft: «{draft}…»" if len(draft) >= 400 else f"  - draft: «{draft}»")
            if j.get("prompt_fix"):
                lines.append(f"  - fix: {j['prompt_fix']}")

    if judge_l1 is not None and report.get("judge_l1_summary"):
        js1 = report["judge_l1_summary"]
        lines.extend(
            [
                "",
                "## L1 — task_summary / feed_visible / tags",
                "",
                f"- Scored: **{js1.get('scored', 0)}/{js1.get('count', 0)}**",
                f"- Avg context_understanding: **{js1.get('avg_context', 0)}**/5",
                f"- l1_usable: **{js1.get('l1_usable_pct', 0)}%** "
                f"({'✅ ≥70%' if js1.get('l1_usable_pct', 0) >= _JUDGE_L1_USABLE_MIN * 100 else '❌ <70%'})",
                f"- category_ok: **{js1.get('category_ok_pct', 0)}%**",
                f"- avg complexity_rating: **{js1.get('avg_complexity_rating', 0)}**/4",
                f"- complexity_ok: **{js1.get('complexity_ok_pct', 0)}%** "
                f"({'✅ ≥70% or avg≥3' if js1.get('accept_complexity') else '❌'})",
                f"- **Accept L1:** {'✅ PASS' if js1.get('accept_l1') else '❌ FAIL'}",
                f"- **Accept complexity (O97):** {'✅ PASS' if js1.get('accept_complexity') else '❌ FAIL'}",
                "",
                "### Top prompt-fix patterns (L1)",
                "",
            ]
        )
        for i, p in enumerate(js1.get("l1_prompt_recommendations", [])[:5], 1):
            lines.append(f"{i}. {p}")
        lines.extend(["", "### Top complexity-fix patterns (O97)", ""])
        for i, p in enumerate(js1.get("complexity_prompt_recommendations", [])[:5], 1):
            lines.append(f"{i}. {p}")
        lines.extend(["", "### Top-10 worst L1", ""])
        for j in js1.get("top_worst", [])[:10]:
            lead = by_id.get(j["lead_id"], {})
            title = (lead.get("title") or "")[:80]
            summary = (lead.get("task_summary") or "")[:300]
            lines.append(f"- **#{j['lead_id']}** {title!r}")
            lines.append(
                f"  - ctx={j.get('context_understanding')} "
                f"usable={j.get('l1_usable')} cat_ok={j.get('category_ok')} "
                f"cx={j.get('complexity_rating')} cx_ok={j.get('complexity_ok')}"
            )
            lines.append(f"  - reason: {j.get('reason', '')}")
            if summary:
                lines.append(f"  - summary: «{summary}»")
            if j.get("l1_prompt_fix"):
                lines.append(f"  - fix: {j['l1_prompt_fix']}")
            if j.get("complexity_prompt_fix"):
                lines.append(f"  - cx_fix: {j['complexity_prompt_fix']}")

    if judge_l3 is not None and report.get("judge_l3_summary"):
        js3 = report["judge_l3_summary"]
        lines.extend(
            [
                "",
                "## L3 — per-user reply (O89 uniquify)",
                "",
                f"- Scored: **{js3.get('scored', 0)}/{js3.get('count', 0)}** "
                f"(db={js3.get('db_pairs', 0)}, synthetic={js3.get('synthetic_pairs', 0)})",
                f"- Avg meaning_preserved: **{js3.get('avg_meaning', 0)}**/5",
                f"- Avg uniqueness: **{js3.get('avg_uniqueness', 0)}**/5 "
                f"({'✅ ≥3.0' if js3.get('avg_uniqueness', 0) >= _JUDGE_L3_UNIQUENESS_MIN else '❌ <3.0'})",
                f"- Avg human_tone: **{js3.get('avg_human_tone', 0)}**/5",
                f"- Avg order_fit: **{js3.get('avg_order_fit', 0)}**/5",
                f"- Avg combined (3 метрики): **{js3.get('avg_combined_3', 0)}**/5 "
                f"({'✅ ≥3.8' if js3.get('avg_combined_3', 0) >= _JUDGE_L3_COMBINED_MIN else '❌ <3.8'})",
                f"- send_as_is: **{js3.get('send_as_is_pct', 0)}%**",
                f"- forbidden_leak: **{js3.get('forbidden_leak_pct', 0)}%**",
                f"- **Accept L3:** {'✅ PASS' if js3.get('accept_l3') else '❌ FAIL'}",
                "",
                "### Top prompt-fix patterns (L3)",
                "",
            ]
        )
        for i, p in enumerate(js3.get("prompt_recommendations", [])[:5], 1):
            lines.append(f"{i}. {p}")
        lines.extend(["", "### Top-10 worst L3", ""])
        for j in js3.get("top_worst", [])[:10]:
            lead = by_id.get(j["lead_id"], {})
            title = (lead.get("title") or "")[:70]
            personal = (j.get("personal_reply") or "")[:350]
            lines.append(
                f"- **#{j['lead_id']}** user={str(j.get('user_id', ''))[:8]}… "
                f"{title!r} [{j.get('source', 'db')}]"
            )
            lines.append(
                f"  - scores: meaning={j.get('meaning_preserved')} "
                f"uniq={j.get('uniqueness')} human={j.get('human_tone')} fit={j.get('order_fit')} "
                f"send={j.get('send_as_is')} leak={j.get('forbidden_leak')}"
            )
            lines.append(f"  - reason: {j.get('reason', '')}")
            if personal:
                lines.append(f"  - personal: «{personal}…»" if len(personal) >= 350 else f"  - personal: «{personal}»")
            if j.get("prompt_fix"):
                lines.append(f"  - fix: {j['prompt_fix']}")

    lines.append("")
    return "\n".join(lines)


def _render_human_md(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        "# O72 — AI prod audit (human)",
        "",
        f"- **Time:** {report['generated_at']}",
        f"- **L2 sample (reply_draft):** {s['total']} leads",
        f"- **Draft quality (L1+L2, без tools):** **{s['draft_only_pass_pct']}%** "
        f"({'✅ ≥95%' if s['accept_draft_95pct'] else '❌ <95%'}) · "
        f"{s['draft_only_pass']}/{s['total']} pass",
        f"- **Tools bucket (отдельно):** **{s['tools_pass_pct']}%** · "
        f"{s['tools_pass']}/{s['total']} pass · KNOWN_TOOLS + canonical aliases",
        f"- **Combined auto-pass (draft+tools):** {s['auto_pass_pct']}% "
        f"({'✅ ≥85%' if s['accept_85pct'] else '❌ <85%'})",
        f"- **L1 empty bucket:** {s.get('l1_empty_sample', 0)} leads · "
        f"missing summary **{s.get('l1_empty_fail', 0)}**",
        f"- **Merged rows:** {s.get('merged_total', s['total'])}",
        f"- **Profile:** {report.get('profile', 'site')}",
        "",
        "> **O72b:** draft-only % — gate качества отклика (L1+L2); tools — отдельная строка "
        "(KNOWN_TOOLS whitelist + canonical aliases, без раздувания picker 51).",
        "",
        "---",
        "",
        "## Draft fail types (L1+L2)",
        "",
    ]
    if s.get("draft_fail_types"):
        for k, v in s["draft_fail_types"].items():
            lines.append(f"- `{k}`: **{v}**")
    else:
        lines.append("- _(none)_")

    lines.extend(["", "## Tools fail types", ""])
    if s.get("tools_fail_types"):
        for k, v in s["tools_fail_types"].items():
            lines.append(f"- `{k}`: **{v}**")
    else:
        lines.append("- _(none)_")

    lines.extend(["", "## Top draft fail cases", ""])
    for item in s.get("top_fail_leads", []):
        lines.append(
            f"- **#{item['lead_id']}** [{item['source']}/{item['category']}] "
            f"{item['title']!r}"
        )
        lines.append(f"  - fails: {', '.join(item['fails'])}")

    lines.extend(["", "## Top tools fail cases", ""])
    for item in s.get("top_tools_fail_leads", []):
        lines.append(
            f"- **#{item['lead_id']}** [{item['source']}/{item['category']}] "
            f"{item['title']!r}"
        )
        lines.append(f"  - fails: {', '.join(item['fails'])}")

    if report.get("judge_l2_summary"):
        js = report["judge_l2_summary"]
        lines.extend(
            [
                "",
                "## LLM judge (O72c)",
                "",
                f"- L2 scored: {js.get('scored', 0)}/{js.get('count', 0)} · "
                f"combined **{js.get('avg_combined_3', 0)}**/5 · "
                f"send_as_is **{js.get('send_as_is_pct', 0)}%** · "
                f"{'✅' if js.get('accept_l2') else '❌'}",
                f"- Подробно: `data/preprod_ai_prod_audit_judge.md`",
            ]
        )

    if report.get("owner_lead_ids"):
        lines.extend(["", "## Owner lead_ids (root cause)", ""])
        for r in report.get("owner_root_cause", []):
            lines.append(f"- **#{r['lead_id']}**: {', '.join(r['fails']) or 'auto_pass'}")

    lines.append("")
    return "\n".join(lines)


def build_sample_and_audit(
    leads: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Pure audit path for tests and CLI."""
    results = [audit_lead(lead) for lead in leads]
    summary = _build_summary(results)
    return results, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="O72 prod AI quality audit")
    parser.add_argument("--profile", default="site", choices=("site", "legacy"))
    parser.add_argument("--limit", type=int, default=150, help="main stratified sample size")
    parser.add_argument("--empty-l1-limit", type=int, default=25, help="extra empty task_summary rows")
    parser.add_argument("--judge", action="store_true", help="O72c: L2 LLM judge")
    parser.add_argument("--judge-limit", type=int, default=40)
    parser.add_argument("--judge-l1", action="store_true", help="O72c: L1 LLM judge")
    parser.add_argument("--judge-l1-limit", type=int, default=35)
    parser.add_argument(
        "--judge-l3",
        action="store_true",
        help="O89: L3 per-user reply judge (DB pairs + synthetic rephrase)",
    )
    parser.add_argument("--judge-l3-limit", type=int, default=25)
    parser.add_argument(
        "--judge-since",
        default="",
        help=f"O72e: judge only leads with created_at on/after date (default {_O72E_JUDGE_SINCE_DEFAULT} when --judge)",
    )
    parser.add_argument("--lead-ids", default="", help="comma lead_id for owner root-cause")
    parser.add_argument(
        "--source-like",
        default="",
        help="O115: filter sample/judge pool, e.g. tg:%% for TG-only pilot",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=_ROOT / "data" / "preprod_ai_prod_audit.json",
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=_ROOT / "data" / "preprod_ai_prod_audit_human.md",
    )
    parser.add_argument(
        "--judge-md-out",
        type=Path,
        default=_ROOT / "data" / "preprod_ai_prod_audit_judge.md",
    )
    args = parser.parse_args()
    apply_profile_argv(["--profile", args.profile])

    load_radar_env()
    cfg = load_config()
    db_url = (cfg.database_url or "").strip()
    if not db_url:
        print("DATABASE_URL не задан — нужен VPS Postgres (.env.site)", file=sys.stderr)
        return 2
    if "neon.tech" in db_url.lower():
        print(
            "DATABASE_URL указывает на Neon (архив). Prod БД — Postgres на VPS.\n"
            "  → docs/ops/PREPROD_ACCOUNTS.md § 1b (SSH tunnel :15432)\n"
            "  → или scripts/_owner_sync_preprod_token.py + audit на VPS",
            file=sys.stderr,
        )
        return 2

    owner_ids = [int(x.strip()) for x in args.lead_ids.split(",") if x.strip().isdigit()]
    src_sql, src_params = public_feed_source_sql()
    source_like_sql, source_like_params = _source_like_sql(args.source_like)
    need_judge = args.judge or args.judge_l1 or args.judge_l3
    judge_since: datetime | None = None
    since_sql = ""
    since_params: list[Any] = []
    if need_judge:
        try:
            judge_since = _parse_judge_since(args.judge_since)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        since_sql, since_params = _since_sql(judge_since)

    with psycopg.connect(db_url) as conn:
        main_sample = _stratified_sample(
            conn,
            n=args.limit,
            src_sql=src_sql,
            src_params=src_params,
            since_sql=since_sql,
            since_params=since_params,
            source_like_sql=source_like_sql,
            source_like_params=source_like_params,
        )
        empty_l1 = _fetch_empty_l1(
            conn,
            limit=args.empty_l1_limit,
            src_sql=src_sql,
            src_params=src_params,
            since_sql=since_sql,
            since_params=since_params,
            source_like_sql=source_like_sql,
            source_like_params=source_like_params,
        )
        owner_leads = _fetch_leads_by_ids(conn, owner_ids)

    seen: set[int] = set()
    merged: list[dict] = []
    for batch in (owner_leads, empty_l1, main_sample):
        for lead in batch:
            if lead["lead_id"] not in seen:
                seen.add(lead["lead_id"])
                merged.append(lead)

    results, summary = build_sample_and_audit(merged)

    owner_root: list[dict] = []
    if owner_ids:
        by_id = {r["lead_id"]: r for r in results}
        for lid in owner_ids:
            if lid in by_id:
                owner_root.append(by_id[lid])

    judge_l2_rows: list[dict] = []
    judge_l1_rows: list[dict] = []
    judge_l3_rows: list[dict] = []
    judge_l2_summary: dict[str, Any] | None = None
    judge_l1_summary: dict[str, Any] | None = None
    judge_l3_summary: dict[str, Any] | None = None
    if need_judge:
        if not cfg.ai_active:
            print("--judge: AI_ENABLED=0 или нет ключа OpenRouter", file=sys.stderr)
            return 2
        assert judge_since is not None
        fresh_results = _filter_fresh_for_judge(results, since=judge_since)
        print(f"Judge model: {_judge_model(cfg)}")
        print(
            f"Judge since: {judge_since.date().isoformat()} "
            f"({len(fresh_results)}/{len(results)} leads in sample)"
        )
        if args.judge:
            judge_l2_rows = _run_judge_l2(cfg, fresh_results, limit=args.judge_limit)
            judge_l2_summary = _judge_l2_summary(judge_l2_rows)
        if args.judge_l1:
            judge_l1_rows = _run_judge_l1(cfg, fresh_results, limit=args.judge_l1_limit)
            judge_l1_summary = _judge_l1_summary(judge_l1_rows)
        if args.judge_l3:
            with psycopg.connect(db_url) as conn:
                l3_targets = _build_l3_judge_targets(
                    cfg,
                    conn,
                    fresh_results,
                    limit=max(1, args.judge_l3_limit),
                )
            db_n = sum(1 for t in l3_targets if t.get("source") == "db")
            syn_n = sum(1 for t in l3_targets if t.get("source") == "synthetic")
            print(f"Judge L3 targets: {len(l3_targets)} (db={db_n}, synthetic={syn_n})")
            judge_l3_rows = _run_judge_l3(cfg, l3_targets)
            judge_l3_summary = _judge_l3_summary(judge_l3_rows)

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": args.profile,
        "judge_model": _judge_model(cfg) if need_judge else "",
        "judge_since": judge_since.date().isoformat() if judge_since else "",
        "sample": {
            "main_limit": args.limit,
            "empty_l1_limit": args.empty_l1_limit,
            "merged_total": len(merged),
        },
        "summary": summary,
        "results": results,
        "owner_lead_ids": owner_ids,
        "owner_root_cause": owner_root,
    }
    if judge_l2_summary is not None:
        report["judge_l2_summary"] = judge_l2_summary
        report["judge_l2_results"] = judge_l2_rows
    if judge_l1_summary is not None:
        report["judge_l1_summary"] = judge_l1_summary
        report["judge_l1_results"] = judge_l1_rows
    if judge_l3_summary is not None:
        report["judge_l3_summary"] = judge_l3_summary
        report["judge_l3_results"] = judge_l3_rows

    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    args.md_out.write_text(_render_human_md(report), encoding="utf-8")
    if need_judge:
        args.judge_md_out.write_text(
            _render_judge_md(
                report,
                results,
                judge_l2=judge_l2_rows or None,
                judge_l1=judge_l1_rows or None,
                judge_l3=judge_l3_rows or None,
            ),
            encoding="utf-8",
        )
        print(f"Judge md → {args.judge_md_out}")

    print(
        f"O72 audit: draft-only {summary['draft_only_pass']}/{summary['total']} "
        f"({summary['draft_only_pass_pct']}%) · tools {summary['tools_pass']}/{summary['total']} "
        f"({summary['tools_pass_pct']}%) → {args.json_out}"
    )
    print(f"Human md → {args.md_out}")
    if summary["accept_draft_95pct"]:
        print("Accept O72b: PASS (draft_only_pass ≥95%)")
    else:
        print("Accept O72b: FAIL (draft_only_pass <95%)")
    if summary["accept_85pct"]:
        print("Accept O72 combined: PASS (≥85% auto-pass)")
    else:
        print("Accept O72 combined: FAIL (<85% auto-pass)")

    if judge_l2_summary is not None:
        print(
            f"Judge L2: combined={judge_l2_summary['avg_combined_3']} "
            f"univ={judge_l2_summary['avg_universal_helpful']} "
            f"send={judge_l2_summary['send_as_is_pct']}% "
            f"({'PASS' if judge_l2_summary['accept_l2'] else 'FAIL'}) · "
            f"balanced O200={('PASS' if judge_l2_summary.get('accept_l2_balanced') else 'FAIL')}"
        )
    if judge_l1_summary is not None:
        print(
            f"Judge L1: ctx={judge_l1_summary['avg_context']} "
            f"usable={judge_l1_summary['l1_usable_pct']}% "
            f"cx={judge_l1_summary.get('avg_complexity_rating', 0)} "
            f"cx_ok={judge_l1_summary.get('complexity_ok_pct', 0)}% "
            f"({'PASS' if judge_l1_summary['accept_l1'] else 'FAIL'}) "
            f"complexity={'PASS' if judge_l1_summary.get('accept_complexity') else 'FAIL'}"
        )
    if judge_l3_summary is not None:
        print(
            f"Judge L3: combined={judge_l3_summary['avg_combined_3']} "
            f"uniq={judge_l3_summary['avg_uniqueness']} "
            f"send={judge_l3_summary['send_as_is_pct']}% "
            f"leak={judge_l3_summary['forbidden_leak_pct']}% "
            f"({'PASS' if judge_l3_summary['accept_l3'] else 'FAIL'})"
        )

    ok = summary["accept_draft_95pct"]
    if judge_l2_summary is not None:
        ok = ok and judge_l2_summary["accept_l2"]
    if judge_l1_summary is not None:
        ok = ok and judge_l1_summary["accept_l1"]
        ok = ok and judge_l1_summary.get("accept_complexity", False)
    if judge_l3_summary is not None:
        ok = ok and judge_l3_summary["accept_l3"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
