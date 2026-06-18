"""O217: quiz card pack lint + JSON source integration tests."""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

os.environ.setdefault("RAWLEAD_JWT_SECRET", "test-jwt-secret-o217")
os.environ.setdefault("RAWLEAD_API_KEY", "test-jwt-secret-o217")
os.environ["RADAR_PROFILE"] = "site"

from src.skills_catalog import CANONICAL_TAGS  # noqa: E402
from src.quiz_adaptive import (  # noqa: E402
    QUIZ_NICHES,
    QUIZ_SIGNALS,
    _card_payload_json,
    _load_json_cards,
    _query_card_json,
    fetch_card_categories,
    fetch_quiz_card,
)

_CARDS_PATH = _ROOT / "data" / "quiz_cards_v1.json"
_V2_PILOT_PATH = _ROOT / "data" / "quiz_cards_v2-pilot.json"

EXPECTED_NICHES = set(QUIZ_NICHES)
VALID_CARD_TYPES = {"anchor", "boundary", "trap"}
VALID_SIGNALS = {sig for sigs in QUIZ_SIGNALS.values() for sig in sigs}


class TestCardsFilePresent(unittest.TestCase):
    def test_file_exists(self) -> None:
        self.assertTrue(_CARDS_PATH.exists(), f"Missing: {_CARDS_PATH}")

    def test_file_nonempty(self) -> None:
        cards = json.loads(_CARDS_PATH.read_text(encoding="utf-8"))
        self.assertIsInstance(cards, list)
        self.assertGreater(len(cards), 0)

    def test_56_cards(self) -> None:
        cards = json.loads(_CARDS_PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(cards), 56, f"Expected 56 cards, got {len(cards)}")


