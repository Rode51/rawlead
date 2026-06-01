"""O72d: regen_shared_reply_drafts helpers."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from preprod_ai_prod_audit import _row_to_lead  # noqa: E402
from regen_shared_reply_drafts import (  # noqa: E402
    _lite_from_lead,
    fetch_regen_candidates,
    regen_one_lead,
)


def _lead(**kw) -> dict:
    base = {
        "lead_id": 100,
        "source": "fl",
        "title": "Парсер",
        "budget_text": "10000",
        "ai_verdict": "Брать",
        "task_summary": "Парсер сайта в CSV.",
        "tools_required": ["python"],
        "reply_draft": "Старый шаблон готов взять задачу.",
        "lead_tags": ["python"],
        "ai_reasons": [],
    }
    base.update(kw)
    return base


class RegenSharedDraftTests(TestCase):
    def test_lite_from_lead(self) -> None:
        lite = _lite_from_lead(_lead())
        self.assertEqual(lite.verdict, "Брать")
        self.assertIn("CSV", lite.task_summary)

    def test_skip_mimo(self) -> None:
        res = regen_one_lead(
            type("C", (), {"ai_active": True, "ai_provider": "openrouter"})(),
            _lead(ai_verdict="МИМО"),
        )
        self.assertEqual(res["status"], "skip_verdict")

    @patch("regen_shared_reply_drafts.analyze_shared_reply_draft")
    def test_regen_ok(self, mock_analyze) -> None:
        mock_analyze.return_value = (
            "Заинтересовал парсинг. Сначала разберу структуру сайта, "
            "напишу скрипт на Python и выгружу данные в CSV."
        )
        cfg = type(
            "Cfg",
            (),
            {
                "ai_active": True,
                "ai_provider": "openrouter",
                "ai_model_shared_draft": "google/gemini-2.5-pro",
            },
        )()
        res = regen_one_lead(cfg, _lead())
        self.assertEqual(res["status"], "ok")
        self.assertTrue(res["changed"])
        self.assertIn("Python", res["reply_draft"])

    @patch("regen_shared_reply_drafts.analyze_shared_reply_draft")
    def test_reject_cliche_retries(self, mock_analyze) -> None:
        mock_analyze.return_value = "Готов взять задачу и полностью погружусь в проект."
        cfg = type(
            "Cfg",
            (),
            {"ai_active": True, "ai_provider": "openrouter"},
        )()
        res = regen_one_lead(cfg, _lead(), max_attempts=2, reject_cliche=True)
        self.assertEqual(res["status"], "fail")

    def test_fetch_filters_verdict(self) -> None:
        class FakeCursor:
            def __init__(self, rows):
                self._rows = rows

            def execute(self, *_a, **_k):
                pass

            def fetchall(self):
                return self._rows

        class FakeConn:
            def cursor(self):
                return FakeCursor(
                    [
                        (
                            1,
                            "fl",
                            "A",
                            "body",
                            "url",
                            "5k",
                            None,
                            "Брать",
                            '["python"]',
                            "[]",
                            None,
                            "dev",
                            "Summary here.",
                            '["python"]',
                            "old draft",
                        ),
                        (
                            2,
                            "fl",
                            "B",
                            "body",
                            "url",
                            "5k",
                            None,
                            "МИМО",
                            "[]",
                            "[]",
                            None,
                            "dev",
                            "Summary.",
                            "[]",
                            "draft",
                        ),
                    ]
                )

            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

        rows = FakeConn().cursor().fetchall()
        pool = [_row_to_lead(r) for r in rows]
        for lead in pool:
            lead["sample_bucket"] = "main"

        with patch(
            "regen_shared_reply_drafts._stratified_sample",
            return_value=pool,
        ):
            picked = fetch_regen_candidates(
                FakeConn(), limit=10, src_sql="", src_params=[]
            )
        self.assertEqual(len(picked), 1)
        self.assertEqual(picked[0]["lead_id"], 1)
