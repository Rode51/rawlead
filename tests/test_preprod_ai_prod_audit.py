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
    sanitize_l1_category,
    sanitize_tools_for_tz,
    O72E5_ANCHOR_IDS,
)
from tools_catalog import is_known_tool, normalize_tools_required  # noqa: E402


# O72e-3 judge worst-3 (fixtures from preprod_ai_prod_audit.json)
_O72E3_WORST_LEADS = {
    8704: {
        "title": "Разработка фирменного шрифта и логотипа гостиницы",
        "task_summary": "Разработать фирменный логотип и шрифт для новой гостиницы с акцентом на узнаваемость.",
        "good_draft": (
            "Здравствуйте! Разработаю фирменный логотип и шрифт для гостиницы Ирбис. "
            "Сначала исследование и концепции в Illustrator, затем векторизация и глифы в FontLab. "
            "Параллельно доработаю знак в Photoshop и подготовлю файлы для печати. "
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
            "Здравствуйте! Проведу аудит скорости WordPress+Elementor+WooCommerce+Tutor LMS на bwa-akademy. "
            "Сначала PageSpeed, Waterfall и метрики LCP/CLS, затем WP Rocket и критический CSS. "
            "Отдельно разберу DOM Elementor, отложенную загрузку сторонних трекеров и Ajax Tutor LMS. "
            "Какие аналитические пиксели критичны при первой загрузке, а какие можно defer?"
        ),
        "bad_draft": "Готов провести глубокий аудит и предложить план улучшения скорости.",
    },
    8925: {
        "title": "Скрипты из Google-таблиц — адаптация к Rhino V8",
        "task_summary": "Адаптировать три скрипта Google-таблицы для работы в новой среде Rhino V8.",
        "good_draft": (
            "Здравствуйте! Адаптирую три сценария Google Apps Script (JavaScript) под Rhino V8. "
            "Сначала аудит API и синтаксиса ES6+ в Apps Script, затем поочерёдная миграция скриптов с таблицей. "
            "Проверю обращения к Google-таблице после перехода на Rhino V8. "
            "Можете дать доступ к исходникам в старой среде для оценки объёма?"
        ),
        "bad_draft": "Готов проанализировать логику и переработать скрипты на Python.",
    },
    8726: {
        "title": "Грамотная e-mail рассылка КП базе ( в «Входящие»)",
        "body": "Нужно провести email-рассылку с SPF, DKIM, DMARC и отчётом доставляемости. База клиентов Excel/CSV.",
        "category": "dev",
        "expected_category": "marketing",
        "good_draft": (
            "Здравствуйте! Настрою email-рассылку КП с фокусом на доставляемость во «Входящие». "
            "Сначала проверю SPF/DKIM/DMARC и верстку письма без стоп-слов. "
            "Затем импортирую базу из Excel/CSV, настрою Reply-to и подготовлю отчёт по открытиям. "
            "Рассылка с вашего домена или с прогретого SMTP?"
        ),
        "bad_draft": "Готов настроить рассылку и обсудить детали проекта.",
    },
    8836: {
        "title": "Создание продающего лендинга",
        "body": "Лендинг с интеграцией Kaspi Pay, автодоставкой на email и установкой на хостинг.",
        "category": "design",
        "expected_category": "dev",
        "good_draft": (
            "Здравствуйте! Разработаю продающий лендинг с Kaspi Pay и автодоставкой на email клиента. "
            "Сначала сверстаю страницу на PHP и подключу оплату Kaspi Pay. "
            "Затем настрою выдачу файла на email и деплой на хостинг. "
            "Домен и хостинг уже есть?"
        ),
        "bad_draft": "Готов сделать красивый лендинг и обсудить детали.",
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
            "Здравствуйте! Сделаю парсер на Python для выгрузки данных в CSV. "
            "Сначала разберу структуру сайта, затем напишу скрипт и проверю выгрузку."
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
                reply_draft=(
                    "Здравствуйте! Сделаю парсер на Python. "
                    "Готов взять задачу в работу сегодня."
                ),
            )
        )
        self.assertTrue(r["draft_only_pass"])
        self.assertIn("warn:reply_draft_cliche", r["warns"])

    def test_fail_reply_draft_missing_greeting(self) -> None:
        r = audit_lead(
            _mock_lead(
                reply_draft="Сделаю парсер на Python и выгружу данные в CSV.",
            )
        )
        self.assertFalse(r["draft_only_pass"])
        self.assertTrue(any("Здравствуйте" in f for f in r["fails"]))

    def test_fail_reply_draft_zainteresoval_opener(self) -> None:
        r = audit_lead(
            _mock_lead(
                reply_draft=(
                    "Заинтересовал проект. Сначала разберу структуру сайта "
                    "и напишу парсер на Python."
                ),
            )
        )
        self.assertFalse(r["draft_only_pass"])
        fails_text = " ".join(r["fails"])
        self.assertTrue(
            "Заинтересовал" in fails_text or "Здравствуйте" in fails_text,
            msg=fails_text,
        )

    def test_fail_reply_draft_beru_v_rabotu(self) -> None:
        r = audit_lead(
            _mock_lead(
                reply_draft=(
                    "Здравствуйте! Беру задачу в работу по парсеру на Python. "
                    "Сначала разберу структуру сайта."
                ),
            )
        )
        self.assertFalse(r["draft_only_pass"])
        self.assertTrue(any("беру в работу" in f for f in r["fails"]))

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
        judged = [{"lead_id": i, "context_understanding": 4, "l1_usable": True} for i in range(10)]
        judged.extend(
            [{"lead_id": i, "context_understanding": 4, "l1_usable": False} for i in range(10, 13)]
        )
        s = _judge_l1_summary(judged)
        self.assertTrue(s["accept_l1"])
        self.assertGreaterEqual(s["l1_usable_pct"], 70)

    def test_judge_l1_summary_accept_complexity(self) -> None:
        judged = [
            {
                "lead_id": i,
                "context_understanding": 4,
                "l1_usable": True,
                "complexity_rating": 5,
                "complexity_ok": True,
            }
            for i in range(7)
        ]
        judged.extend(
            [
                {
                    "lead_id": i,
                    "context_understanding": 4,
                    "l1_usable": True,
                    "complexity_rating": 3,
                    "complexity_ok": False,
                }
                for i in range(7, 10)
            ]
        )
        s = _judge_l1_summary(judged)
        self.assertTrue(s["accept_complexity"])
        self.assertGreaterEqual(s["complexity_ok_pct"], 70)

    def test_judge_l1_summary_fail_complexity(self) -> None:
        judged = [
            {
                "lead_id": i,
                "context_understanding": 4,
                "l1_usable": True,
                "complexity_rating": 2,
                "complexity_ok": False,
                "complexity_prompt_fix": "завышать complexity для монолитов",
            }
            for i in range(10)
        ]
        s = _judge_l1_summary(judged)
        self.assertFalse(s["accept_complexity"])
        self.assertTrue(s["complexity_prompt_recommendations"])

    def test_parse_feed_visible_legacy_verdict(self) -> None:
        from ai_analyze import _parse_lite_analysis

        visible = _parse_lite_analysis(
            {
                "feed_visible": True,
                "task_summary": "Парсер на Python.",
                "lead_tags": ["python"],
                "ai_reasons": ["a", "b"],
            }
        )
        self.assertTrue(visible.feed_visible)
        self.assertEqual(visible.verdict, "Брать")

        hidden = _parse_lite_analysis(
            {
                "verdict": "МИМО",
                "task_summary": "",
                "lead_tags": [],
                "ai_reasons": ["спам"],
            }
        )
        self.assertFalse(hidden.feed_visible)
        self.assertEqual(hidden.verdict, "МИМО")

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
        for lead_id in O72E5_ANCHOR_IDS:
            groups = o72e3_worst_draft_term_groups(lead_id)
            self.assertIsNotNone(groups)
            self.assertGreaterEqual(len(groups or ()), 2)

    def test_o72e5_anchor_good_drafts_pass_term_gate(self) -> None:
        for lead_id in O72E5_ANCHOR_IDS:
            fx = _O72E3_WORST_LEADS.get(lead_id)
            if not fx or "good_draft" not in fx:
                continue
            self.assertTrue(
                draft_passes_o72e3_worst_terms(fx["good_draft"], lead_id),
                msg=f"lead #{lead_id} good_draft",
            )

    def test_o72e5_l1_category_rules(self) -> None:
        for lead_id, fx in _O72E3_WORST_LEADS.items():
            expected = fx.get("expected_category")
            if not expected:
                continue
            got = sanitize_l1_category(
                fx.get("category") or "dev",
                title=fx.get("title") or "",
                snippet=fx.get("body") or fx.get("task_summary") or "",
            )
            self.assertEqual(got, expected, msg=f"lead #{lead_id} category")

    def test_o72e5_bench_fixture_anchors_audit_pass(self) -> None:
        path = _ROOT / "tests" / "fixtures" / "o72e_bench_leads.json"
        self.assertTrue(path.is_file(), "run export_o72e_bench_leads.py first")
        import json

        doc = json.loads(path.read_text(encoding="utf-8"))
        anchor_ids = {int(x) for x in doc.get("anchor_ids") or []}
        self.assertGreaterEqual(len(anchor_ids), 5)
        by_id = {int(l["lead_id"]): l for l in doc.get("leads") or []}
        for lid in anchor_ids:
            lead = by_id.get(lid)
            self.assertIsNotNone(lead, msg=f"missing anchor #{lid}")
            r = audit_lead(lead)
            self.assertTrue(r["draft_only_pass"], msg=f"#{lid} draft")
            self.assertTrue(r["tools_pass"], msg=f"#{lid} tools")

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

    def test_o72e7_tools_sanitize_gas_not_python(self) -> None:
        fx = _O72E3_WORST_LEADS[8925]
        got = sanitize_tools_for_tz(
            ("python", "google_sheets_api"),
            title=fx["title"],
            snippet=fx.get("task_summary") or "",
            task_summary=fx["task_summary"],
        )
        self.assertNotIn("python", got)
        self.assertIn("javascript", got)
        self.assertIn("google_apps_script", got)
        self.assertIn("rhino", got)
        self.assertIn("google_sheets_api", got)

    def test_o72e7_l1_tags_gas_not_python(self) -> None:
        from ai_analyze import sanitize_l1_dev_design_marketing_tags

        fx = _O72E3_WORST_LEADS[8925]
        got = sanitize_l1_dev_design_marketing_tags(
            ("python", "api_integration"),
            title=fx["title"],
            snippet=fx.get("task_summary") or "",
        )
        self.assertNotIn("python", got)
        self.assertIn("javascript", got)

    def test_o72e7_tools_sanitize_email_not_dev(self) -> None:
        fx = _O72E3_WORST_LEADS[8726]
        got = sanitize_tools_for_tz(
            ("consulting", "crm"),
            title=fx["title"],
            snippet=fx.get("body") or "",
        )
        self.assertNotIn("python", got)
        self.assertIn("email_marketing", got)

    def test_o72e3_worst_bad_drafts_fail_term_gate(self) -> None:
        for lead_id, fx in _O72E3_WORST_LEADS.items():
            self.assertFalse(
                draft_passes_o72e3_worst_terms(fx["bad_draft"], lead_id),
                msg=f"lead #{lead_id} bad_draft",
            )


