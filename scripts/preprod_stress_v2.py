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
_CYCLE_HEADER = re.compile(r"── Цикл (\d{4}-\d{2}-\d{2} \d{2}:\d{2})")
_TIER_ENV_KEYS = {
    "free": "RAWLEAD_PREPROD_FREE_TOKEN",
    "trial": "RAWLEAD_PREPROD_TRIAL_TOKEN",
    "premium": "RAWLEAD_PREPROD_ACCESS_TOKEN",
}
_L2_SEND_MIN = 0.70
_L2_AUTO_MIN = 0.95
_INGEST_GAP_MAX_MIN = 15
_DEFAULT_VERIFY_MD = _ROOT / "data" / "preprod_stress_v2_verify.md"
_L2_AUDIT_CANDIDATES = (
    _ROOT / "data" / "preprod_ai_prod_audit.json",
    _ROOT / "data" / "preprod_ai_prod_audit_o162_post.json",
)
_PREPROD_ACC1_USER_ID = "7a83dbd8-ab41-4350-a183-38370d5b5c1c"
_PREPROD_ACC1_DEV_TAGS = {
    "python": 4.0,
    "fastapi": 3.8,
    "django": 3.5,
    "api_integration": 3.0,
    "web_scraping": 2.8,
}


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


def parse_radar_ingest_gaps(
    log_text: str,
    *,
    max_gap_min: int = _INGEST_GAP_MAX_MIN,
) -> dict[str, Any]:
    """O168 g4: max gap between radar cycle headers in log tail (24h proxy)."""
    stamps: list[datetime] = []
    for line in log_text.splitlines():
        m = _CYCLE_HEADER.search(line)
        if not m:
            continue
        try:
            stamps.append(
                datetime.strptime(m.group(1), "%Y-%m-%d %H:%M").replace(
                    tzinfo=timezone.utc
                )
            )
        except ValueError:
            continue
    if len(stamps) < 2:
        return {
            "cycle_count": len(stamps),
            "max_gap_min": None,
            "pass": True,
            "note": "fewer than 2 cycle markers in log tail",
        }
    max_gap = max(
        (stamps[i] - stamps[i - 1]).total_seconds() / 60.0
        for i in range(1, len(stamps))
    )
    return {
        "cycle_count": len(stamps),
        "max_gap_min": round(max_gap, 1),
        "pass": max_gap <= max_gap_min,
    }


def _store_tier_token(name: str, token: str) -> None:
    env_key = _TIER_ENV_KEYS.get(name)
    if env_key and token:
        os.environ[env_key] = token


def _write_env_site_token(env_key: str, token: str) -> None:
    path = _ROOT / ".env.site"
    if not path.is_file():
        return
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    prefix = f"{env_key}="
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.strip().startswith(prefix):
            out.append(f"{prefix}{token}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"{prefix}{token}")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


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
    timeout: float = 45.0,
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


def _ensure_preprod_acc1_dev_tags(db_url: str) -> dict[str, Any]:
    """skills_mismatch leaves acc1 on yii2-only — restore dev profile for J5/J6."""
    if not db_url.strip():
        return {"skipped": True, "reason": "no DATABASE_URL"}
    import psycopg

    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
    from api_server import _replace_quiz_import_user_tags

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT tag FROM user_tags WHERE user_id = %s::uuid ORDER BY tag",
                (_PREPROD_ACC1_USER_ID,),
            )
            before = [r[0] for r in cur.fetchall()]
            needs_restore = before == ["yii2"] or not any(
                t in before for t in ("python", "fastapi", "django")
            )
            if not needs_restore:
                return {"restored": False, "tags": before}
            imported = _replace_quiz_import_user_tags(
                cur, _PREPROD_ACC1_USER_ID, dict(_PREPROD_ACC1_DEV_TAGS), ["dev"]
            )
            conn.commit()
            return {"restored": True, "imported": imported, "before": before}


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
                    _store_tier_token(name, token)
                    env_key = _TIER_ENV_KEYS.get(name)
                    if env_key:
                        _write_env_site_token(env_key, token)
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
            meta["ok"] = True
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
                _store_tier_token(name, token)
                env_key = _TIER_ENV_KEYS.get(name)
                if env_key:
                    _write_env_site_token(env_key, token)
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


