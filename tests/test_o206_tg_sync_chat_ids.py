"""O206-t2b: tg_sync_chat_ids merges all TG_JOIN_QUEUE*.csv per account."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from config import _seed_chat_ids_from_queue_paths  # noqa: E402


def _write_queue(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["wave", "account", "status", "name", "link", "chat_id", "notes"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_seed_chat_ids_merges_all_queue_files(tmp_path: Path) -> None:
    ops = tmp_path / "ops"
    ops.mkdir()
    v1 = ops / "TG_JOIN_QUEUE.csv"
    v3 = ops / "TG_JOIN_QUEUE_v3.csv"
    _write_queue(
        v1,
        [
            {
                "wave": "1",
                "account": "acc1",
                "status": "done",
                "name": "old",
                "link": "https://t.me/old",
                "chat_id": "111",
                "notes": "",
            }
        ],
    )
    _write_queue(
        v3,
        [
            {
                "wave": "4",
                "account": "acc1",
                "status": "done",
                "name": "new",
                "link": "https://t.me/new",
                "chat_id": "222",
                "notes": "",
            },
            {
                "wave": "4",
                "account": "acc2",
                "status": "done",
                "name": "other",
                "link": "https://t.me/other",
                "chat_id": "333",
                "notes": "",
            },
        ],
    )

    ids = _seed_chat_ids_from_queue_paths([v1, v3], "acc1")
    assert ids == [111, 222]

    ids_acc2 = _seed_chat_ids_from_queue_paths([v1, v3], "acc2")
    assert ids_acc2 == [333]


def test_seed_chat_ids_dedupes_same_chat_id(tmp_path: Path) -> None:
    ops = tmp_path / "ops"
    ops.mkdir()
    v1 = ops / "TG_JOIN_QUEUE.csv"
    v2 = ops / "TG_JOIN_QUEUE_v2.csv"
    row = {
        "wave": "1",
        "account": "acc1",
        "status": "done",
        "name": "dup",
        "link": "https://t.me/dup",
        "chat_id": "5177575757",
        "notes": "",
    }
    _write_queue(v1, [row])
    _write_queue(v2, [row])

    ids = _seed_chat_ids_from_queue_paths([v1, v2], "acc1")
    assert ids == [5177575757]
