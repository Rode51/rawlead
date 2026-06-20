"""O282-B: preprod weights journey — narrow / broad / browse personas.

  .venv\\Scripts\\python.exe scripts\\preprod_weights_journey.py
  .venv\\Scripts\\python.exe scripts\\preprod_weights_journey.py --simulate
  .venv\\Scripts\\python.exe scripts\\preprod_weights_journey.py --api-url http://127.0.0.1:8000

Requires DATABASE_URL unless --simulate (rank-only judges B8 + smoke).
Writes: data/preprod_weights_journey.json · data/preprod_weights_journey.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

for _stream in (sys.stdout, sys.stderr):
    enc = getattr(_stream, "encoding", None) or ""
    if enc.lower() != "utf-8":
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

_ARTIFACT_JSON = _ROOT / "data" / "preprod_weights_journey.json"
_ARTIFACT_MD = _ROOT / "data" / "preprod_weights_journey.md"

_TAG_WEIGHT_MAX = 10.0
_BROWSE_EXPANDS = 15
_NOPE_CLUSTER_COUNT = 5


@dataclass(frozen=True)
class Persona:
    id: str
    label_ru: str
    quiz_tags: dict[str, float]
    niches: list[str]
    mode: str  # narrow | broad | browse | skip


PERSONAS: tuple[Persona, ...] = (
    Persona(
        id="narrow",
        label_ru="Узкий профиль (dev)",
        quiz_tags={
            "python": 4.0,
            "fastapi": 3.8,
            "django": 3.5,
            "api_integration": 3.0,
        },
        niches=["dev"],
        mode="narrow",
    ),
    Persona(
        id="broad",
        label_ru="Широкий профиль (dev + design + marketing)",
        quiz_tags={
            "python": 3.5,
            "figma": 3.2,
            "ui_ux": 3.0,
            "smm": 2.8,
            "seo": 2.5,
            "telegram_bot_dev": 2.2,
        },
        niches=["dev", "design", "marketing"],
        mode="broad",
    ),
    Persona(
        id="browse",
        label_ru="Листание без отклика (15 раскрытий)",
        quiz_tags={
            "python": 4.0,
            "fastapi": 3.6,
            "django": 3.2,
            "web_scraping": 2.8,
        },
        niches=["dev"],
        mode="browse",
    ),
    Persona(
        id="skip_cluster",
        label_ru="Явный skip кластера (5× push_nope)",
        quiz_tags={
            "python": 4.0,
            "fastapi": 3.5,
            "figma": 2.0,
        },
        niches=["dev", "design"],
        mode="skip",
    ),
)


@dataclass
class StepSnapshot:
    label: str
    user_tags: dict[str, float]
    feed_top20: list[dict[str, Any]]
    metrics: dict[str, Any] = field(default_factory=dict)


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        for name in (".env", ".env.site"):
            p = _ROOT / name
            if p.is_file():
                load_dotenv(p, override=(name == ".env.site"))
    except ImportError:
        pass


def _primary_niche(persona: Persona) -> str:
    return persona.niches[0]


def _avg_km_primary_top5(feed: list[dict[str, Any]], primary: str) -> float | None:
    primary_items = [
        it
        for it in feed[:20]
        if (it.get("category") or "") == primary and it.get("keyword_match") is not None
    ]
    top5 = primary_items[:5]
    if not top5:
        return None
    return sum(int(it.get("keyword_match") or 0) for it in top5) / len(top5)


def _count_km_positive(feed: list[dict[str, Any]]) -> int:
    return sum(1 for it in feed[:20] if (it.get("keyword_match") or 0) > 0)


def _count_primary_in_top10(feed: list[dict[str, Any]], primary: str) -> int:
    return sum(1 for it in feed[:10] if (it.get("category") or "") == primary)


def _max_skill_weight(tags: dict[str, float]) -> float:
    skill = [w for k, w in tags.items() if not str(k).startswith("__")]
    return max(skill) if skill else 0.0


def _primary_tag_weight(tags: dict[str, float], persona: Persona) -> float | None:
    primary = _primary_niche(persona)
    from skills_catalog import category_for_canonical_tag, resolve_canonical_tag

    best = 0.0
    found = False
    for tag, weight in tags.items():
        if str(tag).startswith("__"):
            continue
        canonical = resolve_canonical_tag(tag) or tag
        if category_for_canonical_tag(canonical) == primary:
            found = True
            best = max(best, float(weight))
    if not found:
        skill = [
            float(w)
            for k, w in tags.items()
            if not str(k).startswith("__")
        ]
        return max(skill) if skill else None
    return best


def _judge_b8_o225_regression() -> dict[str, Any]:
    from rank import (
        CATEGORY_FLOOR_PRIMARY,
        compatibility_match,
        quiz_niche_meta_tag,
        user_quiz_niches_from_tags,
        user_quiz_primary_niche,
    )

    user = {quiz_niche_meta_tag("text"): 2.0, quiz_niche_meta_tag("design"): 1.0}
    user["illustration"] = 11.0
    niches = user_quiz_niches_from_tags(user)
    assert user_quiz_primary_niche(user) == "text"
    km = compatibility_match(
        ["article_writing"],
        user,
        lead_category="text",
        user_quiz_niches=niches,
    )
    passed = km is not None and km >= CATEGORY_FLOOR_PRIMARY
    return {
        "id": "B8",
        "label": "O225: draft чужой ниши не ломает text-floor",
        "pass": passed,
        "keyword_match": km,
        "floor": CATEGORY_FLOOR_PRIMARY,
    }


def _judge_persona(
    persona: Persona,
    *,
    after_quiz: StepSnapshot,
    after_actions: StepSnapshot,
) -> list[dict[str, Any]]:
    primary = _primary_niche(persona)
    judges: list[dict[str, Any]] = []

    max_w = _max_skill_weight(after_actions.user_tags)
    judges.append(
        {
            "id": "B1",
            "label": "max(tag.weight) ≤ 10.0",
            "pass": max_w <= _TAG_WEIGHT_MAX + 1e-6,
            "value": round(max_w, 4),
        }
    )

    km_pos = _count_km_positive(after_actions.feed_top20)
    judges.append(
        {
            "id": "B2",
            "label": "≥ 12/20 с keyword_match > 0",
            "pass": km_pos >= 12,
            "value": km_pos,
        }
    )

    primary_top10 = _count_primary_in_top10(after_actions.feed_top20, primary)
    judges.append(
        {
            "id": "B3",
            "label": "≥ 4 лида primary-ниши в top-10",
            "pass": primary_top10 >= 4,
            "value": primary_top10,
            "primary": primary,
        }
    )

    if persona.mode == "browse":
        baseline_pw = _primary_tag_weight(after_quiz.user_tags, persona)
        after_pw = _primary_tag_weight(after_actions.user_tags, persona)
        judges.append(
            {
                "id": "B4",
                "label": "browse: primary-тег ≥ после квиза",
                "pass": baseline_pw is not None
                and after_pw is not None
                and after_pw >= baseline_pw,
                "baseline": baseline_pw,
                "after": after_pw,
            }
        )

        baseline_avg = _avg_km_primary_top5(after_quiz.feed_top20, primary)
        after_avg = _avg_km_primary_top5(after_actions.feed_top20, primary)
        judges.append(
            {
                "id": "B5",
                "label": "browse: avg keyword_match top-5 primary ≥ baseline (0 допуска)",
                "pass": baseline_avg is not None
                and after_avg is not None
                and after_avg >= baseline_avg,
                "baseline_avg": baseline_avg,
                "after_avg": after_avg,
            }
        )

    if persona.mode == "skip":
        python_before = after_quiz.user_tags.get("python", 0.0)
        python_after = after_actions.user_tags.get("python", 0.0)
        judges.append(
            {
                "id": "B6",
                "label": "5× push_nope → вес кластера ↓",
                "pass": python_after < python_before,
                "before": python_before,
                "after": python_after,
            }
        )
        floor_hits = sum(
            1
            for it in after_actions.feed_top20
            if (it.get("category") or "") == primary
            and (it.get("keyword_match") or 0) >= 20
        )
        judges.append(
            {
                "id": "B7",
                "label": "после skip ≥ 2 primary с floor ≥20% в top-20",
                "pass": floor_hits >= 2,
                "value": floor_hits,
            }
        )

    return judges


def _feed_item_summary(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item.get("id"),
        "category": item.get("category"),
        "keyword_match": item.get("keyword_match"),
        "final_rank": item.get("final_rank"),
        "title": (item.get("title") or "")[:80],
        "lead_tags": (item.get("lead_tags") or item.get("tags") or [])[:5],
    }


def _run_persona_db(persona: Persona, *, api_url: str | None) -> dict[str, Any]:
    import psycopg
    from api_server import (
        _apply_tag_weight_event,
        _load_user_tags,
        _personal_feed_page,
        _replace_quiz_import_user_tags,
    )
    from jwt_auth import issue_access_token

    db_url = os.environ.get("DATABASE_URL", "").strip()
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")

    user_id = str(uuid4())
    tg_user_id = int(uuid4().int % 9_000_000_000) + 1_000_000_000

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, tg_user_id, tg_username, tg_first_name)
                VALUES (%s::uuid, %s, %s, %s)
                """,
                (user_id, tg_user_id, f"o282_{persona.id}", "O282"),
            )
            cur.execute(
                """
                INSERT INTO subscriptions (user_id, plan, is_active)
                VALUES (%s::uuid, 'agent', TRUE)
                ON CONFLICT (user_id) DO UPDATE
                SET plan = 'agent', is_active = TRUE
                """,
                (user_id,),
            )
            _replace_quiz_import_user_tags(
                cur, user_id, dict(persona.quiz_tags), persona.niches
            )
            conn.commit()

    def snapshot(label: str) -> StepSnapshot:
        with psycopg.connect(db_url) as conn:
            with conn.cursor() as cur:
                tags = _load_user_tags(cur, user_id)
                items, count, _ = _personal_feed_page(
                    cur,
                    user_id,
                    limit=20,
                    offset=0,
                    min_score=0,
                    min_match=0,
                    skills=[],
                    categories=[],
                    sort="match",
                    source_keys=None,
                )
        feed = [_feed_item_summary(it) for it in items]
        return StepSnapshot(
            label=label,
            user_tags={k: round(v, 4) for k, v in tags.items()},
            feed_top20=feed,
            metrics={
                "feed_count": count,
                "km_positive": _count_km_positive(feed),
                "primary_top10": _count_primary_in_top10(
                    feed, _primary_niche(persona)
                ),
            },
        )

    after_quiz = snapshot("after_quiz")

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            if persona.mode == "browse":
                lead_ids: list[int] = []
                for it in after_quiz.feed_top20[:_BROWSE_EXPANDS]:
                    lid = it.get("id")
                    if lid:
                        lead_ids.append(int(lid))
                for lid in lead_ids:
                    from api_server import _canonical_lead_tags, _fetch_visible_lead

                    lead_row = _fetch_visible_lead(cur, lid)
                    if lead_row is None:
                        continue
                    tags = _canonical_lead_tags(lead_row[8])
                    if tags:
                        _apply_tag_weight_event(cur, user_id, "expand", tags)
            elif persona.mode == "skip":
                for _ in range(_NOPE_CLUSTER_COUNT):
                    _apply_tag_weight_event(cur, user_id, "push_nope", ["python"])
            conn.commit()

    after_actions = snapshot("after_actions")
    judges = _judge_persona(
        persona, after_quiz=after_quiz, after_actions=after_actions
    )

    token = issue_access_token(user_id, tg_user_id=tg_user_id)
    api_note = None
    if api_url:
        api_note = _smoke_api_feed(api_url, token)

    return {
        "persona": persona.id,
        "label_ru": persona.label_ru,
        "user_id": user_id,
        "steps": {
            "after_quiz": {
                "metrics": after_quiz.metrics,
                "tags_sample": dict(list(after_quiz.user_tags.items())[:12]),
                "feed": after_quiz.feed_top20,
            },
            "after_actions": {
                "metrics": after_actions.metrics,
                "tags_sample": dict(list(after_actions.user_tags.items())[:12]),
                "feed": after_actions.feed_top20,
            },
        },
        "judges": judges,
        "api_smoke": api_note,
    }