def _fetch_l2_audit_sample(
    conn: Any,
    *,
    limit: int,
    since_days: int = 7,
) -> list[dict[str, Any]]:
    from preprod_ai_prod_audit import _SELECT_COLS, _row_to_lead
    from public_feed import public_feed_source_sql

    src_sql, src_params = public_feed_source_sql()
    sql = f"""
        SELECT {_SELECT_COLS}
        FROM leads
        WHERE is_visible = TRUE
          {src_sql}
          AND created_at >= NOW() - make_interval(days => %s)
          AND COALESCE(NULLIF(TRIM(reply_draft), ''), '') <> ''
          AND LOWER(TRIM(COALESCE(ai_verdict, ''))) IN (
              'брать', 'брат', 'сомнительно', 'take', 'ok', 'maybe'
          )
        ORDER BY id DESC
        LIMIT %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, [*src_params, since_days, limit])
        rows = cur.fetchall()
    return [_row_to_lead(r) for r in rows]


def load_cached_l2_send(*, max_age_hours: int = 48) -> dict[str, Any] | None:
    """Recent judge_l2_summary from prod audit artifacts (O168 offline gate)."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
    for path in _L2_AUDIT_CANDIDATES:
        if not path.is_file():
            continue
        try:
            body = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        js = body.get("judge_l2_summary")
        if not isinstance(js, dict) or not js.get("scored"):
            continue
        gen = body.get("generated_at")
        if gen:
            try:
                ts = datetime.fromisoformat(str(gen).replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts < cutoff:
                    continue
            except ValueError:
                pass
        send_pct = float(js.get("send_as_is_pct") or 0) / 100.0
        return {
            "source": str(path.relative_to(_ROOT)),
            "send_as_is_pct": js.get("send_as_is_pct"),
            "accept_l2": bool(js.get("accept_l2")),
            "pass": send_pct >= _L2_SEND_MIN,
            "scored": js.get("scored"),
            "avg_combined_3": js.get("avg_combined_3"),
        }
    return None


def _audit_lead_stress(lead: dict[str, Any]) -> dict[str, Any]:
    """O168: TZ-aware auto-audit (validate_stored_l2_draft), not bare audit_lead."""
    from ai_analyze import validate_stored_l2_draft

    fails = validate_stored_l2_draft(
        verdict=lead.get("ai_verdict") or "",
        reply_draft=lead.get("reply_draft") or "",
        tools_required=lead.get("tools_required") or [],
        title=lead.get("title") or "",
        description=lead.get("body") or "",
        task_summary=lead.get("task_summary") or "",
        lead_tags=lead.get("lead_tags") or [],
    )
    draft_fails = [f for f in fails if f.startswith(("L1:", "L2:"))]
    tools_fails = [f for f in fails if f.startswith("tools:")]
    return {
        **lead,
        "fails": fails,
        "draft_fails": draft_fails,
        "tools_fails": tools_fails,
        "draft_only_pass": not draft_fails,
        "tools_pass": not tools_fails,
        "auto_pass": not fails,
    }


def check_l2_quality(
    db_url: str,
    *,
    run_judge: bool,
    judge_limit: int,
    sample_limit: int,
) -> dict[str, Any]:
    """O168 g1: forbidden/tools auto-audit on Neon sample + optional L2 send judge."""
    from preprod_ai_prod_audit import _judge_l2_summary, _run_judge_l2
    from config import load_config

    try:
        import psycopg

        with psycopg.connect(db_url) as conn:
            leads = _fetch_l2_audit_sample(conn, limit=sample_limit)
    except Exception as exc:
        return {"pass": False, "error": f"db: {exc}"}

    if not leads:
        return {"pass": False, "error": "no L2 sample leads", "sample_size": 0}

    audited = [_audit_lead_stress(lead) for lead in leads]
    draft_ok = sum(1 for r in audited if r.get("draft_only_pass"))
    tools_ok = sum(1 for r in audited if r.get("tools_pass"))
    auto_ok = sum(1 for r in audited if r.get("auto_pass"))
    n = len(audited)
    draft_rate = draft_ok / n
    tools_rate = tools_ok / n
    auto_rate = auto_ok / n
    auto_pass = draft_rate >= _L2_AUTO_MIN and tools_rate >= _L2_AUTO_MIN

    result: dict[str, Any] = {
        "sample_size": n,
        "draft_only_pass_pct": round(draft_rate * 100, 1),
        "tools_pass_pct": round(tools_rate * 100, 1),
        "auto_pass_pct": round(auto_rate * 100, 1),
        "auto_pass": auto_pass,
        "top_fails": [
            {
                "lead_id": r["lead_id"],
                "fails": r.get("fails") or [],
            }
            for r in audited
            if not r.get("auto_pass")
        ][:8],
    }

    send_section: dict[str, Any] = {"pass": False, "mode": "none"}
    if run_judge:
        cfg = load_config()
        judged = _run_judge_l2(cfg, audited, limit=judge_limit)
        js = _judge_l2_summary(judged)
        send_pct = float(js.get("send_as_is_pct") or 0) / 100.0
        send_section = {
            "mode": "judge",
            "pass": send_pct >= _L2_SEND_MIN,
            "send_as_is_pct": js.get("send_as_is_pct"),
            "accept_l2": js.get("accept_l2"),
            "scored": js.get("scored"),
            "avg_combined_3": js.get("avg_combined_3"),
        }
    else:
        cached = load_cached_l2_send()
        if cached:
            send_section = {**cached, "mode": "cached_audit"}
        else:
            send_section = {
                "mode": "skipped",
                "pass": True,
                "note": "run --l2-judge or preprod_ai_prod_audit --judge",
            }

    result["send_gate"] = send_section
    send_ok = (
        send_section.get("pass") is True or send_section.get("mode") == "skipped"
    )
    result["pass"] = auto_pass and send_ok
    return result


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
    l2 = report.get("l2_quality") or {}
    ingest = report.get("ingest_24h") or {}

    gates = {
        "tier_matrix": _gate_result(tier_matrix),
        "load_p95_feed": _gate_result(load, pass_key="s3_pass"),
        "l2_auto": _gate_result(l2, pass_key="auto_pass"),
        "l2_send": (
            "skipped"
            if l2.get("skipped")
            or (l2.get("send_gate") or {}).get("mode") in ("skipped", "missing")
            else _gate_result(l2.get("send_gate") or {}, pass_key="pass")
        ),
        "draft_burst": _gate_result(draft),
        "tz_leads": _gate_result(tz),
        "ux_journey": _gate_result(journey),
        "parsers": _gate_result(parsers),
        "ingest_24h": _gate_result(ingest),
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
    if parsers.get("ingest_max_gap_min") is not None:
        lines.append(
            f"- ingest max gap: **{parsers.get('ingest_max_gap_min')} min** "
            f"(cycles **{parsers.get('ingest_cycle_count', 0)}**)"
        )

    l2 = report.get("l2_quality") or {}
    if not l2.get("skipped"):
        sg = l2.get("send_gate") or {}
        lines.extend(
            [
                "",
                "## L2 quality (O168)",
                "",
                f"- auto pass: **{l2.get('auto_pass_pct', '—')}%** "
                f"(draft **{l2.get('draft_only_pass_pct', '—')}%** · "
                f"tools **{l2.get('tools_pass_pct', '—')}%** · n={l2.get('sample_size', 0)})",
                f"- send gate ({sg.get('mode', '—')}): "
                f"**{sg.get('send_as_is_pct', '—')}%** "
                f"({'PASS' if sg.get('pass') else 'FAIL' if sg.get('mode') not in ('skipped',) else 'skipped'})",
            ]
        )

    ingest = report.get("ingest_24h") or {}
    if not ingest.get("skipped"):
        lines.extend(
            [
                "",
                "## Ingest 24h",
                "",
                f"- max cycle gap: **{ingest.get('max_gap_min', '—')} min** "
                f"(limit **{ingest.get('max_allowed_min', _INGEST_GAP_MAX_MIN)}**)",
            ]
        )

    skills = report.get("skills_mismatch") or {}
    if not skills.get("skipped"):
        lines.extend(["", "## S1-b skills_mismatch", "", f"- PASS: **{skills.get('pass')}**"])

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_verify_brief(report: dict[str, Any], path: Path) -> None:
    """O168: short verify brief for owner / Lead."""
    ps = report.get("pass_summary") or {}
    gates = ps.get("gates") or {}
    load = report.get("load") or {}
    l2 = report.get("l2_quality") or {}
    sg = l2.get("send_gate") or {}
    ingest = report.get("ingest_24h") or {}
    draft = report.get("draft_burst") or {}
    draft_p95 = ((draft.get("timings_agg") or {}).get("total") or {}).get("p95_ms")
    lines = [
        "# PRE-PROD Stress V2 verify (O168)",
        "",
        f"**Generated:** {report.get('generated_at', '')}",
        f"**Overall:** {'PASS' if ps.get('pass') else 'FAIL'}",
        "",
        "## Gates",
        "",
    ]
    for key, ok in gates.items():
        mark = "⏭" if ok == "skipped" else ("✅" if ok else "❌")
        lines.append(f"- **{key}**: {mark}")
    lines.extend(
        [
            "",
            "## Metrics",
            "",
            f"- feed p95 @50 VU: **{load.get('p95_feed_ms', '—')} ms** (target <2000)",
            f"- L2 auto: **{l2.get('auto_pass_pct', '—')}%** · send: "
            f"**{sg.get('send_as_is_pct', '—')}%** ({sg.get('mode', '—')})",
            f"- ingest max gap: **{ingest.get('max_gap_min', '—')} min**",
        ]
    )
    if draft_p95 is not None and float(draft_p95) > 90_000:
        lines.extend(
            [
                "",
                "## Watch",
                "",
                f"- **draft_burst** total p95 **{float(draft_p95) / 1000:.1f}s** >90s — monitor (no fix unless owner bar)",
            ]
        )
    lines.extend(
        [
            "",
            "## Next",
            "",
            "- tier_matrix: `DATABASE_URL` + mint acc2 free / acc3 trial if env tokens stale",
            "- p95: Neon pooler on VPS API (`DATABASE_URL` :6543) — см. O131",
            "- L2 send: `preprod_stress_v2.py --l2-judge` or `preprod_ai_prod_audit.py --judge`",
        ]
    )
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
    skip_l2: bool,
    l2_judge: bool,
    l2_judge_limit: int,
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

    if skip_tz:
        report["tz"] = {"skipped": True, "pass": True}
    else:
        report["tz"] = check_tz_leads(api_url, db_url=db_url or None, limit=5 if not quick else 3)

    # Journey before draft_burst — burst exhausts /draft rate limit (J5/J6 429).
    if skip_journey:
        report["ux_journey"] = {"skipped": True, "pass": True}
    elif not premium_token:
        report["ux_journey"] = {"skipped": True, "reason": "no premium token", "pass": False}
    else:
        if db_url:
            report["preprod_acc1_tags"] = _ensure_preprod_acc1_dev_tags(db_url)
        report["ux_journey"] = run_ux_journey(base_url, token=premium_token)

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

    if skip_skills:
        report["skills_mismatch"] = {"skipped": True, "pass": True}
    else:
        report["skills_mismatch"] = run_skills_mismatch()

    if skip_parsers:
        report["parser_snapshot"] = {"skipped": True, "pass": True}
        report["ingest_24h"] = {"skipped": True, "pass": True}
    else:
        log_text, log_source = fetch_radar_log(vps=vps_log, local_path=radar_log)
        snap = parse_radar_snapshot(log_text)
        snap["log_source"] = log_source
        report["parser_snapshot"] = snap
        report["ingest_24h"] = {
            "max_gap_min": snap.get("ingest_max_gap_min"),
            "cycle_count": snap.get("ingest_cycle_count", 0),
            "max_allowed_min": _INGEST_GAP_MAX_MIN,
            "pass": snap.get("ingest_max_gap_min") is None
            or float(snap.get("ingest_max_gap_min") or 0) <= _INGEST_GAP_MAX_MIN,
        }

    if skip_l2 or not db_url:
        report["l2_quality"] = {
            "skipped": True,
            "pass": True,
            **({"reason": "no DATABASE_URL"} if not db_url else {}),
        }
    else:
        report["l2_quality"] = check_l2_quality(
            db_url,
            run_judge=l2_judge,
            judge_limit=l2_judge_limit,
            sample_limit=15 if quick else 30,
        )

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
    parser.add_argument("--skip-l2", action="store_true")
    parser.add_argument(
        "--l2-judge",
        action="store_true",
        help="Run OpenRouter L2 judge on sample (expensive)",
    )
    parser.add_argument("--l2-judge-limit", type=int, default=10)
    parser.add_argument("--output-json", type=Path, default=_DEFAULT_JSON)
    parser.add_argument("--output-md", type=Path, default=_DEFAULT_MD)
    parser.add_argument("--output-verify-md", type=Path, default=_DEFAULT_VERIFY_MD)
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
        skip_l2=args.skip_l2,
        l2_judge=args.l2_judge,
        l2_judge_limit=args.l2_judge_limit,
        mint_tokens=not args.no_mint,
        vps_log=args.vps_log,
        radar_log=args.radar_log,
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(report, args.output_md)
    write_verify_brief(report, args.output_verify_md)
    print(json.dumps(report.get("pass_summary"), ensure_ascii=False, indent=2))
    print(f"→ {args.output_json}")
    print(f"→ {args.output_md}")
    print(f"→ {args.output_verify_md}")
    return 0 if (report.get("pass_summary") or {}).get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
