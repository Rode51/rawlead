"""O221: quiz v2 coverage CI — Tier-A anchors + P0 reachability."""

from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from src.skills_catalog import TIER_A_BY_NICHE  # noqa: E402

_V1_PATH = _ROOT / "data" / "quiz_cards_v1.json"
_V2_PATH = _ROOT / "data" / "quiz_cards_v2.json"
_MATRIX_PATH = _ROOT / "data" / "quiz_coverage_matrix.csv"


def _load_merged_cards() -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in (_V1_PATH, _V2_PATH):
        raw = json.loads(path.read_text(encoding="utf-8"))
        for card in raw:
            cid = str(card["id"])
            if cid in seen:
                continue
            seen.add(cid)
            cards.append(card)
    return cards


class TestQuizCoverageMergedPool(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cards = _load_merged_cards()

    def test_merged_pool_186_unique_ids(self) -> None:
        self.assertEqual(len(self.cards), 186)
        ids = [c["id"] for c in self.cards]
        self.assertEqual(len(ids), len(set(ids)))

    def test_tier_a_each_tag_has_two_anchors(self) -> None:
        gaps: list[str] = []
        for niche, tags in TIER_A_BY_NICHE.items():
            for tag in tags:
                anchors = [
                    c
                    for c in self.cards
                    if c.get("card_type") == "anchor"
                    and tag in (c.get("skills_on_like") or [])
                ]
                if len(anchors) < 2:
                    gaps.append(f"{niche}/{tag}: {len(anchors)} anchor(s)")
        self.assertFalse(
            gaps,
            "Tier-A tags need >=2 anchor cards:\n" + "\n".join(gaps),
        )

    def test_p0_tags_reachable_via_skills_on_like(self) -> None:
        with _MATRIX_PATH.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        missing: list[str] = []
        for row in rows:
            if row.get("gap_class") != "P0":
                continue
            tag = row["tag"]
            niche = row["niche"]
            found = any(
                tag in (c.get("skills_on_like") or [])
                for c in self.cards
            )
            if not found:
                missing.append(f"{niche}/{tag}")
        self.assertFalse(
            missing,
            "P0 tags must appear in skills_on_like of merged pool:\n"
            + "\n".join(missing),
        )

    def test_v2_signals_in_quiz_signals(self) -> None:
        from src.quiz_adaptive import QUIZ_SIGNALS

        valid = {sig for sigs in QUIZ_SIGNALS.values() for sig in sigs}
        v2_cards = json.loads(_V2_PATH.read_text(encoding="utf-8"))
        bad: list[str] = []
        for card in v2_cards:
            sig = card.get("signal")
            if sig is not None and sig not in valid:
                bad.append(f"{card['id']}: {sig}")
        self.assertFalse(bad, "v2 signals missing from QUIZ_SIGNALS:\n" + "\n".join(bad))


if __name__ == "__main__":
    unittest.main()
