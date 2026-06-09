"""One-shot: Neon лиды без L1 → FILTERS_SITE → analyze_lite → update_after_lite.



Запуск (site):

  .venv\\Scripts\\python.exe scripts\\replay_neon_lite_site.py --profile site --dry-run

  .venv\\Scripts\\python.exe scripts\\replay_neon_lite_site.py --profile site --limit 20

  .venv\\Scripts\\python.exe scripts\\replay_neon_lite_site.py --profile site --tg-replay --limit 200

  .venv\\Scripts\\python.exe scripts\\replay_neon_lite_site.py --profile site --backfill-missing --dry-run

  .venv\\Scripts\\python.exe scripts\\replay_neon_lite_site.py --profile site --backfill-missing --limit 30

  .venv\\Scripts\\python.exe scripts\\replay_neon_lite_site.py --profile site --fresh-l1 --limit 200

  .venv\\Scripts\\python.exe scripts\\replay_neon_lite_site.py --profile site --o97-replay --limit 80

  .venv\\Scripts\\python.exe scripts\\replay_neon_lite_site.py --profile site --tools-replay --limit 80

  .venv\\Scripts\\python.exe scripts\\replay_neon_lite_site.py --profile site --tools-replay-force --limit 71

"""



from __future__ import annotations



import argparse

import sys

for _stream in (sys.stdout, sys.stderr):
    enc = getattr(_stream, "encoding", None) or ""
    if enc.lower() != "utf-8":
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass

from collections import defaultdict
from datetime import date, datetime, timezone

from pathlib import Path



_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(_ROOT / "src"))



from ai_analyze import analyze_lite

from budget import meets_min_budget

from config import apply_profile_argv, load_config, load_radar_env, radar_profile

from filters import default_listing_filter

from fl_parser import fetch_listing_projects

from kwork_parser import fetch_listing_projects as fetch_kwork_listing

from listing import ListingProject

from listing_dedup import listing_content_hash

from lead_pipeline import replay_tools_for_rows
from pg_storage import NeonLeadRow, pg_storage_from_config

from public_feed import public_feed_sources

from storage import storage_from_config



_LIVE_FETCHERS: dict[str, object] = {

    "fl": fetch_listing_projects,

    "kwork": fetch_kwork_listing,

}


def _normalize_tg_source(source: str) -> str:
    s = (source or "").strip()
    if not s.startswith("tg:"):
        return s
    try:
        n = int(s[3:])
        if n > 0:
            return f"tg:-100{n}"
    except ValueError:
        pass
    return s


def _listing_from_row(row: NeonLeadRow) -> ListingProject:
    project = row.to_listing()
    norm = _normalize_tg_source(project.source)
    if norm == project.source:
        return project
    return ListingProject(
        project_id=project.project_id,
        title=project.title,
        budget_text=project.budget_text,
        url=project.url,
        published_at=project.published_at,
        listing_snippet=project.listing_snippet,
        source=norm,
        listing_category=project.listing_category,
        chat_invite_url=project.chat_invite_url,
        chat_title=project.chat_title,
    )


def _fetch_tg_replay_rows(
    pg,
    *,
    limit: int,
    errors: list[str],
) -> list[NeonLeadRow]:
    """TG в Neon: без L1 или is_visible=false (one-shot после PUBLIC_FEED_SOURCES)."""
    lim = max(1, min(int(limit), 500))
    try:
        with pg.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, source, external_id, title, body, url,
                           budget_text, COALESCE(category, '')
                    FROM leads
                    WHERE source LIKE 'tg:%%'
                      AND (
                        (ai_verdict IS NULL AND ai_score IS NULL)
                        OR is_visible = FALSE
                      )
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (lim,),
                )
                rows = cur.fetchall()
        return [
            NeonLeadRow(
                lead_id=int(r[0]),
                source=str(r[1]),
                external_id=str(r[2]),
                title=str(r[3] or ""),
                body=str(r[4] or ""),
                url=str(r[5] or ""),
                budget_text=str(r[6] or ""),
                category=str(r[7] or ""),
            )
            for r in rows
        ]
    except Exception as exc:
        errors.append(f"tg_replay:fetch:{exc}")
        return []


