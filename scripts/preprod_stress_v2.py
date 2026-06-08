"""O129-STRESS-V2 — Wave 2 orchestrator (tiers · load ramp · journey · draft · TZ · parsers).

  .venv\\Scripts\\python.exe scripts\\preprod_stress_v2.py
  .venv\\Scripts\\python.exe scripts\\preprod_stress_v2.py --quick
  .venv\\Scripts\\python.exe scripts\\preprod_stress_v2.py --skip-load --skip-journey
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

for _stream in (sys.stdout, sys.stderr):
    enc = getattr(_stream, "encoding", None) or ""
    if enc.lower() != "utf-8":
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
sys.path.insert(0, str(_SCRIPTS))
sys.path.insert(0, str(_ROOT / "src"))

from preprod_draft_burst import DRAFT_BURST_MAX, run_draft_burst  # noqa: E402
from preprod_load_feed import run_load_ramp  # noqa: E402

_DEFAULT_JSON = _ROOT / "data" / "preprod_stress_v2.json"
_DEFAULT_MD = _ROOT / "data" / "preprod_stress_v2.md"
_TZ_MARKER = "[TZ attachment"
_TZ_EXTRACTED = "[TZ attachment — извлечено"
_RAMP_FULL = [(120, 10), (180, 30), (300, 50)]
_RAMP_QUICK = [(30, 10), (60, 30), (90, 50)]
_UA = "RawLeadStressV2/1.0"

_HEALTH_LINE = re.compile(
    r"health:(?P<source>[a-z_]+)(?:\s+status=(?P<status>\w+))?(?:\s+kind=(?P<kind>\w+))?"
)
_CYCLE_SEC = re.compile(r'"cycle_sec"\s*:\s*([\d.]+)')
_EXCHANGE_ROW = re.compile(
    r"exchange_health:(?P<source>[a-z_]+)\s+(?P<payload>\{.*\})"
)


def percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = int(round((pct / 100.0) * (len(ordered) - 1)))
    return ordered[max(0, min(idx, len(ordered) - 1))]


def parse_radar_snapshot(log_text: str) -> dict[str, Any]:
    """Parse health:* lines, cycle_sec, proxy cascade from radar_site.log tail."""
    lines = log_text.splitlines()
    health: dict[str, dict[str, str]] = {}
    exchange_rows: dict[str, dict[str, Any]] = {}
    cascade_hits = 0
    cycle_secs: list[float] = []

    for line in lines:
        if "proxy cascade exhausted" in line or "pool exhausted" in line.lower():
            cascade_hits += 1
        for m in _CYCLE_SEC.finditer(line):
            try:
                cycle_secs.append(float(m.group(1)))
            except ValueError:
                pass
        hm = _HEALTH_LINE.search(line)
        if hm:
            src = hm.group("source")
            health[src] = {
                "status": hm.group("status") or "",
                "kind": hm.group("kind") or "",
                "line": line.strip()[-240:],
            }
        em = _EXCHANGE_ROW.search(line)
        if em:
            try:
                exchange_rows[em.group("source")] = json.loads(em.group("payload"))
            except json.JSONDecodeError:
                exchange_rows[em.group("source")] = {"raw": em.group("payload")[:200]}

    runaway_cycles = sum(1 for c in cycle_secs if c > 180)
    red_kinds = {"proxy", "403", "browser", "antibot", "timeout"}
    red_sources = [
        src
        for src, row in health.items()
        if (row.get("kind") or "").lower() in red_kinds
        or (row.get("status") or "").lower() in ("fail", "red")
    ]
    all_red = bool(health) and len(red_sources) >= len(health)
    s4_pre_pass = cascade_hits < 5 and runaway_cycles == 0 and not all_red

    return {
        "health_lines": health,
        "exchange_health": exchange_rows,
        "cascade_exhausted_hits": cascade_hits,
        "cycle_sec_samples": cycle_secs[-20:],
        "runaway_cycle_count": runaway_cycles,
        "red_sources": red_sources,
        "pass": s4_pre_pass,
        "note": "См. PREPROD_STRESS_RUN § Parser — downloaded>0 ≠ сломан",
    }


def fetch_radar_log(*, vps: bool, local_path: Path | None) -> tuple[str, str]:
    if local_path and local_path.is_file():
        return local_path.read_text(encoding="utf-8", errors="replace"), str(local_path)
    if vps:
        try:
            import deploy_vps_ssh as ssh

            _, out, _ = ssh.run(
                "tail -400 /opt/rawlead/data/radar_site.log 2>/dev/null || echo ''",
                check=False,
            )
            return out or "", "vps:/opt/rawlead/data/radar_site.log"
        except Exception as exc:
            return "", f"vps_error:{exc}"
    local = _ROOT / "data" / "radar_site.log"
    if local.is_file():
        return local.read_text(encoding="utf-8", errors="replace"), str(local)
    return "", "missing"


def _http_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    timeout: float = 20.0,
) -> tuple[int | None, dict[str, Any] | None, str | None]:
    headers = {"User-Agent": _UA, "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, headers=headers, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            body = json.loads(raw.decode("utf-8")) if raw else {}
            return resp.status, body if isinstance(body, dict) else None, None
    except HTTPError as exc:
        try:
            raw = exc.read()
            body = json.loads(raw.decode("utf-8")) if raw else {}
        except (HTTPError, json.JSONDecodeError, OSError):
            body = None
        return exc.code, body if isinstance(body, dict) else None, str(exc.reason)
    except URLError as exc:
        return None, None, str(exc.reason)


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        for name in (".env", ".env.site"):
            p = _ROOT / name
            if p.is_file():
                load_dotenv(p, override=(name == ".env.site"))
    except ImportError:
        pass


def _env_token(key: str) -> str:
    val = os.environ.get(key, "").strip()
    if val:
        return val
    for name in (".env.site", ".env", ".env.local"):
        path = _ROOT / name
        if not path.is_file():
            continue
        prefix = f"{key}="
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(prefix):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _mint_token(account: str, plan: str, env_key: str, *, force: bool = False) -> tuple[str, str]:
    if not force:
        existing = _env_token(env_key)
        if existing:
            return existing, f"env:{env_key}"
    py = sys.executable
    cmd = [
        py,
        str(_SCRIPTS / "preprod_mint_token.py"),
        "--account",
        account,
        "--plan",
        plan,
        "--write-env-site",
        "--env-key",
        env_key,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(_ROOT))
    if proc.returncode != 0:
        return "", f"mint_fail:{proc.stderr.strip()[:200]}"
    token = _env_token(env_key)
    return token, f"mint:{account}:{plan}"


def _set_trial_subscription(user_id: str, db_url: str) -> None:
    import psycopg

    until = datetime.now(timezone.utc) + timedelta(days=3)
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO subscriptions (
                    user_id, plan, is_active, active_until, paused_until, trial_used_at
                )
                VALUES (%s::uuid, 'trial', TRUE, %s, NULL, NOW())
                ON CONFLICT (user_id) DO UPDATE
                SET plan = 'trial',
                    is_active = TRUE,
                    active_until = EXCLUDED.active_until,
                    paused_until = NULL,
                    trial_used_at = COALESCE(subscriptions.trial_used_at, NOW())
                """,
                (user_id, until),
            )
        conn.commit()


