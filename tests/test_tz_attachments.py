"""O108/O162: TZ attachments — detect, extract, anti-hallucination guards."""

from __future__ import annotations

import io
import sys
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from tz_attachments import (  # noqa: E402
    ATTACHMENT_EXTRACTED_MARKER,
    SKIPPED_MARKER_PREFIX,
    enrich_body_with_attachments,
    extract_attachment_text,
    find_attachment_urls,
    find_kwork_embedded_attachment_urls,
    has_extracted_attachment_marker,
    has_skipped_attachment_marker,
    max_archive_bytes,
    max_text_bytes,
    reply_attachment_claim_reason,
)
from ai_analyze import sanitize_tools_for_tz  # noqa: E402


class TestTzAttachmentGuards(unittest.TestCase):
    def test_claim_blocked_without_marker(self) -> None:
        desc = "Предоставлю ZIP архив с двумя лендингами."
        draft = "Здравствуйте! Вижу ZIP с готовой вёрсткой — загружу HTML."
        self.assertEqual(
            reply_attachment_claim_reason(draft, desc),
            "attachment_claim_without_file",
        )

    def test_claim_allowed_with_marker(self) -> None:
        desc = (
            "Текст заказа.\n\n"
            f"{ATTACHMENT_EXTRACTED_MARKER} из layout.zip]\n"
            "index.html landing one"
        )
        draft = "Здравствуйте! Вижу ZIP с готовой вёрсткой — загружу HTML."
        self.assertIsNone(reply_attachment_claim_reason(draft, desc))

    def test_no_claim_without_phrase(self) -> None:
        desc = "Предоставлю ZIP архив."
        draft = "Здравствуйте! Загружу HTML-лендинги на WordPress без шапки сайта."
        self.assertIsNone(reply_attachment_claim_reason(draft, desc))

    def test_skip_ack_allowed_with_skipped_marker(self) -> None:
        desc = (
            f"{SKIPPED_MARKER_PREFIX}, 52 MB, текст не извлечён из-за размера]"
        )
        draft = (
            "Здравствуйте! Вижу, что прикрепили архив 52 MB — ознакомлюсь в диалоге."
        )
        self.assertIsNone(reply_attachment_claim_reason(draft, desc))

    def test_skip_content_claim_blocked(self) -> None:
        desc = (
            f"{SKIPPED_MARKER_PREFIX}, 52 MB, текст не извлечён из-за размера]"
        )
        draft = "Здравствуйте! Вижу ZIP с готовой HTML-вёрсткой внутри — загружу."
        self.assertEqual(
            reply_attachment_claim_reason(draft, desc),
            "attachment_content_without_extract",
        )