def _run_l1_replay(
    args,
    cfg,
    pg,
    rows: list[NeonLeadRow],
    errors: list[str],
    *,
    label: str,
) -> int:
    print(f"{label}: {len(rows)} (limit={args.limit})")
    if errors:
        for e in errors:
            print(f"  err: {e}")

    if args.dry_run:
        for row in rows[:10]:
            print(f"  id={row.lead_id} {row.source}:{row.external_id} {row.title[:60]}")
        if len(rows) > 10:
            print(f"  … ещё {len(rows) - 10}")
        return 0

    word_filter = default_listing_filter()
    ok = 0
    skipped = 0
    for row in rows:
        project = _listing_from_row(row)
        snippet = (project.listing_snippet or project.title or "").strip()
        if not word_filter.accepts_listing(project, wide=cfg.filter_wide):
            skipped += 1
            print(f"  skip:filter {row.source}:{row.external_id}")
            continue
        log_prefix = f"{row.source}:id={row.external_id} replay:"
        lite = analyze_lite(
            cfg,
            title=project.title,
            budget_text=project.budget_text,
            snippet=snippet,
            url=project.url,
            errors=errors,
            log_prefix=log_prefix,
        )
        pg.update_after_lite(
            project,
            lite=lite,
            errors=errors,
            body_snippet=snippet,
        )
        ok += 1
        verdict = lite.verdict if lite else "?"
        print(f"  L1 {row.source}:{row.external_id} → {verdict}")

    print(f"Готово: L1={ok} filter_skip={skipped} errors={len(errors)}")
    return 0 if not errors else 1





def _sqlite_missing_in_neon(

    storage,

    pg,

    sources: list[str],

    errors: list[str],

) -> list[tuple[str, int]]:

    pairs = storage.list_project_ids(sources)

    by_source: dict[str, list[str]] = defaultdict(list)

    for src, pid in pairs:

        by_source[src].append(str(pid))

    missing: list[tuple[str, int]] = []

    for src, ids in by_source.items():

        present = pg.external_ids_in_neon(src, ids, errors)

        for s, pid in pairs:

            if s == src and str(pid) not in present:

                missing.append((s, pid))

    return missing





def _fetch_live_map(

    cfg,

    sources: list[str],

    errors: list[str],

) -> dict[tuple[str, int], ListingProject]:

    live: dict[tuple[str, int], ListingProject] = {}

    for src in sources:

        fetch_fn = _LIVE_FETCHERS.get(src)

        if fetch_fn is None:

            continue

        try:

            projects = fetch_fn(cfg)

        except Exception as exc:

            errors.append(f"{src}:fetch:{exc}")

            continue

        for p in projects:

            live[(p.source, p.project_id)] = p

    return live





def _backfill_one(

    project: ListingProject,

    *,

    cfg,

    pg,

    word_filter,

    errors: list[str],

) -> bool:

    fingerprint = listing_content_hash(

        project.title, project.listing_snippet or project.title

    )

    ingest_body = (project.listing_snippet or project.title or "").strip()

    ext_id = str(project.project_id)



    if not pg.lead_exists(project.source, ext_id, errors):

        if not pg.record_new_lead(

            project,

            errors,

            content_hash=fingerprint,

            body=ingest_body,

        ):

            if pg.lead_exists(project.source, ext_id, errors):

                pass

            else:

                print(

                    f"  skip:neon_insert {project.source}:{ext_id} "

                    "(content_hash dup?)"

                )

                return False



    if not word_filter.accepts_listing(project, wide=cfg.filter_wide):

        print(f"  skip:filter {project.source}:{ext_id}")

        return False



    if cfg.ai_active and not meets_min_budget(project.budget_text, cfg.min_budget_rub):

        print(f"  skip:budget {project.source}:{ext_id}")

        return False



    snippet = ingest_body

    log_prefix = f"{project.source}:id={ext_id} backfill:"

    lite = analyze_lite(

        cfg,

        title=project.title,

        budget_text=project.budget_text,

        snippet=snippet,

        url=project.url,

        errors=errors,

        log_prefix=log_prefix,

    )

    pg.update_after_lite(

        project,

        lite=lite,

        errors=errors,

        body_snippet=snippet,

    )

    verdict = lite.verdict if lite else "?"

    print(f"  L1 {project.source}:{ext_id} → {verdict}")

    return True