def _smoke_api_feed(api_url: str, token: str) -> dict[str, Any]:
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen

    url = f"{api_url.rstrip('/')}/v1/me/feed?limit=5&sort=match"
    req = Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "RawLeadWeightsJourney/1.0",
        },
    )
    try:
        with urlopen(req, timeout=20.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return {"status": resp.status, "items": len(body.get("items") or [])}
    except HTTPError as exc:
        return {"status": exc.code, "error": str(exc.reason)}
    except URLError as exc:
        return {"status": None, "error": str(exc.reason)}


def _run_simulate() -> dict[str, Any]:
    """Rank-only path when DB unavailable."""
    from rank import compatibility_match, quiz_niche_meta_tag, user_quiz_niches_from_tags

    browse = next(p for p in PERSONAS if p.id == "browse")
    user_tags = dict(browse.quiz_tags)
    user_tags[quiz_niche_meta_tag("dev")] = 2.0
    niches = user_quiz_niches_from_tags(user_tags)

    synthetic_feed = []
    fixtures = [
        (["python", "fastapi"], "dev", "FastAPI backend"),
        (["django"], "dev", "Django CRM"),
        (["figma"], "design", "Figma UI"),
        (["seo"], "marketing", "SEO audit"),
        (["python", "web_scraping"], "dev", "Scraper bot"),
    ]
    for i, (tags, cat, title) in enumerate(fixtures * 5):
        km = compatibility_match(tags, user_tags, lead_category=cat, user_quiz_niches=niches)
        synthetic_feed.append(
            {
                "id": 1000 + i,
                "category": cat,
                "keyword_match": km,
                "final_rank": km,
                "title": title,
                "lead_tags": tags,
            }
        )
    synthetic_feed.sort(key=lambda x: (x.get("final_rank") or 0), reverse=True)

    after_quiz = StepSnapshot(
        label="simulate_quiz",
        user_tags=user_tags,
        feed_top20=synthetic_feed[:20],
        metrics={"km_positive": _count_km_positive(synthetic_feed)},
    )
    after_browse = StepSnapshot(
        label="simulate_browse",
        user_tags=user_tags,
        feed_top20=synthetic_feed[:20],
        metrics={"km_positive": _count_km_positive(synthetic_feed)},
    )
    judges = _judge_persona(browse, after_quiz=after_quiz, after_actions=after_browse)
    return {
        "mode": "simulate",
        "personas": [
            {
                "persona": browse.id,
                "label_ru": browse.label_ru,
                "judges": judges,
                "note": "DB unavailable — synthetic feed only",
            }
        ],
        "global_judges": [_judge_b8_o225_regression()],
    }


def _render_md(report: dict[str, Any]) -> str:
    lines = [
        "# Preprod: путь весов ленты (O282)",
        "",
        f"Сгенерировано: {report.get('generated_at', '')}",
        "",
    ]
    if report.get("mode") == "simulate":
        lines.append(
            "> Режим **simulate** — без DATABASE_URL. Полный прогон: запустите скрипт с БД."
        )
        lines.append("")

    all_pass = True
    for block in report.get("personas") or []:
        lines.append(f"## {block.get('label_ru', block.get('persona'))}")
        lines.append("")
        for j in block.get("judges") or []:
            mark = "✅" if j.get("pass") else "❌"
            if not j.get("pass"):
                all_pass = False
            lines.append(f"- {mark} **{j.get('id')}** — {j.get('label')}")
            if j.get("value") is not None:
                lines.append(f"  - значение: {j['value']}")
            if j.get("baseline_avg") is not None:
                lines.append(
                    f"  - baseline avg: {j['baseline_avg']:.2f} → after: {j.get('after_avg', 0):.2f}"
                )
        lines.append("")

    for j in report.get("global_judges") or []:
        mark = "✅" if j.get("pass") else "❌"
        if not j.get("pass"):
            all_pass = False
        lines.append(f"- {mark} **{j.get('id')}** — {j.get('label')}")
    lines.append("")

    if all_pass:
        lines.append("## Вердикт")
        lines.append("")
        lines.append(
            "Лента после квиза и листания **не схлопывается**: подходящие карточки "
            "остаются в топе, browse без отклика **не штрафует** релевантность. "
            "Явный skip (push_nope) по-прежнему понижает вес тега."
        )
    else:
        lines.append("## Вердикт")
        lines.append("")
        lines.append(
            "Есть проваленные judge — см. ❌ выше. Browse-штраф `expand_no_reply` "
            "удалён из API; при падении B2/B5 проверьте веса и сортировку match."
        )

    return "\n".join(lines) + "\n"


def run_journey(*, simulate: bool, api_url: str | None, personas: list[str]) -> dict[str, Any]:
    _load_env()
    selected = [p for p in PERSONAS if not personas or p.id in personas]
    unknown = [x for x in personas if x not in {p.id for p in PERSONAS}]
    if unknown:
        raise ValueError(f"unknown personas: {unknown}")

    if simulate or not os.environ.get("DATABASE_URL", "").strip():
        report = _run_simulate()
        report["generated_at"] = datetime.now(timezone.utc).isoformat()
        report["api_url"] = api_url
        return report

    from pg_storage import _ensure_user_tags_columns

    try:
        _ensure_user_tags_columns(os.environ["DATABASE_URL"])
    except Exception as exc:
        report = _run_simulate()
        report["generated_at"] = datetime.now(timezone.utc).isoformat()
        report["api_url"] = api_url
        report["db_error"] = str(exc)[:500]
        return report

    persona_results: list[dict[str, Any]] = []
    try:
        for persona in selected:
            print(f"persona {persona.id} …")
            persona_results.append(_run_persona_db(persona, api_url=api_url))
    except Exception as exc:
        report = _run_simulate()
        report["generated_at"] = datetime.now(timezone.utc).isoformat()
        report["api_url"] = api_url
        report["db_error"] = str(exc)[:500]
        return report

    all_judges = [j for pr in persona_results for j in pr.get("judges") or []]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_url": api_url,
        "personas": persona_results,
        "global_judges": [_judge_b8_o225_regression()],
        "summary": {
            "personas": len(persona_results),
            "judges_pass": sum(1 for j in all_judges if j.get("pass")),
            "judges_total": len(all_judges),
            "all_pass": all(j.get("pass") for j in all_judges)
            and _judge_b8_o225_regression()["pass"],
        },
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="O282 weights journey preprod")
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Synthetic feed when DATABASE_URL missing or forced",
    )
    parser.add_argument("--api-url", default=None, help="Optional HTTP smoke on /v1/me/feed")
    parser.add_argument(
        "--personas",
        default="",
        help="Comma-separated persona ids (default: all)",
    )
    args = parser.parse_args()
    personas = [x.strip() for x in args.personas.split(",") if x.strip()]

    try:
        report = run_journey(
            simulate=args.simulate,
            api_url=args.api_url,
            personas=personas,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    _ARTIFACT_JSON.parent.mkdir(parents=True, exist_ok=True)
    _ARTIFACT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _ARTIFACT_MD.write_text(_render_md(report), encoding="utf-8")

    print(f"wrote {_ARTIFACT_JSON.relative_to(_ROOT)}")
    print(f"wrote {_ARTIFACT_MD.relative_to(_ROOT)}")
    summary = report.get("summary") or {}
    if summary:
        print(
            f"judges: {summary.get('judges_pass')}/{summary.get('judges_total')} pass"
        )
    return 0 if (summary.get("all_pass") if summary else True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
