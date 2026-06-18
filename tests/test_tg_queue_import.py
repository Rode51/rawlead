"""O248: tg_queue_import xlsx dedupe and wave 5 filter."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "scripts"))

from tg_join_lib import read_queue_csv  # noqa: E402
from tg_queue_import import (  # noqa: E402
    FIELDNAMES_V4,
    XlsxEntry,
    build_v4_rows,
    filter_xlsx_entries,
    load_existing_by_link,
    normalize_link,
)


def _write_queue(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES_V4[:7])
        writer.writeheader()
        writer.writerows(rows)


def test_normalize_link_https_t_me() -> None:
    assert normalize_link("http://t.me/foo/") == "https://t.me/foo"


def test_filter_xlsx_dedupe_done_blocklist_droplist(tmp_path: Path) -> None:
    ops = tmp_path / "ops"
    ops.mkdir()
    v2 = ops / "TG_JOIN_QUEUE_v2.csv"
    _write_queue(
        v2,
        [
            {
                "wave": "2",
                "account": "acc1",
                "status": "done",
                "name": "done_chat",
                "link": "https://t.me/done_chat",
                "chat_id": "1",
                "notes": "",
            },
            {
                "wave": "2",
                "account": "acc2",
                "status": "pending",
                "name": "pending_dup",
                "link": "https://t.me/pending_dup",
                "chat_id": "",
                "notes": "",
            },
        ],
    )
    existing = load_existing_by_link([v2])
    entries = [
        XlsxEntry("A", "https://t.me/new_one", 6000, "chat"),
        XlsxEntry("B", "https://t.me/done_chat", 7000, "channel"),
        XlsxEntry("C", "https://t.me/pending_dup", 8000, "chat"),
        XlsxEntry("D", "https://t.me/low_subs", 5000, "chat"),
        XlsxEntry("E", "https://t.me/blocked", 9000, "chat"),
        XlsxEntry("F", "https://t.me/dropped", 10000, "channel"),
    ]
    accepted, stats = filter_xlsx_entries(
        entries,
        min_subscribers=5000,
        existing_by_link=existing,
        blocklist={"https://t.me/blocked"},
        droplist={"https://t.me/dropped"},
    )
    assert stats["skip_subscribers"] == 1
    assert stats["skip_done"] == 1
    assert stats["skip_duplicate"] == 1
    assert stats["skip_blocklist"] == 1
    assert stats["skip_droplist"] == 1
    assert stats["added"] == 1
    assert [entry.link for entry in accepted] == ["https://t.me/new_one"]


def test_build_v4_rows_round_robin() -> None:
    entries = [
        XlsxEntry("One", "https://t.me/a", 6000, "chat"),
        XlsxEntry("Two", "https://t.me/b", 7000, "channel"),
        XlsxEntry("Three", "https://t.me/c", 8000, "chat"),
        XlsxEntry("Four", "https://t.me/d", 9000, "channel"),
    ]
    rows = build_v4_rows(entries, pending_before=1)
    assert [row["account"] for row in rows] == ["acc2", "acc3", "acc1", "acc2"]
    assert rows[0]["kind"] == "chat"
    assert rows[1]["subscribers"] == "7000"


def test_v4_csv_pending_count() -> None:
    v4 = _ROOT / "docs" / "ops" / "TG_JOIN_QUEUE_v4.csv"
    if not v4.is_file():
        pytest.skip("v4 queue not generated yet")
    _, rows = read_queue_csv(v4)
    pending = [row for row in rows if row.get("status") == "pending"]
    assert len(pending) == 305
    assert all(row.get("wave") == "5" for row in pending)
    assert all(int(row.get("subscribers", "0")) > 5000 for row in pending)


def test_first_pending_prefers_v2_before_v4(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tg_join_lib import first_pending_row, write_queue_csv

    ops = tmp_path / "ops"
    ops.mkdir()
    v2 = ops / "TG_JOIN_QUEUE_v2.csv"
    v4 = ops / "TG_JOIN_QUEUE_v4.csv"
    fields = ["wave", "account", "status", "name", "link", "chat_id", "notes"]
    write_queue_csv(
        fields,
        [
            {
                "wave": "2",
                "account": "acc1",
                "status": "pending",
                "name": "v2_first",
                "link": "https://t.me/v2_first",
                "chat_id": "",
                "notes": "",
            }
        ],
        v2,
    )
    write_queue_csv(
        fields,
        [
            {
                "wave": "5",
                "account": "acc1",
                "status": "pending",
                "name": "v4_later",
                "link": "https://t.me/v4_later",
                "chat_id": "",
                "notes": "",
            }
        ],
        v4,
    )
    monkeypatch.setattr(
        "tg_join_lib._PROJECT_ROOT",
        tmp_path,
        raising=False,
    )
    found = first_pending_row("acc1", [v2, v4])
    assert found is not None
    _, _, _, row = found
    assert row["link"] == "https://t.me/v2_first"