def _run_backfill_missing(args, cfg, pg, errors: list[str]) -> int:

    sources = sorted(public_feed_sources())

    storage = storage_from_config(cfg)

    sqlite_missing = _sqlite_missing_in_neon(storage, pg, sources, errors)

    live_map = _fetch_live_map(cfg, sources, errors)



    targets: dict[tuple[str, int], ListingProject] = {}

    for key, project in live_map.items():

        if not pg.lead_exists(project.source, str(project.project_id), errors):

            targets[key] = project



    sqlite_only = 0

    for src, pid in sqlite_missing:

        key = (src, pid)

        if key in live_map:

            targets[key] = live_map[key]

        else:

            sqlite_only += 1



    print(

        f"sqlite без Neon: {len(sqlite_missing)} | "

        f"на живой ленте: {len(targets)} | "

        f"sqlite-only (нет на ленте): {sqlite_only}"

    )



    if args.dry_run:

        for key in list(targets.keys())[:10]:

            p = targets[key]

            print(f"  {p.source}:{p.project_id} {p.title[:60]}")

        if len(targets) > 10:

            print(f"  … ещё {len(targets) - 10}")

        return 0



    word_filter = default_listing_filter()

    ok = 0

    lim = max(1, args.limit)

    for key in list(targets.keys())[:lim]:

        if _backfill_one(

            targets[key], cfg=cfg, pg=pg, word_filter=word_filter, errors=errors

        ):

            ok += 1



    print(f"Готово backfill: L1={ok} errors={len(errors)}")

    return 0 if not errors else 1





def _parse_since(raw: str) -> datetime | None:
    text = (raw or "").strip()
    if not text:
        return None
    parsed = date.fromisoformat(text)
    return datetime(parsed.year, parsed.month, parsed.day, tzinfo=timezone.utc)


def _run_tools_replay(
    args,
    cfg,
    pg,
    rows: list[NeonLeadRow],
    errors: list[str],
    *,
    label: str,
) -> int:
    if args.dry_run:
        print(f"{label}: dry-run {len(rows)} rows")
        for row in rows[:10]:
            print(f"  id={row.lead_id} {row.source}:{row.external_id} {row.title[:50]}")
        if len(rows) > 10:
            print(f"  … ещё {len(rows) - 10}")
        return 0
    if not cfg.ai_active:
        print("AI не активен — tools replay пропущен", file=sys.stderr)
        return 2
    ok = replay_tools_for_rows(cfg, pg, rows, errors=errors)
    print(f"{label}: tools ok={ok}/{len(rows)} errors={len(errors)}")
    return 0 if ok > 0 or not errors else 1


