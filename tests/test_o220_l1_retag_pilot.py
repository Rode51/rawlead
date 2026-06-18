"""O220-L1-RETAG-PILOT: selection SQL + safe update (no reply_draft / is_visible)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from ai_analyze import AiLiteAnalysis  # noqa: E402
from listing import ListingProject  # noqa: E402
from pg_storage import NeonLeadStorage  # noqa: E402
from scripts.o220_l1_retag_pilot import (  # noqa: E402
    PILOT_CATEGORIES,
    build_report,
    evaluate_gate,
    judge_command,
    summarize_by_niche,
)


class TestRetagPilotSelection(unittest.TestCase):
    @patch("pg_storage.public_feed_sources", return_value=frozenset({"fl", "kwork"}))
    def test_fetch_retag_pilot_leads_sql_per_category(self, _sources: MagicMock) -> None:
        pg = NeonLeadStorage("postgresql://test")
        conn = MagicMock()
        cur = MagicMock()
        cur.fetchall.side_effect = [
            [(101, "fl", "1", "Dev task", "body", "url", "1000", "dev")],
            [(201, "kwork", "2", "Design task", "body", "url", "2000", "design")],
            [(301, "fl", "3", "Mkt task", "body", "url", "3000", "marketing")],
            [(401, "kwork", "4", "Text task", "body", "url", "4000", "text")],
        ]
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        with patch.object(pg, "connection") as mock_conn:
            mock_conn.return_value.__enter__ = MagicMock(return_value=conn)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            rows = pg.fetch_retag_pilot_leads(per_category=10, errors=[])

        self.assertEqual(len(rows), 4)
        sql_calls = [call[0][0] for call in cur.execute.call_args_list]
        self.assertEqual(len(sql_calls), len(PILOT_CATEGORIES))
        for sql in sql_calls:
            self.assertIn("is_visible = TRUE", sql)
            self.assertIn("jsonb_array_length(lead_tags)", sql)
            self.assertIn("id DESC", sql)
            self.assertNotIn("reply_draft", sql)
        params = [call[0][1] for call in cur.execute.call_args_list]
        self.assertEqual(params[0][0], "dev")
        self.assertEqual(params[0][2], 10)


class TestRetagPilotSafeUpdate(unittest.TestCase):
    def test_update_lite_retag_pilot_preserves_protected_columns(self) -> None:
        pg = NeonLeadStorage("postgresql://test")
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
        conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

        project = ListingProject(
            project_id=99,
            title="Landing page",
            budget_text="50 000",
            url="https://fl.ru/99",
            published_at="",
            listing_snippet="Need WP landing",
            source="fl",
        )
        lite = AiLiteAnalysis(
            feed_visible=True,
            task_summary="WP landing",
            lead_tags=("wordpress", "landing_page_design"),
            ai_reasons=("WP stack", "clear scope"),
            complexity=2,
            primary_category="design",
        )

        with patch.object(pg, "connection") as mock_conn:
            mock_conn.return_value.__enter__ = MagicMock(return_value=conn)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            with patch.object(pg, "record_pending_tags"):
                pg.update_lite_retag_pilot(
                    7051,
                    project,
                    lite=lite,
                    errors=[],
                    body_snippet="Need WP landing",
                )

        cur.execute.assert_called_once()
        sql, params = cur.execute.call_args[0]
        self.assertIn("lead_tags", sql)
        self.assertIn("ai_reasons", sql)
        self.assertIn("task_summary", sql)
        self.assertIn("category", sql)
        self.assertIn("WHERE id = %s", sql)
        self.assertNotIn("is_visible", sql)
        self.assertNotIn("ai_verdict", sql)
        self.assertNotIn("ai_score", sql)
        self.assertNotIn("reply_draft", sql)
        self.assertNotIn("body =", sql)
        self.assertEqual(params[-1], 7051)


class TestRetagPilotReport(unittest.TestCase):
    def test_summarize_and_gate_pass(self) -> None:
        leads = []
        for cat in PILOT_CATEGORIES:
            for i in range(10):
                leads.append(
                    {
                        "id": i,
                        "category": cat,
                        "tag_count_before": 1,
                        "tag_count_after": 3,
                        "tags_before": ["a"],
                        "tags_after": ["a", "b", "c"],
                    }
                )
        summary = summarize_by_niche(leads)
        self.assertEqual(summary["dev"]["count"], 10)
        self.assertEqual(summary["dev"]["avg_tags_after"], 3.0)
        gate = evaluate_gate(summary, judge_l1_usable=0.75)
        self.assertTrue(gate["passed"])

    def test_gate_fail_adds_prompt_fix_in_report(self) -> None:
        leads = [
            {
                "id": 1,
                "category": "dev",
                "title": "Thin tags",
                "tag_count_before": 1,
                "tag_count_after": 1,
                "tags_before": ["python"],
                "tags_after": ["python"],
                "task_summary_after": "API",
            }
        ]
        report = build_report(mode="apply", leads=leads)
        self.assertFalse(report["gate"]["passed"])
        self.assertIn("l1_prompt_fix", report)
        self.assertEqual(report["l1_prompt_fix"][0]["id"], 1)

    def test_judge_command_format(self) -> None:
        cmd = judge_command([10, 20, 30])
        self.assertIn("--lead-ids 10,20,30", cmd)
        self.assertIn("--judge-l1-limit 3", cmd)


if __name__ == "__main__":
    unittest.main()