class TestFindAttachmentUrls(unittest.TestCase):
    def test_fl_download_link(self) -> None:
        html = """
        <div class="fl-project-content">
          <a href="/files/tz.docx">Скачать ТЗ</a>
        </div>
        """
        urls = find_attachment_urls(html, "https://www.fl.ru/projects/1/test.html")
        self.assertEqual(len(urls), 1)
        self.assertTrue(urls[0][0].endswith("tz.docx"))

    def test_kwork_zip_link(self) -> None:
        html = '<a href="https://cdn.kwork.ru/files/job.zip">archive.zip</a>'
        urls = find_attachment_urls(html, "https://kwork.ru/projects/99/view")
        self.assertEqual(len(urls), 1)
        self.assertIn(".zip", urls[0][0])

    def test_fl_footer_regulations_skipped(self) -> None:
        html = """
        <footer>
          <a href="/about/appendix_2_regulations.pdf">Правила пользования</a>
          <a href="https://st.fl.ru/about/documents/cookie_accept.pdf">Cookie</a>
        </footer>
        """
        urls = find_attachment_urls(
            html, "https://www.fl.ru/projects/5506883/test.html"
        )
        self.assertEqual(urls, [])

    def test_fl_real_tz_with_footer(self) -> None:
        html = """
        <div class="b-post__attach">
          <a href="/files/tz/project_brief.docx">Скачать ТЗ</a>
        </div>
        <footer>
          <a href="/about/appendix_2_regulations.pdf">Правила</a>
        </footer>
        """
        urls = find_attachment_urls(
            html, "https://www.fl.ru/projects/5506883/test.html"
        )
        self.assertEqual(len(urls), 1)
        self.assertTrue(urls[0][0].endswith("project_brief.docx"))

    def test_kwork_footer_legal_skipped(self) -> None:
        html = """
        <footer>
          <a href="https://kwork.ru/pages/privacy_policy.pdf">Политика</a>
          <a href="https://cdn.kwork.ru/files/user_agreement.pdf">Соглашение</a>
        </footer>
        """
        urls = find_attachment_urls(html, "https://kwork.ru/projects/99/view")
        self.assertEqual(urls, [])

    def test_kwork_real_docx_with_footer(self) -> None:
        html = """
        <div class="wants-card__files">
          <a href="https://cdn.kwork.ru/files/tz_brief.docx">Скачать ТЗ</a>
        </div>
        <footer>
          <a href="https://kwork.ru/documents/offer.pdf">Оферта</a>
        </footer>
        """
        urls = find_attachment_urls(html, "https://kwork.ru/projects/99/view")
        self.assertEqual(len(urls), 1)
        self.assertTrue(urls[0][0].endswith("tz_brief.docx"))

    def test_kwork_embedded_json_pdf_url(self) -> None:
        html = (
            '{"files":[{"FID":1,"fname":"brief.pdf","url":'
            '"https://kwork.ru/files/uploaded/ab/cd/ef/brief.pdf"}]}'
        )
        urls = find_kwork_embedded_attachment_urls(
            html, "https://kwork.ru/projects/3193806/view"
        )
        self.assertEqual(len(urls), 1)
        self.assertIn("brief.pdf", urls[0][0])

    def test_kwork_enrich_embedded_pdf_with_auth_download(self) -> None:
        html = (
            '{"files":[{"fname":"tz.pdf","url":'
            '"https://kwork.ru/files/uploaded/x/y/z/tz.pdf"}]}'
        )
        cfg = MagicMock(http_user_agent="test")
        with patch("tz_attachments.probe_content_length", return_value=-1):
            with patch(
                "tz_session.download_with_auth_session",
                return_value=(b"%PDF-1.4 text", None),
            ):
                with patch(
                    "tz_attachments.extract_attachment_text",
                    return_value=("Instruction text", ("tz.pdf",)),
                ):
                    result = enrich_body_with_attachments(
                        "kwork",
                        html,
                        "Listing mentions .pdf attachment",
                        cfg,
                        page_url="https://kwork.ru/projects/3193806/view",
                    )
        self.assertTrue(result.attachment_extracted)
        self.assertIn("Instruction text", result.body)

    def test_kwork_auth_html_fetch_when_no_urls(self) -> None:
        cfg = MagicMock(http_user_agent="test")
        auth_html = '<a href="https://kwork.ru/files/uploaded/a/b/c/tz.pdf">pdf</a>'
        with patch(
            "tz_session.fetch_detail_html_with_auth",
            return_value=auth_html,
        ):
            with patch("tz_attachments.probe_content_length", return_value=100):
                with patch(
                    "tz_attachments.download_attachment",
                    return_value=(b"pdf bytes", None),
                ):
                    with patch(
                        "tz_attachments.extract_attachment_text",
                        return_value=("TZ body", ("tz.pdf",)),
                    ):
                        result = enrich_body_with_attachments(
                            "kwork",
                            "<html>no links but pdf promised</html>",
                            "Need work per attached .pdf file",
                            cfg,
                            page_url="https://kwork.ru/projects/3193806/view",
                        )
        self.assertTrue(has_extracted_attachment_marker(result.body))
        self.assertIn("TZ body", result.body)


class TestExtractAttachmentText(unittest.TestCase):
    def test_txt_extract(self) -> None:
        text, files = extract_attachment_text(b"Hello TZ", "readme.txt")
        self.assertEqual(text, "Hello TZ")
        self.assertEqual(files, ("readme.txt",))

    def test_zip_inner_html(self) -> None:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr(
                "landing/index.html",
                "<html><body><p>Landing one</p></body></html>",
            )
        text, files = extract_attachment_text(buf.getvalue(), "layouts.zip")
        self.assertIn("Landing one", text)
        self.assertIn("layouts.zip", files)