def _issue_token_for_user(db_url: str, tg_user_id: int, user_id: str) -> str:
    from jwt_auth import issue_access_token

    return issue_access_token(user_id, tg_user_id=tg_user_id)


def resolve_tier_tokens(*, mint: bool) -> dict[str, Any]:
    _load_env()
    db_url = os.environ.get("DATABASE_URL", "").strip()
    tiers: dict[str, Any] = {}

    premium = _env_token("RAWLEAD_PREPROD_ACCESS_TOKEN")
    premium_src = "env:RAWLEAD_PREPROD_ACCESS_TOKEN"
    if not premium and mint:
        premium, premium_src = _mint_token("acc1", "agent", "RAWLEAD_PREPROD_ACCESS_TOKEN")

    free = _env_token("RAWLEAD_PREPROD_FREE_TOKEN")
    free_src = "env:RAWLEAD_PREPROD_FREE_TOKEN"
    if not free and mint:
        proc = subprocess.run(
            [sys.executable, str(_SCRIPTS / "mint_free_local_token.py"), "--account", "acc2"],
            capture_output=True,
            text=True,
            cwd=str(_ROOT),
        )
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                if line.startswith("token="):
                    free = line.split("=", 1)[1].strip()
                    free_src = "mint:acc2:free"
        if not free and db_url:
            free, free_src = _mint_token("acc2", "free", "RAWLEAD_PREPROD_FREE_TOKEN")

    trial = _env_token("RAWLEAD_PREPROD_TRIAL_TOKEN")
    trial_src = "env:RAWLEAD_PREPROD_TRIAL_TOKEN"
    if not trial and mint and db_url:
        proc = subprocess.run(
            [sys.executable, str(_SCRIPTS / "preprod_mint_token.py"), "--account", "acc3", "--plan", "agent"],
            capture_output=True,
            text=True,
            cwd=str(_ROOT),
        )
        user_id = ""
        tg_user_id = 0
        for line in proc.stdout.splitlines():
            if line.startswith("user_id="):
                user_id = line.split("=", 1)[1].strip()
            if line.startswith("tg_user_id="):
                tg_user_id = int(line.split("=", 1)[1].strip())
        if user_id:
            try:
                _set_trial_subscription(user_id, db_url)
                trial = _issue_token_for_user(db_url, tg_user_id, user_id)
                trial_src = "mint:acc3:trial"
            except Exception as exc:
                trial_src = f"trial_fail:{exc}"

    tiers["anon"] = {"token": None, "source": "none"}
    tiers["free"] = {"token": free or None, "source": free_src, "ok": bool(free)}
    tiers["trial"] = {"token": trial or None, "source": trial_src, "ok": bool(trial)}
    tiers["premium"] = {"token": premium or None, "source": premium_src, "ok": bool(premium)}
    return tiers


