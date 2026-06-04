"""O108: TZ attachments — detect, extract, anti-hallucination guards."""

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
    has_extracted_attachment_marker,
    has_skipped_attachment_marker,
    max_archive_bytes,
    max_text_bytes,
    reply_attachment_claim_reason,
)


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


if __name__ == "__main__":
    unittest.main()
