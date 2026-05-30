"""O60a: shared reply_draft must not leak in public feed."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.api_server import (  # noqa: E402
    _attach_personal_replies,
    _finalize_feed_items,
    _row_to_item,
    _strip_shared_reply_drafts,
)


class _FakeCursor:
    def __init__(self, replies: dict[int, str]) -> None:
        self._replies = replies
        self.last_query = ""

    def execute(self, query: str, params: tuple) -> None:
        self.last_query = query
        self._params = params

    def fetchall(self) -> list[tuple]:
        _uid, ids = self._params
        return [(lid, self._replies[lid]) for lid in ids if lid in self._replies]


class TestFeedPrivacyO60(unittest.TestCase):
    def _item_with_shared_draft(self) -> dict:
        row = (
            42,
            "fl",
            "Title",
            "body",
            "https://fl.ru/1",
            "1000",
            80,
            "Брать",
            '["php"]',
            [],
            None,
            "dev",
            "summary",
            ["php"],
            "SHARED DRAFT TEXT",
        )
        return _row_to_item(row)

    def test_strip_shared_reply_drafts(self) -> None:
        item = self._item_with_shared_draft()
        self.assertEqual(item["reply_draft"], "SHARED DRAFT TEXT")
        _strip_shared_reply_drafts([item])
        self.assertEqual(item["reply_draft"], "")

    def test_finalize_anon_no_personal(self) -> None:
        item = self._item_with_shared_draft()
        cur = _FakeCursor({42: "MY REPLY"})
        _finalize_feed_items(cur, [item], user_id=None)
        self.assertEqual(item["reply_draft"], "")

    def test_finalize_paid_personal_only(self) -> None:
        item = self._item_with_shared_draft()
        cur = _FakeCursor({42: "MY REPLY"})
        _finalize_feed_items(cur, [item], user_id="00000000-0000-0000-0000-000000000099")
        self.assertEqual(item["reply_draft"], "MY REPLY")

    def test_attach_personal_empty_when_no_row(self) -> None:
        item = {"id": 99, "reply_draft": ""}
        cur = _FakeCursor({})
        _attach_personal_replies(cur, "00000000-0000-0000-0000-000000000099", [item])
        self.assertEqual(item["reply_draft"], "")


if __name__ == "__main__":
    unittest.main()
