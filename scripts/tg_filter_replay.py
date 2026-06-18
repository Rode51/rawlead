"""O207-t3: offline filter replay on tg_history_sample.json (no Telethon, no L1 by default)."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from config import load_config  # noqa: E402
from filters import (  # noqa: E402
    ListingWordFilter,
    TG_WIDE_SOFT_STOPS,
    default_listing_filter,
    tg_filter_soft_bypass,
)
from listing import ListingProject, telegram_source  # noqa: E402
from tg_spam_filter import is_tg_spam  # noqa: E402

_OWNER_LABELS = frozenset({"vacancy", "noise", "unsure"})


def _filter_reason(
    word_filter: ListingWordFilter,
    title: str,
    snippet: str,
    *,
    wide: bool,
    soft_bypass: bool = False,
) -> str | None:
    if not word_filter.rejects(title, snippet, wide=wide, soft_bypass=soft_bypass):
        return None
    hay = word_filter.haystack(title, snippet)
    soft_skip = (
        frozenset(token.casefold() for token in TG_WIDE_SOFT_STOPS)
        if soft_bypass
        else frozenset()
    )
    for token in word_filter.stop:
        if token.casefold() in soft_skip:
            continue
        if token.casefold() in hay:
            return f"stop:{token}"
    if not wide:
        return "no_take_keyword"
    return "filter_reject"


def replay_row(
    row: dict,
    *,
    word_filter: ListingWordFilter,
    filter_wide: bool,
) -> dict:
    owner_label = row.get("owner_label")
    if owner_label is not None and owner_label not in _OWNER_LABELS:
        owner_label = None

    out = {
        "account": row.get("account"),
        "chat_id": row.get("chat_id"),
        "msg_id": row.get("msg_id"),
        "chat_title": row.get("chat_title"),
        "title": row.get("title"),
        "body_preview": row.get("body_preview"),
        "parse_ok": bool(row.get("parse_ok")),
        "owner_label": owner_label,
    }

    if not out["parse_ok"]:
        out.update(
            {
                "would_spam": False,
                "filter_pass": False,
                "filter_reason": "parse_skip",
                "stage": "parse_skip",
            }
        )
        return out

    title = str(row.get("title") or "")
    snippet = str(row.get("body_preview") or title)
    spam = is_tg_spam(title, snippet)
    soft_bypass = tg_filter_soft_bypass(
        title, snippet, wide=filter_wide, source="tg:replay"
    )
    reason = _filter_reason(
        word_filter, title, snippet, wide=filter_wide, soft_bypass=soft_bypass
    )
    filter_pass = reason is None

    if spam:
        stage = "spam"
    elif not filter_pass:
        stage = "filter"
    else:
        stage = "pass"

    out.update(
        {
            "would_spam": spam,
            "filter_pass": filter_pass and not spam,
            "filter_reason": "tg_spam" if spam else reason,
            "stage": stage,
        }
    )
    return out


def replay_sample(
    sample: dict,
    *,
    word_filter: ListingWordFilter | None = None,
    filter_wide: bool | None = None,
) -> dict:
    cfg = load_config()
    wf = word_filter or default_listing_filter()
    wide = cfg.filter_wide if filter_wide is None else filter_wide
    if isinstance(sample, list):
        rows_in = sample
    else:
        rows_in = sample.get("rows") or []

    replayed = [replay_row(row, word_filter=wf, filter_wide=wide) for row in rows_in]
    summary = Counter()
    for r in replayed:
        if not r.get("parse_ok"):
            summary["parse_skip"] += 1
            continue
        if r.get("would_spam"):
            summary["would_spam"] += 1
        elif not r.get("filter_pass"):
            summary["would_skip_filter"] += 1
        else:
            summary["would_pass_filter"] += 1
    summary["total"] = len(replayed)

    return {
        "source": sample.get("generated_at", ""),
        "filter_wide": wide,
        "summary": dict(summary),
        "rows": replayed,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="TG filter replay (O207-t3)")
    parser.add_argument("--in", dest="in_path", default="data/tg_history_sample.json")
    parser.add_argument("--out", default="data/tg_filter_replay.json")
    parser.add_argument(
        "--with-l1",
        action="store_true",
        help="Reserved: dry-run L1 (OpenRouter cost). Not run in O207 ship.",
    )
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.with_l1:
        print(
            "warning: --with-l1 not implemented in O207; use owner labels + separate O207b",
            file=sys.stderr,
        )

    in_path = Path(args.in_path)
    if not in_path.is_absolute():
        in_path = _ROOT / in_path
    sample = json.loads(in_path.read_text(encoding="utf-8"))
    report = replay_sample(sample)

    out = Path(args.out)
    if not out.is_absolute():
        out = _ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    header = {
        "_owner_labeling": (
            "Optional owner_label per row: vacancy | noise | unsure | null. "
            "Copy sample to data/tg_history_sample_labeled.json, fill labels, "
            "replay with --in that file."
        ),
    }
    payload = {**header, **report}
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"wrote {out}", file=sys.stderr)


def project_from_row(row: dict) -> ListingProject:
    chat_id = int(row.get("chat_id") or 0)
    return ListingProject(
        project_id=int(row.get("msg_id") or 0),
        title=str(row.get("title") or ""),
        budget_text="",
        url="",
        published_at=str(row.get("date_iso") or ""),
        listing_snippet=str(row.get("body_preview") or ""),
        source=telegram_source(chat_id),
        chat_title=str(row.get("chat_title") or ""),
    )


if __name__ == "__main__":
    main()