_TIER_EXPECTED_PLAN = {"free": "free", "trial": "trial", "premium": "agent"}


def _subscription_plan(api_url: str, token: str) -> str | None:
    _, body, _ = _http_json(
        "GET",
        f"{api_url.rstrip('/')}/v1/me/subscription",
        token=token,
    )
    if not body:
        return None
    plan = (body.get("plan") or "").strip()
    return plan or None


def _remint_free_token(db_url: str) -> tuple[str | None, str]:
    proc = subprocess.run(
        [sys.executable, str(_SCRIPTS / "mint_free_local_token.py"), "--account", "acc2"],
        capture_output=True,
        text=True,
        cwd=str(_ROOT),
    )
    if proc.returncode != 0:
        return None, f"mint_fail:{proc.stderr.strip()[:200]}"
    token = ""
    for line in proc.stdout.splitlines():
        if line.startswith("token="):
            token = line.split("=", 1)[1].strip()
    if token:
        return token, "mint:acc2:free"
    if db_url:
        return _mint_token("acc2", "free", "RAWLEAD_PREPROD_FREE_TOKEN", force=True)
    return None, "mint_fail:no_token"


def _remint_trial_token(db_url: str) -> tuple[str | None, str]:
    proc = subprocess.run(
        [sys.executable, str(_SCRIPTS / "preprod_mint_token.py"), "--account", "acc3", "--plan", "agent"],
        capture_output=True,
        text=True,
        cwd=str(_ROOT),
    )
    user_id = ""
    tg_user_id = 0
    for line in proc.stdout.splitlines():
        if line.startswith("user_id="):
            user_id = line.split("=", 1)[1].strip()
        if line.startswith("tg_user_id="):
            tg_user_id = int(line.split("=", 1)[1].strip())
    if not user_id:
        return None, f"mint_fail:{proc.stderr.strip()[:200]}"
    try:
        _set_trial_subscription(user_id, db_url)
        return _issue_token_for_user(db_url, tg_user_id, user_id), "mint:acc3:trial"
    except Exception as exc:
        return None, f"trial_fail:{exc}"


def _remint_premium_token() -> tuple[str | None, str]:
    token, src = _mint_token("acc1", "agent", "RAWLEAD_PREPROD_ACCESS_TOKEN", force=True)
    return token or None, src


