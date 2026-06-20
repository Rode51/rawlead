"""O171: truth ladder for /ops/ summary — process→fetch→parsed→new→L1→visible."""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from exchange_health import (
    _last_fetch_ok,
    _ok_after_error,
    _parse_ts_epoch,
    _parsed_cards,
    load_all_health,
    source_display_name,
)
from radar_cycle_log import CycleSummary, SourceCycleStats, load_cycle_summary

# Neon «сегодня» = календарный день MSK (tooltip в meta/footer).
_OPS_TZ = "Europe/Moscow"

StepStatus = Literal["ok", "warn", "bad", "na"]

FUNNEL_SOURCES: tuple[str, ...] = ("fl", "kwork", "youdo", "tg")
STEP_ORDER: tuple[str, ...] = ("process", "fetch", "parsed", "new", "l1", "visible")

PARSED_OK = 5
FL_DC_PARSED_INGEST_OK = 25
PROCESS_OK_MIN = 15
PROCESS_WARN_MIN = 20
_STALE_CYCLE_MIN = 30
_CYCLE_HEADER_RE = re.compile(r"── Цикл (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) ──")
L1_OK = 50
L1_WARN = 200
VISIBLE_OK = 10

_SOURCE_PROXY_GROUP: dict[str, str] = {
    "fl": "exchange-fl",
    "kwork": "exchange-kwork",
    "youdo": "exchange-pool",
    "tg": "tg-bot",
}


@dataclass(frozen=True)
class SourceInput:
    source_id: str
    health: dict[str, Any]
    cycle: SourceCycleStats | None
    fetch_failed: bool
    fetch_retries: int
    parsed_threshold: int = PARSED_OK
    new_1h: int = 0
    new_today: int = 0
    new_24h: int = 0
    visible_24h: int = 0
    l1_backlog: int = 0
    cycle_age_min: int | None = None
    lag_min: int | None = None
    empty_exchange: bool = False


def classify_process_step(*, cycle_age_min: int | None, paused: bool = False) -> StepStatus:
    if paused:
        return "warn"
    if cycle_age_min is None:
        return "bad"
    if cycle_age_min < PROCESS_OK_MIN:
        return "ok"
    if cycle_age_min <= PROCESS_WARN_MIN:
        return "warn"
    return "bad"


def classify_fetch_step(
    *,
    fetch_failed: bool,
    retry_count: int,
    recovered: bool = False,
    soft_proxy_exhausted: bool = False,
) -> StepStatus:
    if soft_proxy_exhausted and not fetch_failed:
        return "warn"
    if recovered and not fetch_failed and retry_count <= 0:
        return "ok"
    if retry_count >= 3 or (fetch_failed and retry_count >= 3):
        return "bad"
    if fetch_failed or retry_count >= 1:
        return "warn"
    return "ok"


def classify_parsed_step(
    *,
    parsed: int,
    fetch_ok: bool,
    threshold: int = PARSED_OK,
    empty_exchange: bool = False,
) -> StepStatus:
    if parsed < 0:
        return "na"
    if parsed >= threshold:
        return "ok"
    if parsed >= 1:
        return "warn"
    if empty_exchange and fetch_ok:
        return "warn"
    if fetch_ok:
        return "bad"
    return "warn"


def classify_new_step(
    *,
    new_1h: int,
    new_today: int = 0,
    parsed: int,
    empty_exchange: bool = False,
) -> StepStatus:
    if empty_exchange:
        return "na"
    if new_1h > 0 or new_today > 0:
        return "ok"
    if parsed > 0:
        return "warn"
    return "na"


def classify_l1_step(*, backlog: int) -> StepStatus:
    if backlog < 0:
        return "na"
    if backlog < L1_OK:
        return "ok"
    if backlog <= L1_WARN:
        return "warn"
    return "bad"


def classify_visible_step(
    *,
    visible_24h: int,
    parsed: int,
    empty_exchange: bool = False,
) -> StepStatus:
    if empty_exchange:
        return "na"
    if visible_24h >= VISIBLE_OK:
        return "ok"
    if visible_24h >= 1:
        return "warn"
    if parsed > 0:
        return "bad"
    return "na"


def aggregate_lamp(*statuses: StepStatus) -> StepStatus:
    order = {"bad": 3, "warn": 2, "ok": 1, "na": 0}
    relevant = [s for s in statuses if s != "na"]
    if not relevant:
        return "warn"
    return max(relevant, key=lambda s: order[s])


def _step_label(step: str) -> str:
    return {
        "process": "процесс",
        "fetch": "загрузка",
        "parsed": "разбор",
        "new": "новые",
        "l1": "ИИ",
        "visible": "лента",
    }.get(step, step)


