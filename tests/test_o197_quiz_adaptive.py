"""O197: adaptive quiz start/next — phase transitions and stop rules."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

os.environ.setdefault("RAWLEAD_JWT_SECRET", "test-jwt-secret-o197")
os.environ.setdefault("RAWLEAD_API_KEY", "test-jwt-secret-o197")
os.environ["RADAR_PROFILE"] = "site"

from fastapi.testclient import TestClient  # noqa: E402

from src import api_server  # noqa: E402
from src.api_server import app  # noqa: E402
from src.quiz_adaptive import (  # noqa: E402
    QUIZ_EARLY_SIGNAL_MIN,
    QUIZ_MAX_CARDS,
    QUIZ_MIN_TOTAL,
    QUIZ_NORMAL_STOP_MIN,
    QUIZ_SIGNALS,
    _distinct_signals_shown,
    build_profile,
    check_stop,
    compute_niche_confidence,
    fetch_quiz_card,
    phase1_niche_order,
    pick_target_niche_and_signal,
    quiz_next_response,
)

SEED_ROWS: dict[tuple[str, str], tuple[Any, ...]] = {
    ("dev", "python"): (22141, "Python task", "dev", ["python"]),
    ("dev", "wordpress_dev"): (22283, "WP task", "dev", ["wordpress_dev"]),
    ("dev", "api_integration"): (22305, "API task", "dev", ["api_integration"]),
    ("design", "ui_ux"): (22354, "UI task", "design", ["ui_ux", "figma"]),
    ("design", "brand_identity"): (22341, "Brand task", "design", ["brand_identity"]),
    ("design", "video_editing"): (22327, "Video task", "design", ["video_editing"]),
    ("marketing", "smm"): (22356, "SMM task", "marketing", ["smm"]),
    ("marketing", "seo"): (22276, "SEO task", "marketing", ["seo"]),
    ("marketing", "yandex_direct"): (21677, "Direct task", "marketing", ["yandex_direct"]),
    ("text", "copywriting"): (22326, "Copy task", "text", ["copywriting"]),
    ("text", "article_writing"): (22011, "Article task", "text", ["article_writing"]),
    ("text", "editing_proofreading"): (22213, "Edit task", "text", ["editing_proofreading"]),
}


def _fake_fetcher(_cur: Any, niche: str, signal: str, shown_ids: list[str]) -> tuple[Any, ...] | None:
    row = SEED_ROWS.get((niche, signal))
    if not row:
        return None
    if str(row[0]) in shown_ids:
        return None
    return row


def _categories_from_history(history: list[dict[str, Any]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in history:
        cid = str(item["card_id"])
        for (niche, _signal), row in SEED_ROWS.items():
            if str(row[0]) == cid:
                out[cid] = niche
                break
    return out


class TestPhase1Order(unittest.TestCase):
    def test_starts_dev_then_design(self) -> None:
        order = phase1_niche_order()
        self.assertEqual(order[:2], ["dev", "design"])


class TestConfidenceAndStop(unittest.TestCase):
    def test_liked_plus_two_disliked_minus_one(self) -> None:
        history = [
            {"card_id": "22141", "liked": True, "tags": ["python"]},
            {"card_id": "22354", "liked": False, "tags": ["ui_ux"]},
        ]
        cats = {"22141": "dev", "22354": "design"}
        conf = compute_niche_confidence(history, cats)
        self.assertEqual(conf["dev"], 2)
        self.assertEqual(conf["design"], -1)

    def test_no_early_stop_before_min_total(self) -> None:
        history = [
            {"card_id": str(22141 + i), "liked": True, "tags": ["python"]}
            for i in range(QUIZ_MIN_TOTAL - 1)
        ]
        cats = {str(22141 + i): "dev" for i in range(QUIZ_MIN_TOTAL - 1)}
        stop, null = check_stop(history, cats)
        self.assertFalse(stop)
        self.assertFalse(null)

    def test_no_early_stop_without_signal_coverage(self) -> None:
        """6 dev likes with only 2 distinct signals — must not early-stop."""
        card_ids = ["qc_dev_python_01", "qc_dev_wp_01"] * 3
        history = [{"card_id": cid, "liked": True, "tags": ["python"]} for cid in card_ids]
        cats = {cid: "dev" for cid in card_ids}
        stop, null = check_stop(history, cats)
        self.assertFalse(stop)
        self.assertFalse(null)
        self.assertLess(
            _distinct_signals_shown(history, cats, "dev"),
            QUIZ_EARLY_SIGNAL_MIN,
        )

    def test_early_stop_after_min_total_and_signal_coverage(self) -> None:
        base_ids = [
            "qc_dev_python_01",
            "qc_dev_wp_01",
            "qc_dev_api_01",
            "qc2_dev_js_01",
        ]
        card_ids = (base_ids * 2)[:QUIZ_MIN_TOTAL]
        history = [{"card_id": cid, "liked": True, "tags": ["python"]} for cid in card_ids]
        cats = {cid: "dev" for cid in card_ids}
        self.assertGreaterEqual(
            _distinct_signals_shown(history, cats, "dev"),
            QUIZ_EARLY_SIGNAL_MIN,
        )
        stop, null = check_stop(history, cats)
        self.assertTrue(stop)
        self.assertFalse(null)

    def test_null_stop_all_disliked(self) -> None:
        history = [
            {"card_id": str(22141 + i), "liked": False, "tags": ["python"]}
            for i in range(QUIZ_NORMAL_STOP_MIN)
        ]
        cats = {str(22141 + i): "dev" for i in range(QUIZ_NORMAL_STOP_MIN)}
        stop, null = check_stop(history, cats)
        self.assertTrue(stop)
        self.assertTrue(null)

    def test_forced_stop_at_twenty(self) -> None:
        history = [{"card_id": str(i), "liked": True, "tags": ["python"]} for i in range(20)]
        cats = {str(i): "dev" for i in range(20)}
        stop, null = check_stop(history, cats)
        self.assertTrue(stop)
        self.assertFalse(null)


class TestPhaseTransitions(unittest.TestCase):
    def test_phase1_picks_niche_by_index(self) -> None:
        cats: dict[str, str] = {}
        niche, signal = pick_target_niche_and_signal([], cats)
        self.assertEqual(niche, "dev")
        self.assertEqual(signal, QUIZ_SIGNALS["dev"][0])

        history = [{"card_id": "22141", "liked": True, "tags": ["python"]}]
        cats = {"22141": "dev"}
        niche, signal = pick_target_niche_and_signal(history, cats)
        self.assertEqual(niche, "design")
        self.assertEqual(signal, QUIZ_SIGNALS["design"][0])

    def test_phase2_exploit_dominant_niche(self) -> None:
        history = [
            {"card_id": "22141", "liked": True, "tags": ["python"]},
            {"card_id": "22354", "liked": False, "tags": ["ui_ux"]},
            {"card_id": "22356", "liked": False, "tags": ["smm"]},
            {"card_id": "22011", "liked": False, "tags": ["copywriting"]},
        ]
        cats = _categories_from_history(history)
        niche, _signal = pick_target_niche_and_signal(history, cats)
        self.assertEqual(niche, "dev")

    def test_tags_to_import_from_liked_only(self) -> None:
        history = [
            {"card_id": "22354", "liked": True, "tags": ["ui_ux", "figma"]},
            {"card_id": "22141", "liked": False, "tags": ["python"]},
        ]
        cats = {"22354": "design", "22141": "dev"}
        profile = build_profile(history, cats, 180)
        assert profile is not None
        self.assertEqual(profile["tags_to_import"], ["ui_ux", "figma"])


class TestQuizEndpoints(unittest.TestCase):
    def _mock_cursor(self) -> MagicMock:
        cur = MagicMock()

        def fetch_categories(_sql: str, ids: list[int]) -> None:
            cur._last_ids = ids

        def fetchone_side_effect() -> tuple[Any, ...] | None:
            return None

        cur.execute.side_effect = lambda sql, params=None: None
        cur.fetchone.side_effect = fetchone_side_effect
        cur.fetchall.side_effect = lambda: []
        return cur

    def test_start_returns_dev_python_card(self) -> None:
        cur = MagicMock()
        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            with patch("pg_storage._ensure_user_tags_columns"):
                with patch(
                    "src.quiz_adaptive.quiz_next_response",
                    side_effect=lambda history, c: quiz_next_response(
                        history, c, fetcher=_fake_fetcher
                    ),
                ):
                    client = TestClient(app)
                    resp = client.get("/v1/quiz/start")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertFalse(body["done"])
        self.assertEqual(body["card"]["card_id"], "22141")
        self.assertEqual(body["card"]["category"], "dev")
        self.assertIn("python", body["card"]["lead_tags"])

    def test_next_after_one_card_is_design(self) -> None:
        history = [{"card_id": "22141", "liked": True, "tags": ["python"]}]

        def fake_categories(cur: Any, card_ids: list[str]) -> dict[str, str]:
            return {"22141": "dev"}

        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            with patch("pg_storage._ensure_user_tags_columns"):
                with patch("src.quiz_adaptive.fetch_card_categories", side_effect=fake_categories):
                    with patch(
                        "src.quiz_adaptive.quiz_next_response",
                        side_effect=lambda h, c: quiz_next_response(h, c, fetcher=_fake_fetcher),
                    ):
                        client = TestClient(app)
                        resp = client.post("/v1/quiz/next", json={"history": history})
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertFalse(body["done"])
        self.assertEqual(body["card"]["category"], "design")

    def test_early_stop_returns_profile(self) -> None:
        base_ids = [
            "qc_dev_python_01",
            "qc_dev_wp_01",
            "qc_dev_api_01",
            "qc2_dev_js_01",
        ]
        card_ids = (base_ids * 2)[:QUIZ_MIN_TOTAL]
        history = [{"card_id": cid, "liked": True, "tags": ["python"]} for cid in card_ids]

        def fake_categories(_cur: Any, card_ids: list[str]) -> dict[str, str]:
            return {cid: "dev" for cid in card_ids}

        with patch.object(api_server, "psycopg") as mock_pg:
            conn = MagicMock()
            cur = MagicMock()
            mock_pg.connect.return_value.__enter__.return_value = conn
            conn.cursor.return_value.__enter__.return_value = cur
            with patch("pg_storage._ensure_user_tags_columns"):
                with patch("src.quiz_adaptive.fetch_card_categories", side_effect=fake_categories):
                    with patch("src.quiz_adaptive.count_leads_per_week", return_value=180):
                        with patch(
                            "src.quiz_adaptive.quiz_next_response",
                            side_effect=lambda h, c: quiz_next_response(h, c, fetcher=_fake_fetcher),
                        ):
                            client = TestClient(app)
                            resp = client.post("/v1/quiz/next", json={"history": history})
        body = resp.json()
        self.assertTrue(body["done"])
        self.assertIsNotNone(body["profile"])
        self.assertEqual(body["profile"]["leads_per_week"], 180)
        self.assertIn("python", body["profile"]["tags_to_import"])


class TestFetchCard(unittest.TestCase):
    def test_respects_shown_ids(self) -> None:
        cur = MagicMock()
        card = fetch_quiz_card(cur, "dev", "python", ["22141"], fetcher=_fake_fetcher)
        self.assertIsNone(card)


class TestAllowlist(unittest.TestCase):
    def setUp(self) -> None:
        import src.quiz_adaptive as qa
        qa._ALLOWLIST = None
        qa._ALLOWLIST_LOADED = False

    def tearDown(self) -> None:
        import src.quiz_adaptive as qa
        qa._ALLOWLIST = None
        qa._ALLOWLIST_LOADED = False

    def test_allowlist_none_when_file_missing(self) -> None:
        from src.quiz_adaptive import _load_allowlist
        from unittest.mock import patch
        with patch("src.quiz_adaptive.Path.exists", return_value=False):
            result = _load_allowlist()
        self.assertIsNone(result)

    def test_allowlist_loaded_from_json(self) -> None:
        import json as _json
        from src.quiz_adaptive import _load_allowlist
        from unittest.mock import mock_open, patch
        data = [22141, 22283, 22354]
        with patch("src.quiz_adaptive.Path.exists", return_value=True):
            with patch("src.quiz_adaptive.Path.read_text", return_value=_json.dumps(data)):
                result = _load_allowlist()
        self.assertEqual(result, data)

    def test_allowlist_included_in_query_params(self) -> None:
        from src.quiz_adaptive import _query_card_inner
        cur = MagicMock()
        cur.fetchone.return_value = None
        allowlist = [22141, 22283]
        _query_card_inner(cur, "dev", "python", [0], cx_only=False, min_score=60, allowlist=allowlist)
        sql, params = cur.execute.call_args[0]
        self.assertIn("id = ANY(%s)", sql)
        self.assertIn(allowlist, params)

    def test_no_allowlist_clause_when_none(self) -> None:
        from src.quiz_adaptive import _query_card_inner
        cur = MagicMock()
        cur.fetchone.return_value = None
        _query_card_inner(cur, "dev", "python", [0], cx_only=False, min_score=60, allowlist=None)
        sql, params = cur.execute.call_args[0]
        self.assertNotIn("id = ANY(%s)", sql)

    def test_allowlist_file_present_in_repo(self) -> None:
        """O216b b5: quiz_pool_allowlist.json must exist in repo data/ dir."""
        allowlist_path = _ROOT / "data" / "quiz_pool_allowlist.json"
        self.assertTrue(allowlist_path.exists(), f"Missing: {allowlist_path}")

    def test_allowlist_file_nonempty(self) -> None:
        """O216b b5: _load_allowlist() must return non-empty list when file present."""
        import src.quiz_adaptive as qa
        qa._ALLOWLIST = None
        qa._ALLOWLIST_LOADED = False
        result = qa._load_allowlist()
        self.assertIsNotNone(result, "_load_allowlist() returned None — file missing or empty?")
        self.assertGreater(len(result), 0, "Allowlist is empty")  # type: ignore[arg-type]


class TestO221DevCoverageSimulation(unittest.TestCase):
    """O221: dev pool — 20 picks with dedup should surface many unique cards."""

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

    def test_dev_only_twenty_picks_twelve_unique(self) -> None:
        cur = MagicMock()
        history: list[dict[str, Any]] = []
        shown: list[str] = []
        seen: set[str] = set()
        signals = QUIZ_SIGNALS["dev"]

        for i in range(QUIZ_MAX_CARDS):
            signal = signals[i % len(signals)]
            card = fetch_quiz_card(cur, "dev", signal, shown, history=history)
            self.assertIsNotNone(card, f"no dev card at pick {i + 1}, shown={shown}")
            cid = str(card["card_id"])  # type: ignore[index]
            self.assertNotIn(cid, seen, f"duplicate card_id: {cid}")
            seen.add(cid)
            shown.append(cid)
            history.append(
                {
                    "card_id": cid,
                    "liked": True,
                    "tags": list(card.get("lead_tags") or []),  # type: ignore[union-attr]
                }
            )

        self.assertEqual(len(seen), QUIZ_MAX_CARDS)
        self.assertGreaterEqual(len(seen), 12)


class TestQuizInsufficientProfile(unittest.TestCase):
    def test_done_without_card_returns_null_profile(self) -> None:
        cur = MagicMock()
        with patch("src.quiz_adaptive.fetch_quiz_card", return_value=None):
            with patch("src.quiz_adaptive.fetch_card_categories", return_value={}):
                with patch("src.quiz_adaptive.check_stop", return_value=(False, False)):
                    resp = quiz_next_response([], cur)
        self.assertTrue(resp["done"])
        self.assertIsNone(resp["profile"])

    def test_quiz_overlay_handles_insufficient_retry(self) -> None:
        """Client contract: done && !profile → retry UI (data-testid quiz-insufficient)."""
        overlay = (
            _ROOT / "rawlead-next" / "components" / "feed" / "QuizOverlay.tsx"
        ).read_text(encoding="utf-8")
        self.assertIn('data-testid="quiz-insufficient"', overlay)
        self.assertIn('data-testid="quiz-retry"', overlay)
        self.assertIn("Попробовать ещё", overlay)


if __name__ == "__main__":
    unittest.main()