class TestEnrichBody(unittest.TestCase):
    def test_enrich_appends_marker_block(self) -> None:
        html = '<a href="https://fl.ru/tz.txt">tz</a>'
        cfg = MagicMock(http_user_agent="test")
        with patch("tz_attachments.download_attachment", return_value=(b"Full TZ text", None)):
            with patch("tz_attachments.probe_content_length", return_value=100):
                result = enrich_body_with_attachments(
                    "fl",
                    html,
                    "Short listing",
                    cfg,
                    page_url="https://fl.ru/projects/1/",
                    errors=[],
                )
        self.assertTrue(result.attachment_extracted)
        self.assertTrue(has_extracted_attachment_marker(result.body))
        self.assertIn("Full TZ text", result.body)
        self.assertEqual(result.tz_attachment.status, "extracted")

    def test_no_links_unchanged(self) -> None:
        cfg = MagicMock(http_user_agent="test")
        result = enrich_body_with_attachments(
            "kwork",
            "<html><body>no files</body></html>",
            "Body only",
            cfg,
            page_url="https://kwork.ru/projects/1/view",
        )
        self.assertFalse(result.attachment_extracted)
        self.assertEqual(result.body, "Body only")

    def test_fl_footer_only_no_extract(self) -> None:
        html = (
            '<footer><a href="/about/appendix_2_regulations.pdf">'
            "Правила</a></footer>"
        )
        cfg = MagicMock(http_user_agent="test")
        result = enrich_body_with_attachments(
            "fl",
            html,
            "Listing text",
            cfg,
            page_url="https://www.fl.ru/projects/5506883/test.html",
        )
        self.assertFalse(result.attachment_extracted)
        self.assertFalse(has_extracted_attachment_marker(result.body))
        self.assertEqual(result.body, "Listing text")

    def test_fl_legal_boilerplate_not_marked_extracted(self) -> None:
        html = '<a href="https://www.fl.ru/files/misc/site_rules.pdf">x</a>'
        cfg = MagicMock(http_user_agent="test")
        legal_text = (
            "Приложение №2 \nк Пользовательскому соглашению \n"
            "«Правила пользования Сайтом» \n"
            "Принимая во внимание, что Общество предоставляет"
        )
        with patch("tz_attachments.probe_content_length", return_value=100):
            with patch(
                "tz_attachments.download_attachment",
                return_value=(b"%PDF", None),
            ):
                with patch(
                    "tz_attachments.extract_attachment_text",
                    return_value=(legal_text, ("site_rules.pdf",)),
                ):
                    result = enrich_body_with_attachments(
                        "fl",
                        html,
                        "Listing text",
                        cfg,
                        page_url="https://www.fl.ru/projects/5506883/test.html",
                        errors=[],
                    )
        self.assertFalse(result.attachment_extracted)
        self.assertFalse(has_extracted_attachment_marker(result.body))
        self.assertEqual(result.body, "Listing text")

    def test_oversize_head_skipped_no_extract_marker(self) -> None:
        html = '<a href="https://fl.ru/big.pdf">big.pdf</a>'
        cfg = MagicMock(http_user_agent="test")
        big = max_text_bytes() + 1
        with patch("tz_attachments.probe_content_length", return_value=big):
            result = enrich_body_with_attachments(
                "fl",
                html,
                "Listing",
                cfg,
                page_url="https://fl.ru/projects/1/",
                errors=[],
            )
        self.assertFalse(result.attachment_extracted)
        self.assertFalse(has_extracted_attachment_marker(result.body))
        self.assertTrue(has_skipped_attachment_marker(result.body))
        self.assertEqual(result.tz_attachment.status, "skipped_size")

    def test_docx_under_limit_extracted(self) -> None:
        html = '<a href="https://fl.ru/tz.docx">tz.docx</a>'
        cfg = MagicMock(http_user_agent="test")
        payload = b"x" * (3 * 1024 * 1024)
        with patch("tz_attachments.probe_content_length", return_value=len(payload)):
            with patch(
                "tz_attachments.download_attachment",
                return_value=(payload, None),
            ):
                with patch(
                    "tz_attachments.extract_attachment_text",
                    return_value=("Docx TZ body", ("tz.docx",)),
                ):
                    result = enrich_body_with_attachments(
                        "fl",
                        html,
                        "Listing",
                        cfg,
                        page_url="https://fl.ru/projects/1/",
                    )
        self.assertTrue(has_extracted_attachment_marker(result.body))
        self.assertIn("Docx TZ body", result.body)

    def test_zip_over_archive_limit_listing_only(self) -> None:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("a/index.html", "x" * (3 * 1024 * 1024))
            zf.writestr("b/readme.txt", "readme")
        zip_data = buf.getvalue()
        self.assertGreater(len(zip_data), max_archive_bytes())

        html = '<a href="https://cdn.kwork.ru/big.zip">big.zip</a>'
        cfg = MagicMock(http_user_agent="test")
        with patch("tz_attachments.probe_content_length", return_value=None):
            with patch(
                "tz_attachments.download_attachment",
                return_value=(zip_data, None),
            ):
                result = enrich_body_with_attachments(
                    "kwork",
                    html,
                    "Kwork landing",
                    cfg,
                    page_url="https://kwork.ru/projects/1/view",
                )
        self.assertFalse(has_extracted_attachment_marker(result.body))
        self.assertTrue(has_skipped_attachment_marker(result.body))
        self.assertIn("index.html", result.body)
        self.assertEqual(result.tz_attachment.status, "skipped_size")


