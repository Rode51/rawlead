"""O206-t2: tg_join_listen_audit script."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "scripts"))

import tg_join_listen_audit as audit  # noqa: E402


def _write_queue(path: Path, rows: list[dict[str, str]]) -> None:
    fields = ["wave", "account", "status", "name", "link", "chat_id", "notes"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_build_report_flags_missing_test_group(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ops = tmp_path / "ops"
    ops.mkdir()
    queue = ops / "TG_JOIN_QUEUE.csv"
    _write_queue(
        queue,
        [
            {
                "wave": "test",
                "account": "acc2",
                "status": "done",
                "name": "test_bots",
                "link": "https://t.me/+Z7HcnIAdSw9kY2U6",
                "chat_id": "5177575757",
                "notes": "",
            }
        ],
    )
    ids_dir = tmp_path / "data"
    ids_dir.mkdir()
    (ids_dir / "telethon_chat_ids_acc2.txt").write_text("# empty\n", encoding="utf-8")

    monkeypatch.setattr(audit, "_PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        audit,
        "_queue_paths",
        lambda: [queue],
    )
    monkeypatch.setattr(
        audit,
        "telethon_monitor_accounts",
        lambda: ["acc2"],
    )

    def _fake_path(account: str) -> Path:
        return ids_dir / f"telethon_chat_ids_{account}.txt"

    monkeypatch.setattr(audit, "telethon_chat_ids_path_for_account", _fake_path)

    report = audit.build_report()
    assert report["per_account"]["acc2"]["test_group_in_file"] is False
    assert any("test group" in g for g in report["gaps"])


def test_build_report_allows_small_entity_skip_gap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ops = tmp_path / "ops"
    ops.mkdir()
    queue = ops / "TG_JOIN_QUEUE.csv"
    _write_queue(
        queue,
        [
            {
                "wave": "1",
                "account": "acc1",
                "status": "done",
                "name": "a",
                "link": "https://t.me/a",
                "chat_id": "111",
                "notes": "",
            },
            {
                "wave": "1",
                "account": "acc1",
                "status": "done",
                "name": "b",
                "link": "https://t.me/b",
                "chat_id": "222",
                "notes": "",
            },
            {
                "wave": "1",
                "account": "acc1",
                "status": "done",
                "name": "c",
                "link": "https://t.me/c",
                "chat_id": "333",
                "notes": "",
            },
        ],
    )
    ids_dir = tmp_path / "data"
    ids_dir.mkdir()
    (ids_dir / "telethon_chat_ids_acc1.txt").write_text(
        "# ids\n111\n222\n333\n5177575757\n",
        encoding="utf-8",
    )
    log_path = tmp_path / "radar.log"
    log_path.write_text(
        "2026-06-14 12:00:00 тг:монитор:старт account=acc1 чатов=2 ids=[111, 222] join=да\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(audit, "_PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(audit, "_queue_paths", lambda: [queue])
    monkeypatch.setattr(audit, "telethon_monitor_accounts", lambda: ["acc1"])

    def _fake_path(account: str) -> Path:
        return ids_dir / f"telethon_chat_ids_{account}.txt"

    monkeypatch.setattr(audit, "telethon_chat_ids_path_for_account", _fake_path)

    report = audit.build_report(log_path=log_path)
    assert report["per_account"]["acc1"]["missing_chat_ids_in_file"] == []
    assert report["ok"] is True
