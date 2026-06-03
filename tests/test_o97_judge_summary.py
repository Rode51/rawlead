"""O97-bench: judge complexity summary gate."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

from preprod_ai_prod_audit import _judge_l1_summary  # noqa: E402


class TestO97JudgeSummary(unittest.TestCase):
    def test_accept_by_avg_rating(self) -> None:
        judged = [
            {
                "lead_id": i,
                "context_understanding": 4,
                "complexity_rating": 4,
                "complexity_ok": False,
            }
            for i in range(10)
        ]
        s = _judge_l1_summary(judged)
        self.assertTrue(s["accept_complexity"])
        self.assertGreaterEqual(s["avg_complexity_rating"], 4.0)

    def test_empty_judged(self) -> None:
        s = _judge_l1_summary([])
        self.assertFalse(s["accept_complexity"])
        self.assertEqual(s["scored"], 0)


if __name__ == "__main__":
    unittest.main()
