"""O129: unit smoke for preprod_stress_v2 parsers and tier pass logic."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

from preprod_stress_v2 import (  # noqa: E402
    build_pass_summary,
    ensure_tier_plans,
    parse_radar_snapshot,
    probe_tier_matrix,
)


def test_parse_radar_snapshot_green() -> None:
    log = """
2026-06-07 10:00:00 health:fl status=ok kind=ok downloaded=4 new=0
2026-06-07 10:01:00 health:kwork status=ok kind=ok
{"cycle_sec": 62.5, "neon_insert": 2}
"""
    snap = parse_radar_snapshot(log)
    assert snap["pass"] is True
    assert "fl" in snap["health_lines"]
    assert snap["cascade_exhausted_hits"] == 0


def test_parse_radar_snapshot_proxy_spam_fail() -> None:
    log = "\n".join(
        ["proxy cascade exhausted"] * 6
        + ['health:fl status=fail kind=proxy']
        + ['{"cycle_sec": 240.0}']
    )
    snap = parse_radar_snapshot(log)
    assert snap["pass"] is False
    assert snap["cascade_exhausted_hits"] >= 5
    assert snap["runaway_cycle_count"] >= 1


def test_probe_tier_matrix_anon_only(monkeypatch) -> None:
    def fake_http(method, url, *, token=None, timeout=20.0):
        if "/me/subscription" in url:
            return 200, {"plan": "agent", "status": "active"}, None
        return 200, {"items": [{"id": 1}]}, None

    monkeypatch.setattr("preprod_stress_v2._http_json", fake_http)
    tiers = {
        "anon": {"token": None, "source": "none"},
        "free": {"token": None, "source": "missing", "ok": False},
        "trial": {"token": None, "source": "missing", "ok": False},
        "premium": {"token": "x", "source": "env", "ok": True},
    }
    matrix = probe_tier_matrix("https://api.example", tiers)
    assert matrix["rows"][0]["tier"] == "anon"
    assert matrix["rows"][0]["pass"] is True
    assert matrix["rows"][-1]["items"] == 1
    assert matrix["rows"][-1]["plan_ok"] is True
    assert matrix["pass"] is False
    assert matrix["rows"][1]["pass"] is False


def test_probe_tier_matrix_free_plan_mismatch(monkeypatch) -> None:
    plans = {
        "free-wrong": "agent",
        "trial-ok": "trial",
        "prem-ok": "agent",
    }

    def fake_http(method, url, *, token=None, timeout=20.0):
        if "/me/subscription" in url:
            return 200, {"plan": plans[token or ""], "status": "active"}, None
        return 200, {"items": [{"id": 1}]}, None

    monkeypatch.setattr("preprod_stress_v2._http_json", fake_http)
    tiers = {
        "anon": {"token": None, "source": "none"},
        "free": {"token": "free-wrong", "source": "env", "ok": True},
        "trial": {"token": "trial-ok", "source": "env", "ok": True},
        "premium": {"token": "prem-ok", "source": "env", "ok": True},
    }
    matrix = probe_tier_matrix("https://api.example", tiers)
    free_row = next(r for r in matrix["rows"] if r["tier"] == "free")
    assert free_row["plan_ok"] is False
    assert free_row["pass"] is False
    assert matrix["pass"] is False


def test_ensure_tier_plans_fail_loud_without_mint(monkeypatch) -> None:
    def fake_plan(api_url: str, token: str) -> str | None:
        return {
            "free-wrong": "agent",
            "trial-ok": "trial",
            "prem-ok": "agent",
        }.get(token)

    monkeypatch.setattr("preprod_stress_v2._subscription_plan", fake_plan)
    tiers = {
        "anon": {"token": None, "source": "none"},
        "free": {"token": "free-wrong", "source": "env", "ok": True},
        "trial": {"token": "trial-ok", "source": "env", "ok": True},
        "premium": {"token": "prem-ok", "source": "env", "ok": True},
    }
    check = ensure_tier_plans("https://api.example", tiers, mint=False)
    assert check["pass"] is False
    assert tiers["free"]["ok"] is False
    assert tiers["free"]["plan_mismatch"]["expected"] == "free"


def test_build_pass_summary_all_green() -> None:
    report = {
        "tier_matrix": {"pass": True},
        "load": {"s3_pass": True},
        "draft_burst": {"pass": True},
        "tz": {"pass": True},
        "ux_journey": {"pass": True},
        "parser_snapshot": {"pass": True},
        "skills_mismatch": {"pass": True},
    }
    ps = build_pass_summary(report)
    assert ps["pass"] is True
    assert all(v is True for v in ps["gates"].values())


def test_build_pass_summary_skipped_not_pass() -> None:
    report = {
        "tier_matrix": {"pass": True},
        "load": {"skipped": True, "s3_pass": True},
        "draft_burst": {"skipped": True, "pass": True},
        "tz": {"pass": True},
        "ux_journey": {"skipped": True, "pass": True},
        "parser_snapshot": {"skipped": True, "pass": True},
        "skills_mismatch": {"skipped": True, "pass": True},
    }
    ps = build_pass_summary(report)
    assert ps["pass"] is True
    assert ps["gates"]["load_p95_feed"] == "skipped"
    assert ps["gates"]["ux_journey"] == "skipped"
    assert ps["gates"]["tz_leads"] is True
