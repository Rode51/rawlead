"""O165: invite-only TG test group in allowlist + join queue matching."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from public_feed import _tg_link_key, tg_listen_allowed_chat_ids  # noqa: E402

_TEST_INVITE = "https://t.me/+Z7HcnIAdSw9kY2U6"
_TEST_HASH = "z7hcniadsw9ky2u6"


def test_tg_link_key_invite_hash() -> None:
    assert _tg_link_key(_TEST_INVITE) == _TEST_HASH
    assert _tg_link_key("https://t.me/distantsiya") == "distantsiya"


def test_tg_listen_allowed_includes_test_group_when_done(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text(f"# test\n{_TEST_INVITE}\n", encoding="utf-8")
    queue = tmp_path / "queue.csv"
    with queue.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["wave", "account", "status", "name", "link", "chat_id", "notes"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "wave": "test",
                "account": "acc1",
                "status": "done",
                "name": "test_bots",
                "link": _TEST_INVITE,
                "chat_id": "5177575757",
                "notes": "owner-smoke",
            }
        )

    import public_feed as pf

    pf._ALLOWLIST_PATH = allowlist
    pf._tg_allowlist_link_keys.cache_clear()
    pf.tg_listen_allowed_chat_ids.cache_clear()
    monkeypatch.setenv("TG_JOIN_QUEUE_CSV", str(queue))

    allowed = tg_listen_allowed_chat_ids()
    assert 5177575757 in allowed
