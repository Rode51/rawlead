"""O72 smoke: preprod_ai_prod_audit validators on mock rows."""



from __future__ import annotations



import sys

from pathlib import Path

from unittest import TestCase



_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(_ROOT / "scripts"))

sys.path.insert(0, str(_ROOT / "src"))



from preprod_ai_prod_audit import (  # noqa: E402
    _filter_fresh_for_judge,
    _judge_l1_summary,
    _judge_l2_summary,
    _l1_judge_targets,
    _parse_judge_since,
    audit_lead,
    build_sample_and_audit,
)

from ai_analyze import (  # noqa: E402
    count_o72e3_niche_term_groups,
    draft_passes_o72e3_worst_terms,
    o72e3_worst_draft_term_groups,
)
from tools_catalog import is_known_tool, normalize_tools_required  # noqa: E402


# O72e-3 judge worst-3 (fixtures from preprod_ai_prod_audit.json)
_O72E3_WORST_LEADS = {
    8704: {
        "title": "Разработка фирменного шрифта и логотипа гостиницы",
        "task_summary": "Разработать фирменный логотип и шрифт для новой гостиницы с акцентом на узнаваемость.",
        "good_draft": (
            "Заинтересовал проект шрифта и логотипа для гостиницы Ирбис. "
            "Сначала исследование и концепции в Illustrator, затем векторизация и глифы в FontLab; "
            "параллельно доработаю знак в Photoshop. "
            "Есть ли готовые референсы по стилю гостиничного брендинга?"
        ),
        "bad_draft": "Заинтересовал проект. Готов обсудить детали и предложить варианты.",
    },
    8776: {
        "title": "Улучшить скорость работы сайта Elementor, WC, Tutor",
        "task_summary": (
            "Провести аудит фронтенда сайта на WordPress с Elementor, WooCommerce и Tutor LMS "
            "и предложить план улучшения скорости."
        ),
        "good_draft": (
            "Заинтересовал аудит bwa-akademy на WordPress+Elementor+WooCommerce+Tutor LMS. "
            "Сначала PageSpeed и критический CSS, затем отложенная загрузка JS и минификация; "
            "отдельно раздутый DOM Elementor и Ajax/видео Tutor. "
            "Какие метрики PSI сейчас на мобильных — baseline?"
        ),
        "bad_draft": "Готов провести глубокий аудит и предложить план улучшения скорости.",
    },
    8925: {
        "title": "Скрипты из Google-таблиц — адаптация к Rhino V8",
        "task_summary": "Адаптировать три скрипта Google-таблицы для работы в новой среде Rhino V8.",
        "good_draft": (
            "Заинтересовал перенос трёх сценариев с Google Apps Script на Rhino V8. "
            "Сначала разбор API и синтаксиса ES6+, затем поочерёдная миграция скриптов с таблицей. "
            "Можете дать доступ к исходникам в старой среде для оценки объёма?"
        ),
        "bad_draft": "Готов проанализировать логику и переработать скрипты на Python.",
    },
}





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



    def test_warn_reply_draft_cliche(self) -> None:
        r = audit_lead(
            _mock_lead(
                reply_draft="Заинтересовал проект. Готов взять задачу в работу сегодня.",
            )
        )
        self.assertTrue(r["draft_only_pass"])
        self.assertIn("warn:reply_draft_cliche", r["warns"])

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

    def test_l1_judge_targets_prefers_empty_bucket(self) -> None:
        leads = [
            _mock_lead(lead_id=1, sample_bucket="main"),
            _mock_lead(lead_id=2, sample_bucket="empty_l1", task_summary=""),
        ]
        picked = _l1_judge_targets(leads, limit=2)
        self.assertEqual(picked[0]["lead_id"], 2)

    def test_judge_l2_summary_accept(self) -> None:
        judged = [
            {
                "lead_id": 1,
                "relevance": 4,
                "specificity": 4,
                "universal_helpful": 4,
                "send_as_is": True,
            },
            {
                "lead_id": 2,
                "relevance": 4,
                "specificity": 4,
                "universal_helpful": 4,
                "send_as_is": True,
            },
        ]
        s = _judge_l2_summary(judged)
        self.assertTrue(s["accept_l2"])
        self.assertGreaterEqual(s["avg_combined_3"], 4.0)
        self.assertGreaterEqual(s["send_as_is_pct"], 50)

    def test_judge_l1_summary_accept_usable(self) -> None:
        judged = [{"lead_id": i, "context_understanding": 4, "verdict_fair": 4, "l1_usable": True} for i in range(10)]
        judged.extend(
            [{"lead_id": i, "context_understanding": 4, "verdict_fair": 4, "l1_usable": False} for i in range(10, 13)]
        )
        s = _judge_l1_summary(judged)
        self.assertTrue(s["accept_l1"])
        self.assertGreaterEqual(s["l1_usable_pct"], 70)

    def test_filter_fresh_for_judge(self) -> None:
        since = _parse_judge_since("2026-06-01")
        leads = [
            _mock_lead(lead_id=1, created_at="2026-05-31T12:00:00+00:00"),
            _mock_lead(lead_id=2, created_at="2026-06-01T00:00:00+00:00"),
        ]
        fresh = _filter_fresh_for_judge(leads, since=since)
        self.assertEqual([x["lead_id"] for x in fresh], [2])

    def test_judge_l2_summary_fail_low_send(self) -> None:
        judged = [
            {
                "lead_id": 1,
                "relevance": 5,
                "specificity": 5,
                "universal_helpful": 5,
                "send_as_is": False,
            },
        ] * 10
        s = _judge_l2_summary(judged)
        self.assertFalse(s["accept_l2"])

    def test_normalize_tools_vendor_to_generic(self) -> None:
        out = normalize_tools_required(["neon", "telethon", "python"])
        self.assertEqual(out, ("postgresql", "telegram", "python"))

    def test_fail_tools_vendor_lock(self) -> None:
        r = audit_lead(
            _mock_lead(
                tools_required=["postgresql", "python"],
                tools_required_raw=["neon", "python"],
            )
        )
        self.assertFalse(r["tools_pass"])
        self.assertTrue(any("vendor_lock" in f for f in r["fails"]))

    def test_o72e3_worst_term_groups_defined(self) -> None:
        for lead_id in (8704, 8776, 8925):
            groups = o72e3_worst_draft_term_groups(lead_id)
            self.assertIsNotNone(groups)
            self.assertGreaterEqual(len(groups or ()), 2)

    def test_o72e3_worst_good_drafts_pass_term_gate(self) -> None:
        for lead_id, fx in _O72E3_WORST_LEADS.items():
            self.assertTrue(
                draft_passes_o72e3_worst_terms(fx["good_draft"], lead_id),
                msg=f"lead #{lead_id} good_draft",
            )
            groups = o72e3_worst_draft_term_groups(lead_id)
            assert groups is not None
            self.assertGreaterEqual(
                count_o72e3_niche_term_groups(fx["good_draft"], groups), 2
            )

    def test_o72e3_worst_bad_drafts_fail_term_gate(self) -> None:
        for lead_id, fx in _O72E3_WORST_LEADS.items():
            self.assertFalse(
                draft_passes_o72e3_worst_terms(fx["bad_draft"], lead_id),
                msg=f"lead #{lead_id} bad_draft",
            )