def main() -> int:

    parser = argparse.ArgumentParser(description="Replay L1 для Neon (site only)")

    parser.add_argument("--dry-run", action="store_true", help="Только SELECT, без L1")

    parser.add_argument("--limit", type=int, default=50, help="Макс. строк за прогон")

    parser.add_argument(

        "--backfill-missing",

        action="store_true",

        help="Живая лента ∪ sqlite-only → INSERT Neon + L1",

    )

    parser.add_argument(
        "--tg-replay",
        action="store_true",
        help="TG source LIKE tg:%% — L1 + is_visible (one-shot § TG-FEED-SOURCES)",
    )

    parser.add_argument(
        "--o97-replay",
        action="store_true",
        help="O97 backfill: re-L1 для visible лидов без complexity в ai_reasons",
    )

    parser.add_argument(
        "--o97-replay-force",
        action="store_true",
        help="O97 re-bench: re-L1 для последних visible лидов с L1 (после правки промпта)",
    )

    parser.add_argument(
        "--fresh-l1",
        action="store_true",
        help="L1 для последних N id DESC (§ FEED-FRESHNESS one-shot)",
    )

    parser.add_argument(
        "--since",
        default="",
        help="O97 re-bench: created_at >= YYYY-MM-DD (с --o97-replay-force)",
    )

    parser.add_argument(
        "--lead-ids",
        default="",
        help="Точечный re-L1: id через запятую (judge sample)",
    )

    parser.add_argument(
        "--tools-replay",
        action="store_true",
        help="O98: L2 tools-only для visible без tools_required",
    )

    parser.add_argument(
        "--tools-replay-force",
        action="store_true",
        help="O98: перезаписать tools_required у последних visible с L1 (bench)",
    )

    parser.add_argument("--profile", default="", help="legacy|site (default: env)")

    args, _rest = parser.parse_known_args()

    if args.profile:

        sys.argv = [sys.argv[0], "--profile", args.profile.strip()] + [

            a for a in sys.argv[1:] if a not in ("--profile", args.profile.strip())

        ]

    apply_profile_argv()

    load_radar_env()

    if radar_profile() != "site":

        print("replay_neon_lite_site: только RADAR_PROFILE=site", file=sys.stderr)

        return 2



    cfg = load_config()

    pg = pg_storage_from_config(cfg)

    if pg is None or not pg.enabled:

        print("DATABASE_URL не задан — нечего replay", file=sys.stderr)

        return 1



    errors: list[str] = []



    if args.backfill_missing:

        return _run_backfill_missing(args, cfg, pg, errors)



    if args.tg_replay:
        rows = _fetch_tg_replay_rows(pg, limit=args.limit, errors=errors)
        return _run_l1_replay(args, cfg, pg, rows, errors, label="TG replay")

    if args.lead_ids.strip():
        raw_ids = [p.strip() for p in args.lead_ids.split(",") if p.strip()]
        lead_ids: list[int] = []
        for p in raw_ids:
            try:
                lead_ids.append(int(p))
            except ValueError:
                print(f"skip:invalid lead id {p!r}", file=sys.stderr)
        rows = pg.fetch_leads_by_ids(lead_ids, errors=errors)
        if args.tools_replay or args.tools_replay_force:
            label = "Lead-ids tools replay"
            if args.tools_replay_force:
                label += " (force)"
            return _run_tools_replay(args, cfg, pg, rows, errors, label=label)
        return _run_l1_replay(args, cfg, pg, rows, errors, label="Lead-ids replay")

    if args.tools_replay or args.tools_replay_force:
        since = _parse_since(args.since) if args.since else None
        if args.tools_replay_force:
            rows = pg.fetch_visible_leads_with_l1(
                limit=args.limit,
                order_desc=True,
                since=since,
                errors=errors,
            )
            label = "O98 tools re-bench (force)"
        else:
            rows = pg.fetch_leads_missing_tools(limit=args.limit, errors=errors)
            label = "O98 tools backfill"
        if since is not None:
            label += f" since={args.since.strip()}"
        return _run_tools_replay(args, cfg, pg, rows, errors, label=label)

    if args.o97_replay or args.o97_replay_force:
        since = _parse_since(args.since) if args.since else None
        if args.o97_replay_force:
            rows = pg.fetch_visible_leads_with_l1(
                limit=args.limit,
                order_desc=True,
                since=since,
                errors=errors,
            )
            label = "O97 re-bench (force)"
        else:
            rows = pg.fetch_leads_missing_complexity(
                limit=args.limit,
                order_desc=not bool(since),
                since=since,
                errors=errors,
            )
            label = "O97 complexity backfill"
        if since is not None:
            label += f" since={args.since.strip()}"
        return _run_l1_replay(args, cfg, pg, rows, errors, label=label)

    if args.fresh_l1:
        backlog = pg.count_leads_missing_l1(errors=errors)
        print(f"Очередь без L1: {backlog}")
        rows = pg.fetch_leads_missing_l1(
            limit=args.limit, order_desc=True, errors=errors
        )
        return _run_l1_replay(
            args, cfg, pg, rows, errors, label="Fresh L1 (id DESC)"
        )

    rows = pg.fetch_leads_missing_l1(
        limit=args.limit, order_desc=True, errors=errors
    )
    return _run_l1_replay(args, cfg, pg, rows, errors, label="Найдено без L1")





if __name__ == "__main__":

    raise SystemExit(main())