def _step_tooltip(step: str, status: StepStatus, ctx: dict[str, Any]) -> str:
    if step == "process":
        age = ctx.get("cycle_age_min")
        if age is None:
            return "Радар без цикла"
        return f"Радар жив · цикл {age} мин назад"
    if step == "fetch":
        retries = int(ctx.get("fetch_retries") or 0)
        if status == "bad":
            return f"timeout × {max(retries, 3)}"
        if retries:
            return f"HTTP · {retries} попытка"
        return "HTTP 200 · 1 попытка"
    if step == "parsed":
        parsed = int(ctx.get("parsed") or 0)
        return f"HTML→карточки: {parsed} за цикл"
    if step == "new":
        new_1h = int(ctx.get("new_1h") or 0)
        new_today = int(ctx.get("new_today") or 0)
        new_24h = int(ctx.get("new_24h") or 0)
        if new_1h or new_today or new_24h:
            return (
                f"Вставки в Neon: {new_1h} за 1 ч · {new_today} сегодня ({_OPS_TZ}) · {new_24h} за 24 ч"
            )
        if ctx.get("empty_exchange"):
            return "0 вставок — биржа пустая"
        return "0 вставок в Neon за 1 ч"
    if step == "l1":
        backlog = int(ctx.get("l1_backlog") or 0)
        return f"очередь {backlog}"
    if step == "visible":
        visible = int(ctx.get("visible_24h") or 0)
        return f"+{visible} за 24 ч"
    return ""


def _fl_soft_dc_exhausted(parsed: int, fetch_failed: bool) -> bool:
    """DC tier pool_exhausted while ingest still parses — warn, not red (O210)."""
    if fetch_failed or parsed < FL_DC_PARSED_INGEST_OK:
        return False
    try:
        from exchange_proxy import fl_dc_tier_exhausted

        return fl_dc_tier_exhausted()
    except Exception:
        return False


def _fl_recent_pool_exhausted(log_path: Path | None, *, tail: int = 400) -> bool:
    """Last fetch:fl line shows pool_exhausted (O215 — parsed=0 must stay red)."""
    if log_path is None or not log_path.is_file():
        return False
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False
    for line in reversed(lines[-tail:]):
        low = line.lower()
        if "fetch:fl" not in low:
            continue
        return "pool_exhausted" in low or "alive=0/" in low
    return False


def _youdo_recent_parsed_zero_cycles(log_path: Path | None, *, n: int = 3, tail: int = 1200) -> bool:
    """Last n YouDo listing cycles all parsed=0 (O262f ops lamp)."""
    if log_path is None or not log_path.is_file() or n < 1:
        return False
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False
    hits: list[int] = []
    for line in reversed(lines[-tail:]):
        low = line.lower()
        if "youdo:trace stage=fetch_end" not in low and "listing:youdo" not in low:
            continue
        m = re.search(r"parsed=(\d+)", line, re.I)
        if m:
            hits.append(int(m.group(1)))
        elif "listing:youdo" in low and "parsed=" in low:
            m2 = re.search(r"parsed=(\d+)", line, re.I)
            if m2:
                hits.append(int(m2.group(1)))
        if len(hits) >= n:
            break
    if len(hits) < n:
        return False
    return all(p == 0 for p in hits[:n])


def _youdo_last_fetch_kind_ok(log_path: Path | None, *, tail: int = 800) -> bool:
    """Last youdo:trace fetch_end has kind=ok (O262f)."""
    if log_path is None or not log_path.is_file():
        return False
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False
    for line in reversed(lines[-tail:]):
        if "youdo:trace stage=fetch_end" not in line.lower():
            continue
        low = line.lower()
        if "kind=ok" in low:
            return True
        if "kind=" in low:
            return False
    return False


def _apply_youdo_ops_lamp(row: dict[str, Any], *, lag_min: int | None, log_path: Path | None) -> None:
    """O262f: red when lag>60 or 3× parsed=0; green only kind=ok + parsed>0."""
    parsed_now = int((row.get("meta") or {}).get("parsed") or 0)
    lag_bad = lag_min is not None and lag_min > 60
    zero_streak = _youdo_recent_parsed_zero_cycles(log_path)
    kind_ok = _youdo_last_fetch_kind_ok(log_path)
    if lag_bad or zero_streak:
        row["lamp"] = "bad"
        if lag_bad:
            row["meta"]["youdo_lag_min"] = lag_min
        if zero_streak:
            row["meta"]["youdo_parsed_zero_streak"] = 3
        for step_row in row.get("steps") or []:
            if step_row.get("id") in ("fetch", "parsed", "new"):
                step_row["status"] = "bad"
            step_row["is_break"] = step_row.get("id") == "parsed"
        return
    if parsed_now > 0 and kind_ok:
        row["lamp"] = "ok"
        for step_row in row.get("steps") or []:
            if step_row.get("id") in ("fetch", "parsed"):
                step_row["status"] = "ok"
                step_row["is_break"] = False
    elif parsed_now == 0 or not kind_ok:
        row["lamp"] = "bad"
        for step_row in row.get("steps") or []:
            if step_row.get("id") in ("fetch", "parsed"):
                step_row["status"] = "bad"
            step_row["is_break"] = step_row.get("id") == "parsed"