class TestCardsSchema(unittest.TestCase):
    """Lint each card: required fields, canonical tags, enum values."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cards: list[dict[str, Any]] = json.loads(
            _CARDS_PATH.read_text(encoding="utf-8")
        )

    def test_all_ids_unique(self) -> None:
        ids = [c["id"] for c in self.cards]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate card ids found")

    def test_required_fields(self) -> None:
        required = {"id", "pack_version", "card_type", "niche", "signal", "complexity",
                    "title", "task_summary", "skills_on_like", "skills_on_dislike"}
        for card in self.cards:
            missing = required - set(card.keys())
            self.assertFalse(missing, f"Card {card.get('id')} missing fields: {missing}")

    def test_pack_version_v1(self) -> None:
        for card in self.cards:
            self.assertEqual(card["pack_version"], "v1", f"Card {card['id']} bad pack_version")

    def test_niche_in_canonical_niches(self) -> None:
        for card in self.cards:
            self.assertIn(card["niche"], EXPECTED_NICHES,
                          f"Card {card['id']} niche={card['niche']} not in QUIZ_NICHES")

    def test_card_type_valid(self) -> None:
        for card in self.cards:
            self.assertIn(card["card_type"], VALID_CARD_TYPES,
                          f"Card {card['id']} invalid card_type={card['card_type']}")

    def test_signal_valid_or_null(self) -> None:
        for card in self.cards:
            sig = card.get("signal")
            if sig is not None:
                self.assertIn(
                    sig, VALID_SIGNALS,
                    f"Card {card['id']} signal={sig} not in QUIZ_SIGNALS"
                )

    def test_anchor_cards_have_signal(self) -> None:
        for card in self.cards:
            if card["card_type"] == "anchor":
                self.assertIsNotNone(
                    card.get("signal"),
                    f"Anchor card {card['id']} must have a signal"
                )

    def test_skills_on_like_canonical(self) -> None:
        bad: list[str] = []
        for card in self.cards:
            for tag in card.get("skills_on_like", []):
                if tag not in CANONICAL_TAGS:
                    bad.append(f"{card['id']}: {tag}")
        self.assertFalse(bad, f"Non-canonical tags in skills_on_like:\n" + "\n".join(bad))

    def test_skills_on_dislike_empty_v1(self) -> None:
        for card in self.cards:
            self.assertEqual(
                card.get("skills_on_dislike", []), [],
                f"Card {card['id']}: skills_on_dislike must be [] for v1"
            )

    def test_complexity_range(self) -> None:
        for card in self.cards:
            cx = card.get("complexity")
            self.assertIn(cx, (1, 2, 3),
                          f"Card {card['id']} complexity={cx} not in 1-3")

    def test_task_summary_nonempty(self) -> None:
        for card in self.cards:
            ts = card.get("task_summary", "")
            self.assertGreater(len(ts), 20,
                               f"Card {card['id']} task_summary too short")

    def test_14_cards_per_niche(self) -> None:
        by_niche: dict[str, int] = {}
        for card in self.cards:
            by_niche[card["niche"]] = by_niche.get(card["niche"], 0) + 1
        for niche in QUIZ_NICHES:
            self.assertEqual(by_niche.get(niche, 0), 14,
                             f"Niche {niche} has {by_niche.get(niche, 0)} cards (expected 14)")

    def test_8_anchors_per_niche(self) -> None:
        by_niche: dict[str, int] = {}
        for card in self.cards:
            if card["card_type"] == "anchor":
                by_niche[card["niche"]] = by_niche.get(card["niche"], 0) + 1
        for niche in QUIZ_NICHES:
            self.assertEqual(by_niche.get(niche, 0), 8,
                             f"Niche {niche} has {by_niche.get(niche, 0)} anchors (expected 8)")

    def test_2_boundaries_per_niche(self) -> None:
        by_niche: dict[str, int] = {}
        for card in self.cards:
            if card["card_type"] == "boundary":
                by_niche[card["niche"]] = by_niche.get(card["niche"], 0) + 1
        for niche in QUIZ_NICHES:
            self.assertEqual(by_niche.get(niche, 0), 2,
                             f"Niche {niche} has {by_niche.get(niche, 0)} boundaries (expected 2)")

    def test_4_traps_per_niche(self) -> None:
        by_niche: dict[str, int] = {}
        for card in self.cards:
            if card["card_type"] == "trap":
                by_niche[card["niche"]] = by_niche.get(card["niche"], 0) + 1
        for niche in QUIZ_NICHES:
            self.assertEqual(by_niche.get(niche, 0), 4,
                             f"Niche {niche} has {by_niche.get(niche, 0)} traps (expected 4)")


class TestJsonLoader(unittest.TestCase):
    def setUp(self) -> None:
        import src.quiz_adaptive as qa
        qa._JSON_CARDS = None
        qa._JSON_CARDS_LOADED = False
        qa._JSON_CATEGORIES = {}

    def tearDown(self) -> None:
        import src.quiz_adaptive as qa
        qa._JSON_CARDS = None
        qa._JSON_CARDS_LOADED = False
        qa._JSON_CATEGORIES = {}

    def test_load_returns_merged_cards(self) -> None:
        cards = _load_json_cards()
        self.assertIsNotNone(cards)
        self.assertEqual(len(cards), 186)  # type: ignore[arg-type]

    def test_json_categories_populated(self) -> None:
        import src.quiz_adaptive as qa
        _load_json_cards()
        self.assertEqual(len(qa._JSON_CATEGORIES), 186)
        self.assertEqual(qa._JSON_CATEGORIES.get("qc_dev_python_01"), "dev")
        self.assertEqual(qa._JSON_CATEGORIES.get("qc2_dev_js_01"), "dev")
        self.assertEqual(qa._JSON_CATEGORIES.get("qc_design_uiux_01"), "design")

    def test_load_missing_file_returns_none(self) -> None:
        with patch("src.quiz_adaptive.Path.exists", return_value=False):
            result = _load_json_cards()
        self.assertIsNone(result)


class TestQueryCardJson(unittest.TestCase):
    def setUp(self) -> None:
        import src.quiz_adaptive as qa
        qa._JSON_CARDS = None
        qa._JSON_CARDS_LOADED = False
        qa._JSON_CATEGORIES = {}

    def tearDown(self) -> None:
        import src.quiz_adaptive as qa
        qa._JSON_CARDS = None
        qa._JSON_CARDS_LOADED = False
        qa._JSON_CATEGORIES = {}

    def test_returns_card_for_niche_signal(self) -> None:
        card = _query_card_json("dev", "python", [])
        self.assertIsNotNone(card)
        self.assertEqual(card["niche"], "dev")  # type: ignore[index]
        self.assertEqual(card["signal"], "python")  # type: ignore[index]

    def test_skips_shown_ids(self) -> None:
        first = _query_card_json("dev", "python", [])
        self.assertIsNotNone(first)
        second = _query_card_json("dev", "python", [first["id"]])  # type: ignore[index]
        # should return a different card (or None if only 1 python anchor)
        if second is not None:
            self.assertNotEqual(second["id"], first["id"])  # type: ignore[index]

    def test_fallback_to_any_niche_when_signal_exhausted(self) -> None:
        # show all dev cards
        cards = _load_json_cards() or []
        dev_ids = [c["id"] for c in cards if c["niche"] == "dev"]
        result = _query_card_json("dev", "python", dev_ids[:-1])
        # should still return the last card
        self.assertIsNotNone(result)

    def test_returns_none_when_all_shown(self) -> None:
        cards = _load_json_cards() or []
        dev_ids = [c["id"] for c in cards if c["niche"] == "dev"]
        result = _query_card_json("dev", "python", dev_ids)
        self.assertIsNone(result)

    def test_signal_null_query_matches_traps(self) -> None:
        cards = _load_json_cards() or []
        # show only anchors/boundaries for dev, check we can get a trap via None signal
        non_trap_ids = [c["id"] for c in cards
                        if c["niche"] == "dev" and c["card_type"] != "trap"]
        card = _query_card_json("dev", None, non_trap_ids)
        # only traps remain; should return one
        self.assertIsNotNone(card)
        self.assertEqual(card["card_type"], "trap")  # type: ignore[index]


class TestCardPayloadJson(unittest.TestCase):
    def test_payload_fields(self) -> None:
        card = {"id": "qc_dev_python_01", "niche": "dev", "title": "Test",
                "task_summary": "Summary text", "skills_on_like": ["python"],
                "complexity": 2}
        payload = _card_payload_json(card)
        self.assertEqual(payload["card_id"], "qc_dev_python_01")
        self.assertEqual(payload["category"], "dev")
        self.assertEqual(payload["lead_tags"], ["python"])
        self.assertEqual(payload["source"], "synthetic")
        self.assertEqual(payload["complexity"], 2)
        self.assertEqual(payload["task_summary"], "Summary text")


class TestFetchCardCategoriesJson(unittest.TestCase):
    def setUp(self) -> None:
        import src.quiz_adaptive as qa
        qa._JSON_CARDS = None
        qa._JSON_CARDS_LOADED = False
        qa._JSON_CATEGORIES = {}

    def tearDown(self) -> None:
        import src.quiz_adaptive as qa
        qa._JSON_CARDS = None
        qa._JSON_CARDS_LOADED = False
        qa._JSON_CATEGORIES = {}

    def test_json_ids_resolved_without_neon(self) -> None:
        cur = MagicMock()
        cur.fetchall.return_value = []
        result = fetch_card_categories(cur, ["qc_dev_python_01", "qc_design_uiux_01"])
        self.assertEqual(result["qc_dev_python_01"], "dev")
        self.assertEqual(result["qc_design_uiux_01"], "design")
        # Neon should NOT have been queried for JSON ids
        cur.execute.assert_not_called()

    def test_mixed_json_and_neon_ids(self) -> None:
        cur = MagicMock()
        cur.fetchall.return_value = [(22141, "dev")]
        result = fetch_card_categories(cur, ["qc_dev_python_01", "22141"])
        self.assertEqual(result["qc_dev_python_01"], "dev")
        self.assertEqual(result["22141"], "dev")
        # Neon queried only for non-JSON id
        cur.execute.assert_called_once()


class TestFetchQuizCardJsonSource(unittest.TestCase):
    def setUp(self) -> None:
        import src.quiz_adaptive as qa
        qa._JSON_CARDS = None
        qa._JSON_CARDS_LOADED = False
        qa._JSON_CATEGORIES = {}

    def tearDown(self) -> None:
        import src.quiz_adaptive as qa
        qa._JSON_CARDS = None
        qa._JSON_CARDS_LOADED = False
        qa._JSON_CATEGORIES = {}

    def test_returns_synthetic_card_no_neon(self) -> None:
        cur = MagicMock()
        card = fetch_quiz_card(cur, "dev", "python", [])
        self.assertIsNotNone(card)
        self.assertEqual(card["source"], "synthetic")  # type: ignore[index]
        self.assertEqual(card["category"], "dev")  # type: ignore[index]
        # Neon should not have been queried
        cur.execute.assert_not_called()

    def test_returns_design_card(self) -> None:
        cur = MagicMock()
        card = fetch_quiz_card(cur, "design", "ui_ux", [])
        self.assertIsNotNone(card)
        self.assertEqual(card["source"], "synthetic")  # type: ignore[index]
        self.assertEqual(card["category"], "design")  # type: ignore[index]

    def test_quiz_start_returns_synthetic_card(self) -> None:
        from src import api_server
        from fastapi.testclient import TestClient

        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchall.return_value = []
            cur.fetchone.return_value = None
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            with patch("pg_storage._ensure_user_tags_columns"):
                client = TestClient(api_server.app)
                resp = client.get("/v1/quiz/start")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertFalse(body["done"])
        self.assertIn("card", body)
        self.assertEqual(body["card"]["source"], "synthetic")

    def test_quiz_next_returns_synthetic_card(self) -> None:
        from src import api_server
        from fastapi.testclient import TestClient

        history = [{"card_id": "qc_dev_python_01", "liked": True, "tags": ["python"]}]

        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchall.return_value = []
            cur.fetchone.return_value = None
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            with patch("pg_storage._ensure_user_tags_columns"):
                client = TestClient(api_server.app)
                resp = client.post("/v1/quiz/next", json={"history": history})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertFalse(body.get("done", True))
        self.assertEqual(body["card"]["source"], "synthetic")

    def test_quiz_next_dedup_json_card_id(self) -> None:
        """O220-QUIZ-DEDUP: history with JSON card_id must exclude it from next pick."""
        from src import api_server
        from fastapi.testclient import TestClient

        shown_id = "qc_dev_python_01"
        history = [
            {"card_id": shown_id, "liked": True, "tags": ["python"]},
            {"card_id": shown_id, "liked": False, "tags": []},
        ]

        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            cur.fetchall.return_value = []
            cur.fetchone.return_value = None
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            with patch("pg_storage._ensure_user_tags_columns"):
                client = TestClient(api_server.app)
                resp = client.post("/v1/quiz/next", json={"history": history})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertFalse(body.get("done", True), body)
        self.assertNotEqual(body["card"]["card_id"], shown_id)


class TestV2PilotPack(unittest.TestCase):
    """O221: v2-pilot pack lint (40 cards, merged at runtime)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cards: list[dict[str, Any]] = json.loads(
            _V2_PILOT_PATH.read_text(encoding="utf-8")
        )

    def test_file_exists(self) -> None:
        self.assertTrue(_V2_PILOT_PATH.exists(), f"Missing: {_V2_PILOT_PATH}")

    def test_40_cards(self) -> None:
        self.assertEqual(len(self.cards), 40)

    def test_pack_version_v2_pilot(self) -> None:
        for card in self.cards:
            self.assertEqual(card["pack_version"], "v2-pilot", card["id"])

    def test_10_cards_per_niche(self) -> None:
        by_niche: dict[str, int] = {}
        for card in self.cards:
            by_niche[card["niche"]] = by_niche.get(card["niche"], 0) + 1
        for niche in QUIZ_NICHES:
            self.assertEqual(by_niche.get(niche, 0), 10, niche)

    def test_all_signals_in_quiz_signals(self) -> None:
        for card in self.cards:
            sig = card.get("signal")
            if sig is not None:
                self.assertIn(sig, VALID_SIGNALS, f"{card['id']} signal={sig}")

    def test_skills_on_like_canonical(self) -> None:
        bad: list[str] = []
        for card in self.cards:
            for tag in card.get("skills_on_like", []):
                if tag not in CANONICAL_TAGS:
                    bad.append(f"{card['id']}: {tag}")
        self.assertFalse(bad, "Non-canonical v2 tags:\n" + "\n".join(bad))

    def test_v2_javascript_card_query(self) -> None:
        card = _query_card_json("dev", "javascript", [])
        self.assertIsNotNone(card)
        self.assertEqual(card["signal"], "javascript")  # type: ignore[index]
        self.assertTrue(str(card["id"]).startswith("qc2_"))  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
