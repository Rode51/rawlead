"""O190: TG join→listen chain helpers (allowlist expand + filter ladder)."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

import public_feed as pf  # noqa: E402
from public_feed import (  # noqa: E402
    append_link_to_allowlist,
    collect_done_links_from_queues,
    expand_allowlist_from_done_queues,
    filter_listen_chat_ids,
    link_in_allowlist,
)


def _write_queue(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["wave", "account", "status", "name", "link", "chat_id", "notes"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_collect_done_links_dedupes_across_queues(tmp_path: Path) -> None:
    q1 = tmp_path / "v2.csv"
    q2 = tmp_path / "v3.csv"
    row = {
        "wave": "1",
        "account": "acc1",
        "status": "done",
        "name": "alpha",
        "link": "https://t.me/alpha_jobs",
        "chat_id": "1001",
        "notes": "",
    }
    _write_queue(q1, [row])
    _write_queue(q2, [row, {**row, "link": "https://t.me/beta_jobs", "chat_id": "1002", "name": "beta"}])
    links = collect_done_links_from_queues((q1, q2))
    assert links == ["https://t.me/alpha_jobs", "https://t.me/beta_jobs"]


def test_expand_allowlist_appends_missing_done_links(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text("# tier\nhttps://t.me/distantsiya\n", encoding="utf-8")
    queue = tmp_path / "queue.csv"
    _write_queue(
        queue,
        [
            {
                "wave": "1",
                "account": "acc1",
                "status": "done",
                "name": "new_chat",
                "link": "https://t.me/new_chat_jobs",
                "chat_id": "555",
                "notes": "",
            }
        ],
    )
    added = expand_allowlist_from_done_queues(
        allowlist_path=allowlist,
        queue_paths=(queue,),
    )
    assert added == 1
    text = allowlist.read_text(encoding="utf-8")
    assert "https://t.me/new_chat_jobs" in text
    assert link_in_allowlist("https://t.me/new_chat_jobs") is False  # cache from repo path
    pf._ALLOWLIST_PATH = allowlist
    pf.clear_tg_listen_caches()
    assert link_in_allowlist("https://t.me/new_chat_jobs") is True


def test_append_link_to_allowlist_appends_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text("# tier\nhttps://t.me/existing\n", encoding="utf-8")
    pf._ALLOWLIST_PATH = allowlist
    pf.clear_tg_listen_caches()

    assert append_link_to_allowlist("https://t.me/new_jobs") is True
    assert append_link_to_allowlist("https://t.me/new_jobs") is False
    text = allowlist.read_text(encoding="utf-8")
    assert "https://t.me/new_jobs" in text
    assert link_in_allowlist("https://t.me/new_jobs") is True


def test_filter_listen_chat_ids_passes_all_file_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text("https://t.me/allowed_one\n", encoding="utf-8")
    queue = tmp_path / "queue.csv"
    _write_queue(
        queue,
        [
            {
                "wave": "1",
                "account": "acc1",
                "status": "done",
                "name": "one",
                "link": "https://t.me/allowed_one",
                "chat_id": "101",
                "notes": "",
            },
        ],
    )
    pf._ALLOWLIST_PATH = allowlist
    pf.clear_tg_listen_caches()
    monkeypatch.setenv("TG_JOIN_QUEUE_CSV", str(queue))

    assert filter_listen_chat_ids([101, 202, 101]) == [101, 202]