class TestReplyAttachmentPdfClaims(unittest.TestCase):
    """O162: pdf-claim phrases without extraction marker → attachment_claim_without_file."""

    def test_pdf_adjective_claim_blocked(self) -> None:
        desc = "Оформить готовую презентацию (юридический текст)."
        draft = "Здравствуйте! Изучил приложенного PDF — понял задачу, начну сразу."
        self.assertEqual(
            reply_attachment_claim_reason(draft, desc),
            "attachment_claim_without_file",
        )

    def test_pdf_from_phrase_blocked(self) -> None:
        desc = "Нужно оформить документ по образцу."
        draft = "Здравствуйте! Понял требования из pdf-файла — сделаю оформление быстро."
        self.assertEqual(
            reply_attachment_claim_reason(draft, desc),
            "attachment_claim_without_file",
        )

    def test_pdf_claim_allowed_with_extracted_marker(self) -> None:
        desc = (
            "Оформить презентацию.\n\n"
            f"{ATTACHMENT_EXTRACTED_MARKER} из brief.pdf]\n"
            "Юридический текст, 3 раздела."
        )
        draft = "Здравствуйте! Изучил приложенного PDF — понял задачу, начну сразу."
        self.assertIsNone(reply_attachment_claim_reason(draft, desc))


class TestSanitizeToolsTgDrop(unittest.TestCase):
    """O162: sanitize_tools_for_tz drops tg-tools when TZ has no Telegram mention."""

    def test_telegram_bot_dev_dropped_no_tg_in_tz(self) -> None:
        tools = ("telegram_bot_dev", "python", "postgresql")
        result = sanitize_tools_for_tz(
            tools,
            title="Оформить готовую презентацию",
            snippet="Юридический документ, нужно красиво оформить.",
            task_summary="Оформление PDF-документа",
        )
        self.assertNotIn("telegram_bot_dev", result)
        self.assertIn("python", result)

    def test_telegram_tool_dropped_no_tg_in_tz(self) -> None:
        tools = ("telegram", "python")
        result = sanitize_tools_for_tz(
            tools,
            title="Автоматизация рассылки по базе",
            snippet="Рассылка email по CSV-базе, нужен скрипт Python.",
            task_summary="Email рассылка по базе",
        )
        self.assertNotIn("telegram", result)

    def test_telegram_bot_dev_kept_when_tg_in_tz(self) -> None:
        tools = ("telegram_bot_dev", "python")
        result = sanitize_tools_for_tz(
            tools,
            title="TG-бот для автоответов",
            snippet="Нужен Telegram-бот на Python для автоматических ответов.",
            task_summary="Telegram бот",
        )
        self.assertIn("telegram_bot_dev", result)

    def test_telegram_kept_when_tg_abbrev_in_tz(self) -> None:
        tools = ("telegram", "python")
        result = sanitize_tools_for_tz(
            tools,
            title="Бот в ТГ канал",
            snippet="Пушить посты в ТГ-канал автоматически.",
            task_summary="Автопостинг в ТГ",
        )
        self.assertIn("telegram", result)


class TestAnalyzeSharedReplyAttachFail(unittest.TestCase):
    """O162: L2 last attempt attach fail → returns None, not last_draft."""

    def test_last_attempt_attach_fail_returns_none(self) -> None:
        from ai_analyze import AiLiteAnalysis, analyze_shared_reply_draft

        cfg = MagicMock()
        cfg.ai_active = True
        cfg.ai_provider = "openrouter"
        cfg.ai_model_shared_draft = "test-model"
        cfg.ai_api_key = "fake-key"

        lite = AiLiteAnalysis(
            feed_visible=True,
            task_summary="Оформление презентации в PDF",
        )
        # Draft contains attachment-claim phrase without marker in description
        bad_json = (
            '{"reply_draft": "Здравствуйте! Изучил приложенного PDF — '
            'понял задачу, начну сразу."}'
        )

        with (
            patch("ai_analyze._openrouter_chat", return_value=bad_json),
            patch("ai_analyze.openrouter_proxy_urls", return_value=[]),
            patch("ai_analyze.openrouter_proxy_hint", return_value="direct"),
            patch("ai_analyze._shared_reply_system", return_value="sys"),
            patch("l3_human_style.reply_ai_smell_reason", return_value=None),
            patch("l3_human_style.reply_retry_user_suffix", return_value=""),
        ):
            errors: list[str] = []
            result = analyze_shared_reply_draft(
                cfg,
                title="Оформить презентацию",
                budget_text="5000",
                lite=lite,
                description="Нужно оформить документ.",
                max_attempts=2,
                errors=errors,
            )

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