def ensure_tier_plans(api_url: str, tiers: dict[str, Any], *, mint: bool) -> dict[str, Any]:
    """Validate free/trial/premium JWT plans; remint or fail loud before tier matrix."""
    db_url = os.environ.get("DATABASE_URL", "").strip()
    issues: list[dict[str, Any]] = []

    for name in ("free", "trial", "premium"):
        meta = tiers.get(name) or {}
        expected = _TIER_EXPECTED_PLAN[name]
        token = meta.get("token")

        if not token:
            if mint and db_url:
                if name == "free":
                    token, src = _remint_free_token(db_url)
                elif name == "trial":
                    token, src = _remint_trial_token(db_url)
                else:
                    token, src = _remint_premium_token()
                if token:
                    meta["token"] = token
                    meta["source"] = src
                    meta["ok"] = True
            if not meta.get("token"):
                meta["ok"] = False
                issues.append(
                    {
                        "tier": name,
                        "error": "no_token",
                        "expected_plan": expected,
                        "source": meta.get("source"),
                    }
                )
                continue
            token = meta["token"]

        actual = _subscription_plan(api_url, token)
        if actual == expected:
            meta.pop("plan_mismatch", None)
            continue

        if mint:
            if name == "free":
                token, src = _remint_free_token(db_url)
            elif name == "trial":
                token, src = _remint_trial_token(db_url)
            else:
                token, src = _remint_premium_token()
            if token:
                meta["token"] = token
                meta["source"] = src
                meta["ok"] = True
                actual = _subscription_plan(api_url, token)

        if actual != expected:
            meta["ok"] = False
            meta["plan_mismatch"] = {"expected": expected, "actual": actual}
            issues.append(
                {
                    "tier": name,
                    "error": "plan_mismatch",
                    "expected_plan": expected,
                    "actual_plan": actual,
                    "source": meta.get("source"),
                }
            )

    return {"pass": not issues, "issues": issues}