def build_source_funnel(inp: SourceInput) -> dict[str, Any]:
    health = inp.health
    parsed = _parsed_cards(health)
    if inp.cycle is not None and inp.cycle.parsed_cards >= 0:
        parsed = inp.cycle.parsed_cards
    fetch_ok = _last_fetch_ok(health) and not inp.fetch_failed
    recovered = _ok_after_error(health)
    empty = inp.empty_exchange or (parsed == 0 and fetch_ok and inp.source_id in ("youdo",))

    ctx = {
        "parsed": parsed,
        "new_1h": inp.new_1h,
        "new_today": inp.new_today,
        "new_24h": inp.new_24h,
        "visible_24h": inp.visible_24h,
        "l1_backlog": inp.l1_backlog,
        "fetch_retries": inp.fetch_retries,
        "cycle_age_min": inp.cycle_age_min,
        "empty_exchange": empty,
    }

    soft_dc = (
        _fl_soft_dc_exhausted(parsed, inp.fetch_failed)
        if inp.source_id == "fl"
        else False
    )

    steps_map: dict[str, StepStatus] = {
        "process": classify_process_step(cycle_age_min=inp.cycle_age_min),
        "fetch": classify_fetch_step(
            fetch_failed=inp.fetch_failed,
            retry_count=0 if soft_dc else inp.fetch_retries,
            recovered=recovered,
            soft_proxy_exhausted=soft_dc,
        ),
        "parsed": classify_parsed_step(
            parsed=parsed,
            fetch_ok=fetch_ok,
            threshold=inp.parsed_threshold,
            empty_exchange=empty,
        ),
        "new": classify_new_step(
            new_1h=inp.new_1h,
            new_today=inp.new_today,
            parsed=parsed,
            empty_exchange=empty,
        ),
        "l1": classify_l1_step(backlog=inp.l1_backlog),
        "visible": classify_visible_step(
            visible_24h=inp.visible_24h,
            parsed=parsed,
            empty_exchange=empty,
        ),
    }

    steps = [
        {
            "id": step,
            "status": steps_map[step],
            "label": _step_label(step),
            "tooltip": _step_tooltip(step, steps_map[step], ctx),
            "is_break": False,
        }
        for step in STEP_ORDER
    ]
    break_idx = next((i for i, s in enumerate(steps) if s["status"] == "bad"), None)
    if break_idx is not None:
        steps[break_idx]["is_break"] = True

    lamp = aggregate_lamp(*steps_map.values())
    if (
        inp.source_id == "youdo"
        and inp.visible_24h > 0
        and lamp == "bad"
        and steps_map["process"] != "bad"
        and steps_map["fetch"] != "bad"
    ):
        lamp = "warn"
        for step_row in steps:
            if step_row["status"] == "bad" and step_row["id"] in ("parsed", "new", "visible", "l1"):
                step_row["status"] = "warn"
                step_row["is_break"] = False
                steps_map[step_row["id"]] = "warn"
    headline = _source_headline(inp.source_id, lamp, steps_map, ctx)
    muted = "Биржа пустая — это норма" if empty and parsed == 0 else None

    return {
        "source_id": inp.source_id,
        "name": source_display_name(inp.source_id),
        "lamp": lamp,
        "headline": headline,
        "steps": steps,
        "meta": {
            "parsed": parsed if parsed >= 0 else None,
            "parsed_title": "разбор HTML→карточки за последний цикл радара",
            "new": inp.new_1h,
            "new_today": inp.new_today,
            "new_24h": inp.new_24h,
            "visible_24h": inp.visible_24h,
            "lag_min": inp.lag_min,
        },
        "muted_note": muted,
        "empty_exchange": empty,
    }


def _source_headline(
    source_id: str,
    lamp: StepStatus,
    steps: dict[str, StepStatus],
    ctx: dict[str, Any],
) -> str:
    visible = int(ctx.get("visible_24h") or 0)
    if visible > 0 and lamp == "ok":
        return f"visible +{visible} за 24ч"
    if ctx.get("empty_exchange") and steps.get("parsed") in ("warn", "bad"):
        return "parsed 0 · fetch ок"
    if steps.get("new") == "warn":
        return "нет новых 2 ч"
    icons = {"ok": "🟢", "warn": "🟡", "bad": "🔴", "na": "—"}
    return f"{icons.get(lamp, '—')} {source_display_name(source_id)}"


