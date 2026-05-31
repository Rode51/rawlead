"""O72 smoke: preprod_ai_prod_audit validators on mock rows."""



from __future__ import annotations



import sys

from pathlib import Path

from unittest import TestCase



_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(_ROOT / "scripts"))

sys.path.insert(0, str(_ROOT / "src"))



from preprod_ai_prod_audit import audit_lead, build_sample_and_audit  # noqa: E402

from tools_catalog import is_known_tool  # noqa: E402





def _mock_lead(**overrides) -> dict:

    base = {

        "lead_id": 1,

        "source": "fl",

        "title": "Python парсер сайта",

        "body": "Нужен парсер на Python, выгрузка в CSV.",

        "url": "https://fl.ru/1",

        "budget_text": "15000",

        "ai_verdict": "Брать",

        "category": "dev",

        "task_summary": "Парсер сайта с выгрузкой в CSV.",

        "tools_required": ["python", "web_scraping"],

        "reply_draft": (

            "Заинтересовал проект. Сначала разберу структуру сайта, "

            "напишу парсер на Python и выгружу данные в CSV."

        ),

        "sample_bucket": "mock",

    }

    base.update(overrides)

    return base





class TestPreprodAiProdAudit(TestCase):

    def test_auto_pass_good_lead(self) -> None:

        r = audit_lead(_mock_lead())

        self.assertTrue(r["auto_pass"])

        self.assertTrue(r["draft_only_pass"])

        self.assertTrue(r["tools_pass"])

        self.assertEqual(r["fails"], [])



    def test_fail_empty_l1(self) -> None:

        r = audit_lead(_mock_lead(task_summary=""))

        self.assertFalse(r["auto_pass"])

        self.assertFalse(r["draft_only_pass"])

        self.assertTrue(any(f.startswith("L1:") for f in r["fails"]))



    def test_fail_empty_draft(self) -> None:

        r = audit_lead(_mock_lead(reply_draft=""))

        self.assertFalse(r["auto_pass"])

        self.assertFalse(r["draft_only_pass"])

        self.assertIn("L2:empty_reply_draft", r["fails"])



    def test_fail_tools_not_in_catalog(self) -> None:

        r = audit_lead(_mock_lead(tools_required=["python", "totally_fake_tool_xyz"]))

        self.assertFalse(r["tools_pass"])

        self.assertTrue(r["draft_only_pass"])

        self.assertTrue(any("not_in_catalog" in f for f in r["fails"]))



    def test_known_tools_whitelist(self) -> None:

        self.assertTrue(is_known_tool("photoshop"))

        self.assertTrue(is_known_tool("Google Analytics"))

        r = audit_lead(_mock_lead(tools_required=["photoshop", "canva"]))

        self.assertTrue(r["tools_pass"])

        self.assertTrue(r["draft_only_pass"])



    def test_skill_alias_via_synonym(self) -> None:

        r = audit_lead(_mock_lead(tools_required=["wordpress", "html"]))

        self.assertTrue(r["tools_pass"])



    def test_fail_tools_empty_with_hints(self) -> None:

        r = audit_lead(

            _mock_lead(

                title="Дизайн в Figma",

                body="Нужен UI kit в Figma",

                tools_required=[],

            )

        )

        self.assertFalse(r["tools_pass"])

        self.assertTrue(r["draft_only_pass"])

        self.assertTrue(any("empty_but_desc_hints" in f for f in r["fails"]))



    def test_summary_rate(self) -> None:

        leads = [

            _mock_lead(lead_id=1),

            _mock_lead(lead_id=2, reply_draft=""),

        ]

        _, summary = build_sample_and_audit(leads)

        self.assertEqual(summary["total"], 1)

        self.assertEqual(summary["draft_only_pass"], 1)

        self.assertEqual(summary["draft_only_pass_pct"], 100.0)

        self.assertTrue(summary["accept_draft_95pct"])