def probe_tier_matrix(api_url: str, tiers: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for name in ("anon", "free", "trial", "premium"):
        meta = tiers.get(name) or {}
        token = meta.get("token")
        t0 = time.perf_counter()
        st, body, err = _http_json(
            "GET",
            f"{api_url.rstrip('/')}/v1/feed?limit=5",
            token=token,
        )
        feed_ms = round((time.perf_counter() - t0) * 1000.0, 1)
        items = len((body or {}).get("items") or []) if st == 200 else 0
        sub: dict[str, Any] | None = None
        if token:
            _, sub_body, _ = _http_json(
                "GET",
                f"{api_url.rstrip('/')}/v1/me/subscription",
                token=token,
            )
            sub = sub_body
        expected_plan = _TIER_EXPECTED_PLAN.get(name)
        actual_plan = (sub or {}).get("plan")
        plan_ok = name == "anon" or not expected_plan or actual_plan == expected_plan
        tier_ready = name == "anon" or bool(meta.get("ok"))
        row_pass = st == 200 and items > 0 and tier_ready and plan_ok
        row_error = err
        if not tier_ready and name != "anon":
            row_error = row_error or meta.get("plan_mismatch") or "tier_not_ready"
        elif not plan_ok:
            row_error = row_error or {
                "expected_plan": expected_plan,
                "actual_plan": actual_plan,
            }
        rows.append(
            {
                "tier": name,
                "feed_status": st,
                "feed_ms": feed_ms,
                "items": items,
                "token_source": meta.get("source"),
                "subscription_status": (sub or {}).get("status"),
                "plan": actual_plan,
                "expected_plan": expected_plan,
                "plan_ok": plan_ok,
                "error": row_error,
                "pass": row_pass,
            }
        )
    return {
        "rows": rows,
        "pass": all(r["pass"] for r in rows),
    }


def check_tz_leads(
    api_url: str,
    *,
    db_url: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    lead_ids: list[int] = []
    if db_url:
        try:
            import psycopg

            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id FROM leads
                        WHERE body LIKE %s AND is_visible = TRUE
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (f"%{_TZ_MARKER}%", limit),
                    )
                    lead_ids = [int(r[0]) for r in cur.fetchall()]
        except Exception as exc:
            return {"pass": False, "error": f"db: {exc}", "rows": []}

    if not lead_ids:
        st, body, _ = _http_json("GET", f"{api_url.rstrip('/')}/v1/feed?limit=50")
        if st == 200 and body:
            for it in body.get("items") or []:
                text = f"{it.get('title','')} {it.get('body','')}"
                if _TZ_MARKER in text:
                    lead_ids.append(int(it["id"]))
                if len(lead_ids) >= limit:
                    break

    rows: list[dict[str, Any]] = []
    ok_extracted = 0
    for lid in lead_ids[:limit]:
        t0 = time.perf_counter()
        st, item, err = _http_json("GET", f"{api_url.rstrip('/')}/v1/leads/{lid}")
        ms = round((time.perf_counter() - t0) * 1000.0, 1)
        body = (item or {}).get("body") or ""
        extracted = _TZ_EXTRACTED in body
        chars = len(body)
        row_ok = st == 200 and extracted and chars >= 200
        if row_ok:
            ok_extracted += 1
        rows.append(
            {
                "lead_id": lid,
                "status": st,
                "tz_fetch_ms": ms,
                "body_chars": chars,
                "extracted": extracted,
                "pass": row_ok,
                "error": err,
            }
        )

    need = max(1, (len(rows) * 2 + 2) // 3) if rows else 1
    passed = len(rows) >= 1 and ok_extracted >= min(need, len(rows))
    return {
        "lead_ids": lead_ids[:limit],
        "rows": rows,
        "ok_extracted": ok_extracted,
        "required_ok": need,
        "pass": passed,
    }


def run_subprocess_step(
    cmd: list[str],
    *,
    env: dict[str, str] | None = None,
    timeout_sec: int = 3600,
) -> dict[str, Any]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    t0 = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=str(_ROOT),
        capture_output=True,
        text=True,
        env=merged,
        timeout=timeout_sec,
    )
    return {
        "cmd": cmd,
        "exit_code": proc.returncode,
        "duration_sec": round(time.perf_counter() - t0, 1),
        "stdout_tail": (proc.stdout or "")[-2000:],
        "stderr_tail": (proc.stderr or "")[-1000:],
        "pass": proc.returncode == 0,
    }


def run_ux_journey(base_url: str, *, token: str) -> dict[str, Any]:
    out_json = _ROOT / "data" / "preprod_ux_journey_stress.json"
    out_md = _ROOT / "data" / "preprod_ux_journey_stress.md"
    cmd = [
        sys.executable,
        str(_SCRIPTS / "preprod_playwright" / "ux_journey.py"),
        "--base-url",
        base_url,
        "--browser",
        "chromium",
        "--output-json",
        str(out_json),
        "--output-md",
        str(out_md),
    ]
    step = run_subprocess_step(cmd, env={"RAWLEAD_PREPROD_ACCESS_TOKEN": token}, timeout_sec=1800)
    report: dict[str, Any] = {}
    if out_json.is_file():
        try:
            report = json.loads(out_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report = {}
    step["critical_count"] = report.get("critical_count", -1)
    step["journeys_pass"] = report.get("journeys_pass")
    step["journeys_total"] = report.get("journeys_total")
    step["pass"] = bool(report.get("pass")) and step["exit_code"] == 0
    step["artifacts"] = {"json": str(out_json), "md": str(out_md)}
    return step


def run_skills_mismatch(*, profile: str = "site") -> dict[str, Any]:
    out = _ROOT / "data" / "preprod_skills_mismatch.json"
    cmd = [
        sys.executable,
        str(_SCRIPTS / "preprod_ai_matrix.py"),
        "--profile",
        profile,
        "--scenario",
        "skills_mismatch",
        "--output",
        str(out),
    ]
    step = run_subprocess_step(cmd, timeout_sec=600)
    if out.is_file():
        try:
            body = json.loads(out.read_text(encoding="utf-8"))
            step["pass"] = bool(body.get("pass"))
            step["summary"] = body.get("summary")
        except json.JSONDecodeError:
            pass
    step["artifact"] = str(out)
    return step


def _gate_result(section: dict[str, Any], *, pass_key: str = "pass") -> bool | str:
    if section.get("skipped"):
        return "skipped"
    if pass_key == "s3_pass":
        return bool(section.get("s3_pass"))
    return bool(section.get(pass_key))


def build_pass_summary(report: dict[str, Any]) -> dict[str, Any]:
    load = report.get("load") or {}
    draft = report.get("draft_burst") or {}
    tz = report.get("tz") or {}
    journey = report.get("ux_journey") or {}
    parsers = report.get("parser_snapshot") or {}
    skills = report.get("skills_mismatch") or {}
    tier_matrix = report.get("tier_matrix") or {}

    gates = {
        "tier_matrix": _gate_result(tier_matrix),
        "load_p95_feed": _gate_result(load, pass_key="s3_pass"),
        "draft_burst": _gate_result(draft),
        "tz_leads": _gate_result(tz),
        "ux_journey": _gate_result(journey),
        "parsers": _gate_result(parsers),
        "skills_mismatch": _gate_result(skills),
    }
    actionable = [v for v in gates.values() if v != "skipped"]
    return {"gates": gates, "pass": all(v is True for v in actionable)}


def write_markdown(report: dict[str, Any], path: Path) -> None:
    ps = report.get("pass_summary") or {}
    gates = ps.get("gates") or {}
    lines = [
        "# PRE-PROD Stress V2 (O129)",
        "",
        f"**Generated:** {report.get('generated_at', '')}",
        f"**Overall:** {'PASS' if ps.get('pass') else 'FAIL'}",
        "",
        "## Gates",
        "",
        "| Gate | PASS |",
        "|------|------|",
    ]
    for key, ok in gates.items():
        mark = "⏭" if ok == "skipped" else ("✅" if ok else "❌")
        lines.append(f"| {key} | {mark} |")

    load = report.get("load") or {}
    lines.extend(
        [
            "",
            "## Load (S3-pre ramp)",
            "",
            f"- Peak VU: **{load.get('workers_peak', '—')}** · p95 feed: **{load.get('p95_feed_ms', '—')} ms**",
            f"- Error rate max: **{load.get('error_rate_max', '—')}**",
            f"- {load.get('s3_pre_note', '')}",
            "",
            "## Timings (draft burst)",
            "",
        ]
    )
    agg = (report.get("draft_burst") or {}).get("timings_agg") or {}
    if agg:
        lines.append("| Phase | p50 ms | p95 ms |")
        lines.append("|-------|--------|--------|")
        for phase in ("feed", "expand", "tools", "draft_wait", "total"):
            row = agg.get(phase) or {}
            lines.append(
                f"| {phase} | {row.get('p50_ms', '—')} | {row.get('p95_ms', '—')} |"
            )
        note = (report.get("draft_burst") or {}).get("note_l2_l3")
        if note:
            lines.append(f"\n_{note}_")
    else:
        lines.append("_draft burst skipped or empty_")

    tiers = (report.get("tier_matrix") or {}).get("rows") or []
    if tiers:
        lines.extend(["", "## Tier matrix", "", "| Tier | feed | items | plan |", "|------|------|-------|------|"])
        for r in tiers:
            lines.append(
                f"| {r['tier']} | {r['feed_status']} ({r['feed_ms']}ms) | {r['items']} | {r.get('plan') or '—'} |"
            )

    tz = report.get("tz") or {}
    lines.extend(
        [
            "",
            "## TZ attachments",
            "",
            f"- OK extracted: **{tz.get('ok_extracted', 0)} / {len(tz.get('rows') or [])}** (need ≥2/3)",
        ]
    )
    for row in tz.get("rows") or []:
        lines.append(
            f"- lead `{row['lead_id']}`: {row['body_chars']} chars · "
            f"{'extracted' if row['extracted'] else 'no extract'} · {row['tz_fetch_ms']} ms"
        )

    journey = report.get("ux_journey") or {}
    lines.extend(
        [
            "",
            "## UX Journey J1–J11",
            "",
            f"- critical: **{journey.get('critical_count', '—')}** · "
            f"pass: **{journey.get('journeys_pass', '—')}/{journey.get('journeys_total', '—')}**",
        ]
    )

    parsers = report.get("parser_snapshot") or {}
    lines.extend(["", "## Parser snapshot", ""])
    if parsers.get("health_lines"):
        for src, row in parsers["health_lines"].items():
            lines.append(f"- **{src}**: kind={row.get('kind') or '—'} status={row.get('status') or '—'}")
    else:
        lines.append(f"_log source: {parsers.get('log_source', 'missing')}_")
    lines.append(
        f"- cascade hits: **{parsers.get('cascade_exhausted_hits', 0)}** · "
        f"runaway cycles: **{parsers.get('runaway_cycle_count', 0)}**"
    )

    skills = report.get("skills_mismatch") or {}
    if not skills.get("skipped"):
        lines.extend(["", "## S1-b skills_mismatch", "", f"- PASS: **{skills.get('pass')}**"])

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_stress_v2(
    *,
    base_url: str,
    api_url: str,
    quick: bool,
    skip_load: bool,
    skip_journey: bool,
    skip_draft: bool,
    skip_tz: bool,
    skip_skills: bool,
    skip_parsers: bool,
    mint_tokens: bool,
    vps_log: bool,
    radar_log: Path | None,
) -> dict[str, Any]:
    _load_env()
    db_url = os.environ.get("DATABASE_URL", "").strip()

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url.rstrip("/"),
        "api_url": api_url.rstrip("/"),
        "mode": "quick" if quick else "full",
    }

    tiers = resolve_tier_tokens(mint=mint_tokens)
    report["tier_plan_check"] = ensure_tier_plans(api_url, tiers, mint=mint_tokens)
    report["tiers"] = {
        k: {
            "source": v.get("source"),
            "ok": v.get("ok", True),
            **({"plan_mismatch": v["plan_mismatch"]} if v.get("plan_mismatch") else {}),
        }
        for k, v in tiers.items()
    }
    report["tier_matrix"] = probe_tier_matrix(api_url, tiers)

    premium_token = (tiers.get("premium") or {}).get("token") or ""

    if skip_load:
        report["load"] = {"skipped": True, "s3_pass": True}
    else:
        stages = _RAMP_QUICK if quick else _RAMP_FULL
        report["load"] = run_load_ramp(api_url=api_url, stages=stages)

    if skip_draft:
        report["draft_burst"] = {"skipped": True, "pass": True}
    elif not premium_token:
        report["draft_burst"] = {
            "skipped": True,
            "reason": "no premium token",
            "pass": False,
        }
    else:
        os.environ["RAWLEAD_PREPROD_ACCESS_TOKEN"] = premium_token
        report["draft_burst"] = run_draft_burst(
            api_url=api_url,
            token=premium_token,
            max_leads=DRAFT_BURST_MAX if not quick else min(5, DRAFT_BURST_MAX),
            concurrency=3 if quick else 4,
        )

    if skip_tz:
        report["tz"] = {"skipped": True, "pass": True}
    else:
        report["tz"] = check_tz_leads(api_url, db_url=db_url or None, limit=5 if not quick else 3)

    if skip_journey:
        report["ux_journey"] = {"skipped": True, "pass": True}
    elif not premium_token:
        report["ux_journey"] = {"skipped": True, "reason": "no premium token", "pass": False}
    else:
        report["ux_journey"] = run_ux_journey(base_url, token=premium_token)

    if skip_skills:
        report["skills_mismatch"] = {"skipped": True, "pass": True}
    else:
        report["skills_mismatch"] = run_skills_mismatch()

    if skip_parsers:
        report["parser_snapshot"] = {"skipped": True, "pass": True}
    else:
        log_text, log_source = fetch_radar_log(vps=vps_log, local_path=radar_log)
        snap = parse_radar_snapshot(log_text)
        snap["log_source"] = log_source
        report["parser_snapshot"] = snap

    report["pass_summary"] = build_pass_summary(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="O129 PRE-PROD Stress V2 orchestrator")
    parser.add_argument("--base-url", default="https://rawlead.ru")
    parser.add_argument("--api-url", default="https://api.rawlead.ru")
    parser.add_argument("--quick", action="store_true", help="Shorter ramp/draft/journey subset")
    parser.add_argument("--no-mint", action="store_true", help="Only env tokens, no Telethon mint")
    parser.add_argument("--vps-log", action="store_true", help="Fetch radar_site.log via SSH")
    parser.add_argument("--radar-log", type=Path, help="Local radar log file")
    parser.add_argument("--skip-load", action="store_true")
    parser.add_argument("--skip-journey", action="store_true")
    parser.add_argument("--skip-draft", action="store_true")
    parser.add_argument("--skip-tz", action="store_true")
    parser.add_argument("--skip-skills", action="store_true")
    parser.add_argument("--skip-parsers", action="store_true")
    parser.add_argument("--output-json", type=Path, default=_DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=_DEFAULT_MD)
    args = parser.parse_args()

    report = run_stress_v2(
        base_url=args.base_url,
        api_url=args.api_url,
        quick=args.quick,
        skip_load=args.skip_load,
        skip_journey=args.skip_journey,
        skip_draft=args.skip_draft,
        skip_tz=args.skip_tz,
        skip_skills=args.skip_skills,
        skip_parsers=args.skip_parsers,
        mint_tokens=not args.no_mint,
        vps_log=args.vps_log,
        radar_log=args.radar_log,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(report, args.output_md)
    print(json.dumps(report.get("pass_summary"), ensure_ascii=False, indent=2))
    print(f"→ {args.output_json}")
    print(f"→ {args.output_md}")
    return 0 if (report.get("pass_summary") or {}).get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
