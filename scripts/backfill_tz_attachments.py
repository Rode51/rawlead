#!/usr/bin/env python3
"""O133-TZ-BACKFILL: re-fetch detail + enrich TZ attachments → UPDATE leads.body."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

import psycopg  # noqa: E402

from ai_reasons import merge_tz_attachment_into_reasons_json  # noqa: E402
from config import apply_profile_argv, load_config, load_radar_env  # noqa: E402
from lead_pipeline import _resolve_ingest_body  # noqa: E402
from listing import SOURCE_FL, SOURCE_KWORK, ListingProject  # noqa: E402
from tz_attachments import (  # noqa: E402
    has_extracted_attachment_marker,
    has_skipped_attachment_marker,
    infer_tz_attachment_from_body,
)

BACKFILL_SOURCES = frozenset({SOURCE_FL, SOURCE_KWORK})

_SELECT_BY_ID = """
SELECT id, source, external_id, title, body, url, budget_text, ai_reasons
FROM leads WHERE id = %s
"""

_SELECT_BY_EXT = """
SELECT id, source, external_id, title, body, url, budget_text, ai_reasons
FROM leads WHERE source = %s AND external_id = %s
"""

_SELECT_CANDIDATES = """
SELECT id, source, external_id, title, body, url, budget_text, ai_reasons
FROM leads
WHERE source = %s
  AND (body ILIKE %s OR body ILIKE %s)
  AND body NOT ILIKE %s
