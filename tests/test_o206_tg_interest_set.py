"""O206: TG interest set + conditional не_слушаем logging."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

import public_feed as pf  # noqa: E402
from public_feed import (  # noqa: E402
    TG_TEST_GROUP_RAW_ID,
    chat_in_tg_interest_set,
    clear_tg_listen_caches,
)


def _write_queue(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["wave", "account", "status", "name", "link", "chat_id", "notes"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_test_group_in_interest_set() -> None:
    assert chat_in_tg_interest_set(-1005177575757)
    assert chat_in_tg_interest_set(TG_TEST_GROUP_RAW_ID)


def test_random_chat_not_in_interest_set() -> None:
    assert not chat_in_tg_interest_set(-1009999999999)


def test_done_queue_chat_in_interest_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text("https://t.me/jobs_channel\n", encoding="utf-8")
    queue = tmp_path / "queue.csv"
    _write_queue(
        queue,
        [
            {
                "wave": "1",
                "account": "acc1",
                "status": "done",
                "name": "jobs",
                "link": "https://t.me/jobs_channel",
                "chat_id": "424242",
                "notes": "",
            }
        ],
    )
    pf._ALLOWLIST_PATH = allowlist
    clear_tg_listen_caches()
    monkeypatch.setenv("TG_JOIN_QUEUE_CSV", str(queue))
    assert chat_in_tg_interest_set(424242)
    assert chat_in_tg_interest_set(-100424242)


def test_none_chat_not_interest() -> None:
    assert not chat_in_tg_interest_set(None)