def _action_for_break(source_id: str, step: str) -> dict[str, str] | None:
    if step == "fetch":
        group = _SOURCE_PROXY_GROUP.get(source_id, "exchange-pool")
        labels = {
            "fl": "Проверить прокси FL",
            "kwork": "Проверить прокси Kwork",
            "youdo": "Проверить прокси YouDo",
            "tg": "Открыть прокси TG",
        }
        return {
            "label": labels.get(source_id, "Проверить прокси"),
            "scroll_to": "ops-proxies",
            "group": group,
        }
    if step in ("process",):
        return {
            "label": "Перезапустить радар",
            "target": "radar",
            "action": "restart",
        }
    if step in ("l1", "visible"):
        return {"label": "Открыть ленту", "scroll_to": "ops-leads"}
    if step == "parsed" and source_id != "tg":
        return {
            "label": f"Проверить {source_display_name(source_id)}",
            "scroll_to": "ops-exchanges",
        }
    if source_id == "tg":
        return {"label": "Подробнее TG", "scroll_to": "ops-tg"}
    return None


def build_diagnosis(sources: list[dict[str, Any]]) -> dict[str, Any] | None:
    for src in sources:
        sid = str(src.get("source_id") or "")
        steps = {s["id"]: s["status"] for s in src.get("steps") or []}
        for step in STEP_ORDER:
            if steps.get(step) == "bad":
                name = src.get("name") or sid
                action = _action_for_break(sid, step)
                return {
                    "level": "bad",
                    "text": f"Обрыв на {name} · { _step_label(step)}",
                    "action": action,
                }
        parsed = int((src.get("meta") or {}).get("parsed") or 0)
        visible = int((src.get("meta") or {}).get("visible") or 0)
        if parsed > 0 and visible == 0 and steps.get("visible") == "bad":
            action = _action_for_break(sid, "visible")
            return {
                "level": "bad",
                "text": f"{src.get('name')}: parsed>0, visible 0 за 24ч",
                "action": action,
            }
    return None


def count_consecutive_fetch_fails(source: str, log_path: Path | None = None) -> int:
    if log_path is None:
        log_path = _resolve_log_path()
    if log_path is None or not log_path.is_file():
        return 0
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return 0
    src = source.strip().lower()
    count = 0
    for line in reversed(lines[-800:]):
        low = line.lower()
        if f"fetch:{src}" not in low and f"health:{src}" not in low:
            continue
        if "status=ok" in low or " parsed=" in low and "parsed=0" not in low:
            if "err" not in low and "fail" not in low and "timeout" not in low:
                break
        if any(x in low for x in ("err", "fail", "timeout", "http 4", "http 5", "status=fail")):
            if "pool_exhausted" in low and f"fetch:{src}" in low:
                continue
            count += 1
        elif f"listing:{src}" in low and "parsed=" in low:
            break
    return count


def _resolve_log_path() -> Path | None:
    raw = os.environ.get("RADAR_LOG_PATH", "").strip()
    root = Path(__file__).resolve().parent.parent
    if raw:
        p = Path(raw)
        if not p.is_absolute():
            p = root / p
        return p if p.is_file() else None
    for candidate in ("data/radar_site.log", "data/radar.log"):
        p = root / candidate
        if p.is_file():
            return p
    return None


def _cycle_ts_from_log(log_path: Path, *, tail_lines: int = 500) -> float | None:
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in reversed(text.splitlines()[-tail_lines:]):
        m = _CYCLE_HEADER_RE.search(line)
        if m:
            return _parse_ts_epoch(m.group(1))
    return None