ORDER BY id DESC
LIMIT %s
"""


def strip_tz_attachment_blocks(text: str) -> str:
    """Убрать блоки [TZ attachment …] для идемпотентного re-enrich."""
    raw = text or ""
    idx = raw.find("[TZ attachment")
    if idx >= 0:
        return raw[:idx].rstrip()
    return raw.strip()


@dataclass(frozen=True)
class BackfillLead:
    lead_id: int
    source: str
    external_id: str
    title: str
    body: str
    url: str
    budget_text: str
    ai_reasons: Any


@dataclass(frozen=True)
class BackfillResult:
    lead_id: int
    source: str
    external_id: str
    old_len: int
    new_len: int
    marker: str
    applied: bool
    skipped: bool
    skip_reason: str = ""


def _row_to_lead(row: tuple) -> BackfillLead:
    return BackfillLead(
        lead_id=int(row[0]),
        source=str(row[1]),
        external_id=str(row[2]),
        title=str(row[3] or ""),
        body=str(row[4] or ""),
        url=str(row[5] or ""),
        budget_text=str(row[6] or ""),
        ai_reasons=row[7],
    )


def _reasons_json_str(raw: Any) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, (dict, list)):
        return json.dumps(raw, ensure_ascii=False)
    s = str(raw).strip()
    return s or None


def marker_label(body: str) -> str:
    if has_extracted_attachment_marker(body):
        return "extracted"
    if has_skipped_attachment_marker(body):
        return "skipped"
    return "none"


def build_listing_project(lead: BackfillLead) -> ListingProject:
    base = strip_tz_attachment_blocks(lead.body)
    try:
        project_id = int(lead.external_id)
    except ValueError:
        project_id = abs(hash((lead.source, lead.external_id))) % (2**31 - 1)
    return ListingProject(
        project_id=project_id,
        title=lead.title,
        budget_text=lead.budget_text,
        url=lead.url,
        published_at="",
        listing_snippet=base,
        source=lead.source,
    )


def resolve_backfill_body(
    lead: BackfillLead,
    cfg,
    errors: list[str],
) -> tuple[str, dict | None]:
    if lead.source not in BACKFILL_SOURCES:
        raise ValueError(f"unsupported source: {lead.source}")
    body, tz, _ = _resolve_ingest_body(build_listing_project(lead), cfg, errors)
    return body, tz


def apply_lead_update(
    cur,
    lead: BackfillLead,
    new_body: str,
    tz_dict: dict[str, Any] | None,
) -> None:
    reasons = _reasons_json_str(lead.ai_reasons)
    tz = tz_dict if tz_dict is not None else infer_tz_attachment_from_body(new_body)
    merged = merge_tz_attachment_into_reasons_json(reasons, tz)
    cur.execute(
        """
        UPDATE leads
        SET body = %s,
            last_fetch_ok_at = NOW(),
            ai_reasons = COALESCE(%s::jsonb, ai_reasons)
        WHERE id = %s
        """,
        (new_body, merged, lead.lead_id),
    )


def fetch_leads(
    cur,
    *,
    lead_id: int | None,
    external_id: str | None,
    source: str | None,
    limit: int,
) -> list[BackfillLead]:
    if lead_id is not None:
        cur.execute(_SELECT_BY_ID, (lead_id,))
        row = cur.fetchone()
        return [_row_to_lead(row)] if row else []

    if external_id and source:
        cur.execute(_SELECT_BY_EXT, (source, external_id))
        row = cur.fetchone()
        return [_row_to_lead(row)] if row else []

    if source and limit > 0:
        cur.execute(
            _SELECT_CANDIDATES,
            (source, "%вложен%", "%прикреп%", "%[TZ attachment%", limit),
        )
        return [_row_to_lead(r) for r in cur.fetchall()]

    return []


def process_lead(
    lead: BackfillLead,
    cfg,
    *,
    apply: bool,
    cur=None,
) -> BackfillResult:
    if lead.source not in BACKFILL_SOURCES:
        return BackfillResult(
            lead_id=lead.lead_id,
            source=lead.source,
            external_id=lead.external_id,
            old_len=len(lead.body),
            new_len=len(lead.body),
            marker=marker_label(lead.body),
            applied=False,
            skipped=True,
            skip_reason="unsupported_source",
        )

    errors: list[str] = []
    new_body, tz_dict = resolve_backfill_body(lead, cfg, errors)
    old_len = len(lead.body)
    new_len = len(new_body)
    label = marker_label(new_body)

    if new_body == lead.body:
        return BackfillResult(
            lead_id=lead.lead_id,
            source=lead.source,
            external_id=lead.external_id,
            old_len=old_len,
            new_len=new_len,
            marker=label,
            applied=False,
            skipped=True,
            skip_reason="unchanged",
        )

    if apply:
        if cur is None:
            raise RuntimeError("apply requires db cursor")
        apply_lead_update(cur, lead, new_body, tz_dict)

    return BackfillResult(
        lead_id=lead.lead_id,
        source=lead.source,
        external_id=lead.external_id,
        old_len=old_len,
        new_len=new_len,
        marker=label,
        applied=apply,
        skipped=False,
    )


def _print_result(result: BackfillResult, *, dry_run: bool) -> None:
    mode = "dry-run" if dry_run else ("applied" if result.applied else "pending")
    skip = f" skip={result.skip_reason}" if result.skipped else ""
    print(
        f"id={result.lead_id} {result.source}:{result.external_id} "
        f"old_len={result.old_len} new_len={result.new_len} "
        f"marker={result.marker} {mode}{skip}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill TZ attachments into leads.body (fl/kwork only)",
    )
    parser.add_argument("--profile", default="site", choices=("site", "legacy"))
    parser.add_argument("--lead-id", type=int, default=None)
    parser.add_argument("--external-id", type=str, default=None)
    parser.add_argument("--source", type=str, default=None, choices=("fl", "kwork"))
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Печать old_len→new_len без UPDATE (по умолчанию, если нет --apply)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Записать body + last_fetch_ok_at (+ ai_reasons.tz_attachment) в Neon",
    )
    args = parser.parse_args()

    apply_profile_argv()
    load_radar_env()
    cfg = load_config()
    if not cfg.database_url.strip():
        print("DATABASE_URL empty")
        return 1

    dry_run = not args.apply
    if args.dry_run and args.apply:
        print("use either --dry-run or --apply, not both")
        return 1

    has_target = (
        args.lead_id is not None
        or (args.external_id and args.source)
        or (args.source and args.limit > 0)
    )
    if not has_target:
        print("need --lead-id, or --external-id + --source, or --source + --limit")
        return 1

    if args.external_id and not args.source:
        print("--external-id requires --source")
        return 1

    errors: list[str] = []
    updated = 0
    skipped = 0

    with psycopg.connect(cfg.database_url) as conn:
        with conn.cursor() as cur:
            leads = fetch_leads(
                cur,
                lead_id=args.lead_id,
                external_id=args.external_id,
                source=args.source,
                limit=max(1, args.limit),
            )
            if not leads:
                print("no leads matched")
                return 1

            for lead in leads:
                result = process_lead(
                    lead,
                    cfg,
                    apply=args.apply,
                    cur=cur if args.apply else None,
                )
                _print_result(result, dry_run=dry_run)
                if result.skipped:
                    skipped += 1
                elif result.applied:
                    updated += 1

            if args.apply:
                conn.commit()

    if errors:
        for e in errors[-5:]:
            print(" err:", e)

    print(f"done updated={updated} skipped={skipped} dry_run={dry_run}")
    return 0 if updated > 0 or skipped > 0 or dry_run else 1


if __name__ == "__main__":
    raise SystemExit(main())
