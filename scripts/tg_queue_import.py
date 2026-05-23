"""Импорт каналов из TG_CHANNELS_EXPORT.txt в TG_JOIN_QUEUE.csv (волна 3)."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from tg_join_lib import read_lines, read_queue_csv, write_queue_csv  # noqa: E402

EXPORT = _ROOT / "docs" / "ops" / "TG_CHANNELS_EXPORT.txt"
BLOCKLIST = _ROOT / "docs" / "ops" / "TG_JOIN_BLOCKLIST.txt"
QUEUE = _ROOT / "docs" / "ops" / "TG_JOIN_QUEUE.csv"

ACCOUNTS = ("acc1", "acc2", "acc3")
WAVE = "3"
NOTES = "волна3"


def normalize_link(link: str) -> str:
    s = link.strip()
    if not s:
        return ""
    if s.startswith("t.me/"):
        s = "https://" + s
    elif s.startswith("http://"):
        s = "https://" + s[7:]
    parsed = urlparse(s)
    host = (parsed.hostname or "").lower()
    if host in ("t.me", "telegram.me"):
        host = "t.me"
    path = parsed.path.rstrip("/")
    if not path:
        path = "/"
    return urlunparse(("https", host, path, "", parsed.query, ""))


def link_display_name(link: str) -> str:
    path = urlparse(link).path.strip("/")
    if path.startswith("+"):
        return f"invite:{path[1:8]}…" if len(path) > 9 else f"invite:{path[1:]}"
    return path.split("/")[-1] or link


def load_blocklist(path: Path) -> set[str]:
    return {normalize_link(ln) for ln in read_lines(path) if normalize_link(ln)}


def load_export(path: Path) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for ln in read_lines(path):
        norm = normalize_link(ln)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        out.append(norm)
    return out


def account_at(index: int) -> str:
    return ACCOUNTS[index % len(ACCOUNTS)]


def run_import(*, dry_run: bool) -> int:
    if not EXPORT.is_file():
        print(f"Нет файла: {EXPORT}")
        return 1

    blocklist = load_blocklist(BLOCKLIST)
    export_links = load_export(EXPORT)
    fieldnames, rows = read_queue_csv(QUEUE)

    if not fieldnames:
        fieldnames = [
            "wave",
            "account",
            "status",
            "name",
            "link",
            "chat_id",
            "notes",
        ]

    existing_by_link: dict[str, dict[str, str]] = {}
    for row in rows:
        norm = normalize_link(row.get("link", ""))
        if norm:
            existing_by_link[norm] = row

    stats = {
        "added": 0,
        "skip_done": 0,
        "skip_duplicate": 0,
        "skip_blocklist": 0,
        "by_acc": {a: 0 for a in ACCOUNTS},
    }
    new_rows: list[dict[str, str]] = []
    pending_before = sum(
        1 for r in rows if r.get("status", "").strip().lower() == "pending"
    )
    assign_index = pending_before

    for link in export_links:
        if link in blocklist:
            stats["skip_blocklist"] += 1
            continue
        if link in existing_by_link:
            status = existing_by_link[link].get("status", "").strip().lower()
            if status == "done":
                stats["skip_done"] += 1
            else:
                stats["skip_duplicate"] += 1
            continue

        acc = account_at(assign_index)
        assign_index += 1
        new_rows.append(
            {
                "wave": WAVE,
                "account": acc,
                "status": "pending",
                "name": link_display_name(link),
                "link": link,
                "chat_id": "",
                "notes": NOTES,
            }
        )
        stats["added"] += 1
        stats["by_acc"][acc] += 1

    out_rows = rows + new_rows

    mode = "DRY-RUN" if dry_run else "WRITE"
    print(f"[{mode}] EXPORT: {len(export_links)} уникальных ссылок")
    print(f"  добавлено pending: {stats['added']}")
    print(f"  пропуск done:       {stats['skip_done']}")
    print(f"  пропуск дубль:      {stats['skip_duplicate']}")
    print(f"  пропуск blocklist:  {stats['skip_blocklist']}")
    for acc in ACCOUNTS:
        print(f"  новых на {acc}:      {stats['by_acc'][acc]}")
    pending_after = pending_before + stats["added"]
    print(f"  pending всего:      {pending_after} (было {pending_before})")

    if not dry_run and new_rows:
        write_queue_csv(fieldnames, out_rows, QUEUE)
        print(f"Записано: {QUEUE}")
    elif not dry_run:
        print("CSV без изменений.")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Импорт TG_CHANNELS_EXPORT.txt → TG_JOIN_QUEUE.csv",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только счётчики, без записи CSV",
    )
    args = parser.parse_args()
    raise SystemExit(run_import(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