def _cycle_age_min(
    summary: CycleSummary | None,
    now: float | None = None,
    log_path: Path | None = None,
) -> int | None:
    ref = now if now is not None else time.time()
    age: int | None = None
    if summary is not None and summary.ts:
        epoch = _parse_ts_epoch(summary.ts)
        if epoch is not None:
            age = max(0, int((ref - epoch) // 60))
    if age is None or age > _STALE_CYCLE_MIN:
        path = log_path if log_path is not None else _resolve_log_path()
        if path is not None:
            log_epoch = _cycle_ts_from_log(path)
            if log_epoch is not None:
                log_age = max(0, int((ref - log_epoch) // 60))
                if age is None or log_age < age:
                    age = log_age
    return age


def _soften_fl_residential_lamp(row: dict[str, Any]) -> None:
    """Residential fallback with healthy parse — warn, not red (O214)."""
    if row.get("lamp") != "bad":
        return
    parsed = int(row.get("meta", {}).get("parsed") or 0)
    if parsed < FL_DC_PARSED_INGEST_OK:
        return
    if row.get("meta", {}).get("fl_pool_exhausted"):
        return
    row["lamp"] = "warn"
    for step_row in row.get("steps") or []:
        if step_row.get("status") == "bad":
            step_row["status"] = "warn"
            step_row["is_break"] = False


def _lead_counts_by_source(database_url: str) -> dict[str, dict[str, int]]:
    url = database_url.strip()
    if not url:
        return {}
    try:
        import psycopg

        with psycopg.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT source,
                           COUNT(*) FILTER (
                             WHERE created_at >= NOW() - INTERVAL '1 hour'
                           )::int AS new_1h,
                           COUNT(*) FILTER (
                             WHERE created_at >= NOW() - INTERVAL '24 hours'
                           )::int AS new_24h,
                           COUNT(*) FILTER (
                             WHERE created_at >= (
                               date_trunc('day', NOW() AT TIME ZONE %s) AT TIME ZONE %s
                             )
                           )::int AS new_today,
                           COUNT(*) FILTER (
                             WHERE is_visible = TRUE
                               AND created_at >= NOW() - INTERVAL '24 hours'
                           )::int AS visible_24h
                    FROM leads
                    WHERE source = ANY(%s)
                    GROUP BY source
                    """,
                    (_OPS_TZ, _OPS_TZ, list(FUNNEL_SOURCES)),
                )
                out: dict[str, dict[str, int]] = {}
                for source, new_1h, new_24h, new_today, visible_24h in cur.fetchall():
                    out[str(source)] = {
                        "new_1h": int(new_1h or 0),
                        "new_24h": int(new_24h or 0),
                        "new_today": int(new_today or 0),
                        "visible_24h": int(visible_24h or 0),
                    }
                return out
    except Exception:
        return {}


def _l1_backlog_total(cfg) -> int | None:
    try:
        from radar_status import _query_l1_backlog

        return _query_l1_backlog(cfg)
    except Exception:
        return None


def _l1_backlog_by_source(cfg) -> dict[str, int]:
    try:
        from radar_status import _query_l1_backlog_by_source

        return _query_l1_backlog_by_source(cfg, hours=48)
    except Exception:
        return {"fl": 0, "kwork": 0, "tg": 0}


def _ingest_metrics_snapshot(database_url: str) -> dict[str, dict[str, int | float | str]]:
    url = database_url.strip()
    if not url:
        return {}
    try:
        import psycopg

        with psycopg.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    WITH base AS (
                      SELECT
                        CASE
                          WHEN source IN ('fl', 'freelance_ru', 'freelancejob') THEN 'fl'
                          WHEN source = 'kwork' THEN 'kwork'
                          WHEN source = 'tg' THEN 'tg'
                          ELSE source
                        END AS source_bucket,
                        created_at,
                        l1_completed_at,
                        source_published_at
                      FROM leads
                      WHERE created_at >= NOW() - INTERVAL '48 hours'
                    )
                    SELECT
                      source_bucket,
                      EXTRACT(EPOCH FROM (NOW() - MAX(created_at)))::int AS last_insert_gap_sec,
                      COUNT(*) FILTER (
                        WHERE l1_completed_at IS NULL
                          AND created_at >= NOW() - INTERVAL '48 hours'
                      )::int AS backlog
                    FROM base
                    WHERE source_bucket IN ('fl', 'kwork', 'tg', 'youdo')
                    GROUP BY source_bucket
                    """
                )
                out: dict[str, dict[str, int | float | str]] = {}
                for row in cur.fetchall():
                    bucket = str(row[0] or "")
                    if bucket:
                        out[bucket] = {
                            "last_insert_gap_sec": int(row[1] or 0),
                            "backlog": int(row[2] or 0),
                        }
                return out
    except Exception:
        return {}


def build_funnel_payload(
    storage,
    *,
    database_url: str = "",
    now: float | None = None,
) -> dict[str, Any]:
    from config import load_radar_env
    from storage import ProjectStorage

    if not isinstance(storage, ProjectStorage):
        storage = ProjectStorage(storage)

    load_radar_env()
    from config import load_config

    cfg = load_config()
    summary = load_cycle_summary(storage)
    all_health = load_all_health(storage)
    lead_counts = _lead_counts_by_source(database_url)
    ingest = _ingest_metrics_snapshot(database_url)
    log_path = _resolve_log_path()

    cycle_age = _cycle_age_min(summary, now=now, log_path=log_path)
    paused = storage.is_radar_paused()
    l1_total = _l1_backlog_total(cfg)
    l1_by_src = _l1_backlog_by_source(cfg)

    sources_out: list[dict[str, Any]] = []
    for sid in FUNNEL_SOURCES:
        health = all_health.get(sid) or {}
        st = summary.sources.get(sid) if summary else None
        fetch_failed = bool(st and st.fetch_error)
        retries = count_consecutive_fetch_fails(sid, log_path)
        if fetch_failed and retries < 1:
            retries = 1
        ing = ingest.get(sid) or {}
        lag_min = int(int(ing.get("last_insert_gap_sec", 0) or 0) // 60) or None
        counts = lead_counts.get(sid, {})
        inp = SourceInput(
            source_id=sid,
            health=health,
            cycle=st,
            fetch_failed=fetch_failed,
            fetch_retries=retries,
            new_1h=int(counts.get("new_1h", 0)),
            new_today=int(counts.get("new_today", 0)),
            new_24h=int(counts.get("new_24h", 0)),
            visible_24h=int(counts.get("visible_24h", 0)),
            l1_backlog=int(l1_by_src.get(sid, ing.get("backlog", 0) or 0)),
            cycle_age_min=cycle_age,
            lag_min=lag_min,
            empty_exchange=sid == "youdo" and _parsed_cards(health) == 0 and _last_fetch_ok(health),
        )
        row = build_source_funnel(inp)
        row["meta"]["visible"] = inp.visible_24h
        if sid == "fl":
            parsed_now = int(row.get("meta", {}).get("parsed") or 0)
            pool_dead = parsed_now == 0 and _fl_recent_pool_exhausted(log_path)
            if pool_dead:
                row["meta"]["fl_pool_exhausted"] = True
                row["lamp"] = "bad"
                for step_row in row.get("steps") or []:
                    if step_row.get("id") in ("fetch", "parsed"):
                        step_row["status"] = "bad"
                    step_row["is_break"] = step_row.get("id") == "parsed"
            else:
                try:
                    from radar_status import apply_fl_antibot_soft_ops_row

                    apply_fl_antibot_soft_ops_row(row, storage, log_path)
                except Exception:
                    pass
                try:
                    from exchange_proxy import fl_on_residential_tier, fl_residential_counts

                    if fl_on_residential_tier():
                        alive, total = fl_residential_counts()
                        row["meta"]["fl_tier"] = "residential"
                        row["meta"]["fl_res_alive"] = f"{alive}/{total}"
                        _soften_fl_residential_lamp(row)
                except Exception:
                    pass
        elif sid == "youdo":
            try:
                _apply_youdo_ops_lamp(row, lag_min=lag_min, log_path=log_path)
            except Exception:
                pass
        sources_out.append(row)

    radar_lamp = classify_process_step(cycle_age_min=cycle_age, paused=paused)
    lamps = {
        "radar": {
            "status": radar_lamp,
            "label": f"Радар {cycle_age}м" if cycle_age is not None else "Радар",
        },
    }
    for src in sources_out:
        lamps[src["source_id"]] = {
            "status": src["lamp"],
            "label": source_display_name(src["source_id"]),
        }

    l1_status = classify_l1_step(backlog=int(l1_total or 0))
    diagnosis = build_diagnosis(sources_out)

    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "cycle_age_min": cycle_age,
        "lamps": lamps,
        "l1": {
            "status": l1_status,
            "queue": int(l1_total or 0),
            "label": f"очередь {int(l1_total or 0)}",
        },
        "diagnosis": diagnosis,
        "sources": sources_out,
    }


def _load_join_state() -> dict[str, Any]:
    try:
        from config import load_tg_join_config

        cfg = load_tg_join_config()
        if not cfg.state_path.is_file():
            return {}
        data = json.loads(cfg.state_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _join_queue_counts() -> dict[str, int]:
    try:
        from tg_join_lib import read_queue_csv

        _, rows = read_queue_csv()
        counts = {"done": 0, "pending": 0, "fail": 0}
        for row in rows:
            st = row.get("status", "").strip().lower()
            if st in counts:
                counts[st] += 1
        return counts
    except Exception:
        return {"done": 0, "pending": 0, "fail": 0}


def _acc_strikes(acc_state: dict[str, Any]) -> int:
    history = acc_state.get("history")
    if not isinstance(history, list):
        return 0
    strikes = 0
    for item in reversed(history):
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "").strip().lower()
        if status == "fail":
            strikes += 1
        elif status == "done":
            break
    return min(strikes, 3)


TG_LISTEN_TOOLTIP = (
    "Сейчас в эфире / Вступили / После фильтра — три числа. "
    "Почему меньше слушаем, чем вступили — см. фильтр; после O190-auto должны совпадать."
)
TG_MSGS_TOOLTIP = (
    "Сессия = с последнего рестарта радара · Всего = накопительно"
)


def tg_msgs_line_ru(
    *,
    session: int,
    total: int,
    new_count: int = 0,
    notified_count: int = 0,
    neon24h: int = 0,
) -> str:
    parts: list[str] = []
    if session or total:
        parts.append(f"+{session} за сессию")
        if total:
            parts.append(f"всего {total}")
    if new_count:
        parts.append(f"new {new_count}")
    if notified_count:
        parts.append(f"увед {notified_count}")
    if neon24h:
        parts.append(f"neon24h {neon24h}")
    return " · ".join(parts) if parts else "—"


def _tg_listen_file_counts(account: str) -> tuple[int, int]:
    from config import parse_telethon_chat_ids, telethon_chat_ids_path_for_account
    from public_feed import filter_listen_chat_ids

    path = telethon_chat_ids_path_for_account(account)
    try:
        raw_ids = parse_telethon_chat_ids(str(path))
    except (OSError, ValueError):
        raw_ids = []
    filtered = filter_listen_chat_ids(raw_ids)
    return len(raw_ids), len(filtered)


def tg_listen_line_ru(peers: int, file_n: int, filt_n: int) -> str:
    return f"Слушают {peers} · вступили {file_n} · после фильтра {filt_n}"


def tg_join_label_ru(
    *,
    pending: int,
    join_active: bool,
    ready: bool,
) -> tuple[str, str]:
    if pending <= 0 and ready:
        return "done", "готово"
    if join_active:
        return "active", f"идёт ({pending})"
    if pending > 0:
        return "pending", f"ждут {pending}"
    return "done", "готово"


def tg_queue_hint_ru(
    done: int,
    pending: int,
    fail: int,
    max_per_hour: int,
) -> str:
    return (
        f"Очередь: {done} готово · {pending} ждут · {fail} ошибка · "
        f"лимит {max_per_hour}/ч"
    )


def _tg_last_err_is_auth(last_err: str) -> bool:
    s = (last_err or "").strip().lower()
    if not s:
        return False
    if s.startswith("get_me:"):
        return True
    for needle in ("auth", "session", "авториз", "unauthorized", "401", "not authorized"):
        if needle in s:
            return True
    return False


def _tg_lamp_reason_ru(
    *,
    state: str,
    last_err: str,
    strikes_n: int,
    peers: int,
) -> str:
    if _tg_last_err_is_auth(last_err):
        return "Нужна переавторизация"
    if strikes_n >= 3 and state != "listening":
        return "3 ошибки join"
    if strikes_n >= 3:
        return f"3 ошибки join · слушает {peers} чатов"
    if strikes_n >= 2:
        return f"{strikes_n} ошибки join"
    if state == "listening":
        return f"Слушает {peers} чатов"
    if state == "join_pending":
        return "Очередь join"
    if state == "join_active":
        return "Вступает в чаты"
    if last_err:
        return last_err[:120]
    return "OK"


def _tg_acc_row(
    storage,
    account: str,
    join_state: dict,
    pending: int,
    *,
    neon_tg: dict[str, int] | None = None,
) -> dict[str, Any]:
    from config import load_tg_monitor_config
    from radar_status import _int_setting, _tg_key

    try:
        tg_cfg = load_tg_monitor_config()
        acfg = next((a for a in tg_cfg.accounts if a.account == account), None)
    except SystemExit:
        acfg = None

    listen = _int_setting(storage, _tg_key(account, "chats_listen"))
    in_file = _int_setting(storage, _tg_key(account, "chats_file"))
    after_filter = _int_setting(storage, _tg_key(account, "chats_filter"))
    file_live, filter_live = _tg_listen_file_counts(account)
    if file_live:
        in_file = file_live
    if filter_live:
        after_filter = filter_live
    peers = max(after_filter, listen, filter_live or 0)
    msgs = _int_setting(storage, _tg_key(account, "msgs"))
    msgs_total = _int_setting(storage, _tg_key(account, "msgs_total"))
    new_msgs = _int_setting(storage, _tg_key(account, "new"))
    notified = _int_setting(storage, _tg_key(account, "notified"))
    neon24h = int((neon_tg or {}).get("visible_24h") or 0)
    ready = _int_setting(storage, _tg_key(account, "ready")) > 0
    last_err = storage.get_setting(_tg_key(account, "last_err"), "").strip()
    acc_state = join_state.get(account) if isinstance(join_state.get(account), dict) else {}
    strikes_n = _acc_strikes(acc_state)
    strikes_level: StepStatus = "ok"
    if strikes_n >= 3:
        strikes_level = "bad"
    elif strikes_n >= 2:
        strikes_level = "warn"

    join_active = int(acc_state.get("joins_this_hour") or 0) > 0 and pending > 0
    auth_err = _tg_last_err_is_auth(last_err)
    if auth_err:
        state = "auth_error"
        state_label = "Ошибка авторизации"
    elif pending > 0 and not ready:
        state = "join_pending"
        state_label = f"В очереди {pending}"
    elif join_active:
        state = "join_active"
        state_label = "Вступает в чаты…"
    elif ready and peers > 0:
        state = "listening"
        state_label = tg_listen_line_ru(peers, in_file, after_filter)
    elif ready:
        state = "ready"
        state_label = "Готов · слушает"
    else:
        state = "join_queue"
        state_label = "Очередь join"

    join_status, join_label = tg_join_label_ru(
        pending=pending,
        join_active=join_active,
        ready=ready,
    )

    listen_line = tg_listen_line_ru(peers, in_file, after_filter)
    lamp_reason_ru = _tg_lamp_reason_ru(
        state=state,
        last_err=last_err,
        strikes_n=strikes_n,
        peers=peers,
    )

    lamp: StepStatus = "ok"
    if auth_err:
        lamp = "bad"
    elif state in ("join_pending", "join_queue"):
        lamp = "warn"
    elif state == "listening":
        if strikes_level == "warn":
            lamp = "warn"
    elif strikes_level == "bad":
        lamp = "bad"
    elif strikes_level == "warn" or state in ("join_active",):
        lamp = "warn"

    return {
        "id": account,
        "state": state,
        "state_label": state_label,
        "lamp": lamp,
        "lamp_reason_ru": lamp_reason_ru,
        "listen_count": peers,
        "file_count": in_file,
        "filter_count": after_filter,
        "peers_count": peers,
        "listen_line": listen_line,
        "listen_title": TG_LISTEN_TOOLTIP,
        "msgs_count": msgs,
        "msgs_total": msgs_total,
        "msgs_line": tg_msgs_line_ru(
            session=msgs,
            total=msgs_total,
            new_count=new_msgs,
            notified_count=notified,
            neon24h=neon24h,
        ),
        "msgs_title": TG_MSGS_TOOLTIP,
        "new_count": new_msgs,
        "notified_count": notified,
        "neon24h": neon24h,
        "join_status": join_status,
        "join_label": join_label,
        "strikes": f"{strikes_n}/3",
        "strikes_level": strikes_level,
        "has_chats": bool(acfg and acfg.chat_ids),
    }


def build_tg_payload(storage) -> dict[str, Any]:
    from config import load_tg_join_config, load_tg_monitor_config
    from radar_status import _pending_join_by_account
    from storage import ProjectStorage
    from tg_proxy_pool import status_summary

    if not isinstance(storage, ProjectStorage):
        storage = ProjectStorage(storage)

    join_cfg = load_tg_join_config()
    join_state = _load_join_state()
    queue = _join_queue_counts()
    pending_by_acc = _pending_join_by_account(join_cfg.queue_csv)
    neon_tg: dict[str, int] = {}
    try:
        from config import load_config

        neon_tg = _lead_counts_by_source((load_config().database_url or "").strip()).get(
            "tg",
            {},
        )
    except Exception:
        neon_tg = {}

    try:
        tg_cfg = load_tg_monitor_config()
        accounts = tuple(a.account for a in tg_cfg.accounts)
    except SystemExit:
        accounts = ("acc1", "acc2", "acc3")

    acc_rows = [
        _tg_acc_row(
            storage,
            acc,
            join_state,
            pending_by_acc.get(acc, 0),
            neon_tg=neon_tg,
        )
        for acc in accounts
    ]

    pool = status_summary()
    total = int(pool.get("total") or pool.get("pool_size") or 0)
    alive = int(pool.get("alive") or 0)
    free = max(0, alive - 1) if alive else 0

    try:
        from proxy_ops import collect_proxies_payload

        auto = bool((collect_proxies_payload() or {}).get("auto_failover", True))
    except Exception:
        auto = True

    last_switch = ""
    pool_path = Path(os.getenv("TG_PROXY_POOL_JSON", "data/tg_proxy_pool.json").strip())
    if not pool_path.is_absolute():
        pool_path = Path(__file__).resolve().parent.parent / pool_path
    if pool_path.is_file():
        try:
            raw = json.loads(pool_path.read_text(encoding="utf-8"))
            last_switch = str(raw.get("last_switch_at") or raw.get("last_failover_at") or "")
        except Exception:
            pass

    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "botapi": {
            "active_slot": int(pool.get("active_slot") or 0),
            "auto_failover": auto,
            "free": free,
            "total": total,
            "alive": alive,
            "last_switch_at": last_switch or None,
        },
        "queue": {
            "done": queue.get("done", 0),
            "pending": queue.get("pending", 0),
            "fail": queue.get("fail", 0),
            "max_per_hour": join_cfg.max_per_hour,
            "hint_ru": tg_queue_hint_ru(
                int(queue.get("done", 0)),
                int(queue.get("pending", 0)),
                int(queue.get("fail", 0)),
                int(join_cfg.max_per_hour),
            ),
        },
        "accounts": acc_rows,
    }
