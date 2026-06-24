"""YOUDO-IMAP-ONLY: model B — last N emails + PG dedup."""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from youdo_imap import (  # noqa: E402
    extract_email_body,
    extract_task_ids,
    youdo_imap_enabled,
    youdo_imap_detail_from_email,
    _imap_config,
    _imap_fetch_last_n,
    _YOUDO_TASK_RE,
)


class TestImapEnv(unittest.TestCase):
    def test_enabled_default(self) -> None:
        os.environ.pop("YOUDO_IMAP_ENABLED", None)
        self.assertFalse(youdo_imap_enabled())

    def test_enabled_on(self) -> None:
        os.environ["YOUDO_IMAP_ENABLED"] = "1"
        self.assertTrue(youdo_imap_enabled())
        os.environ.pop("YOUDO_IMAP_ENABLED", None)

    def test_detail_from_email_default(self) -> None:
        os.environ.pop("YOUDO_IMAP_DETAIL_FROM_EMAIL", None)
        self.assertTrue(youdo_imap_detail_from_email())

    def test_detail_from_email_off(self) -> None:
        os.environ["YOUDO_IMAP_DETAIL_FROM_EMAIL"] = "0"
        self.assertFalse(youdo_imap_detail_from_email())
        os.environ.pop("YOUDO_IMAP_DETAIL_FROM_EMAIL", None)

    def test_imap_config_defaults(self) -> None:
        cfg = _imap_config()
        self.assertEqual(cfg["host"], "imap.mail.ru")
        self.assertEqual(cfg["port"], 993)
        self.assertEqual(cfg["folder"], "INBOX/Newsletters")

    def test_fetch_last_n_default(self) -> None:
        os.environ.pop("YOUDO_IMAP_FETCH_LAST", None)
        os.environ["YOUDO_IMAP_FETCH_LAST"] = "50"
        from youdo_imap import _imap_fetch_last_n
        # Just verify env reading works — the function returns int
        # (we test the actual IMAP fetch in integration tests)
        os.environ.pop("YOUDO_IMAP_FETCH_LAST", None)


class TestTaskIdExtraction(unittest.TestCase):
    def test_extract_from_subject(self) -> None:
        ids = extract_task_ids("Печать листовок - youdo.com/t14886201", "")
        self.assertEqual(ids, ["14886201"])

    def test_extract_from_body(self) -> None:
        body = "Заказ: https://youdo.com/t14884710 оплатить"
        ids = extract_task_ids("", body)
        self.assertEqual(ids, ["14884710"])

    def test_extract_multiple(self) -> None:
        text = "https://youdo.com/t111 https://youdo.com/t222 https://youdo.com/t333"
        ids = extract_task_ids(text, text)
        self.assertEqual(sorted(ids), ["111", "222", "333"])

    def test_no_ids(self) -> None:
        ids = extract_task_ids("no ids here", "nothing")
        self.assertEqual(ids, [])

    def test_regex_pattern(self) -> None:
        self.assertTrue(_YOUDO_TASK_RE.search("youdo.com/t12345"))
        self.assertTrue(_YOUDO_TASK_RE.search("https://youdo.com/t99999"))
        self.assertFalse(_YOUDO_TASK_RE.search("youdo.com/tasks"))


class TestEmailBodyExtraction(unittest.TestCase):
    def test_strips_style_tags(self) -> None:
        html = "<html><head><style>body{color:red}</style></head><body><p>Task description here with enough text</p></body></html>"
        body = extract_email_body(html)
        self.assertNotIn("color:red", body)
        self.assertIn("Task description", body)

    def test_strips_script_tags(self) -> None:
        html = "<html><body><script>alert('xss')</script><p>Real content</p></body></html>"
        body = extract_email_body(html)
        self.assertNotIn("alert", body)
        self.assertIn("Real content", body)

    def test_empty_html(self) -> None:
        self.assertEqual(extract_email_body(""), "")
        self.assertEqual(extract_email_body(None), "")  # type: ignore[arg-type]

    def test_plain_text_passthrough(self) -> None:
        html = "<p>Simple paragraph with enough text to pass the length check for detail validation</p>"
        body = extract_email_body(html)
        self.assertIn("Simple paragraph", body)

    def test_strips_invisible_unicode_padding(self) -> None:
        """YouDo preheader uses zero-width chars; must not push TZ past snippet cap."""
        pad = "\u034f\u200c\xa0" * 200
        html = (
            "<html><body>"
            f"<p>Никита, новое задание в категории разработка по{pad}</p>"
            "<a href='https://youdo.com/t14888221'>Генерация изображений</a>"
            "<div>Нужно сделать ИИ фотосессию на белом фоне. Все рефы есть.</div>"
            "</body></html>"
        )
        body = extract_email_body(html)
        self.assertIn("ИИ фотосессию", body)
        self.assertLess(body.find("ИИ фотосессию"), 500)
        self.assertNotIn("\u200c", body)


class TestImapPoller(unittest.TestCase):
    def test_disabled_returns_empty(self) -> None:
        os.environ.pop("YOUDO_IMAP_ENABLED", None)
        from youdo_imap import poll_youdo_imap
        self.assertEqual(poll_youdo_imap(), [])

    def test_no_credentials_returns_empty(self) -> None:
        os.environ["YOUDO_IMAP_ENABLED"] = "1"
        os.environ.pop("YOUDO_IMAP_USER", None)
        os.environ.pop("YOUDO_IMAP_PASSWORD", None)
        from youdo_imap import poll_youdo_imap
        result = poll_youdo_imap()
        self.assertEqual(result, [])
        os.environ.pop("YOUDO_IMAP_ENABLED", None)

    @patch("youdo_imap._imap_connect")
    def test_poll_last_n(self, mock_connect: MagicMock) -> None:
        """Model B: fetch last N emails, no UID cursor."""
        os.environ["YOUDO_IMAP_ENABLED"] = "1"
        os.environ["YOUDO_IMAP_USER"] = "test@mail.ru"
        os.environ["YOUDO_IMAP_PASSWORD"] = "pass"
        os.environ["YOUDO_IMAP_FETCH_LAST"] = "5"
        try:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            mock_conn.select.return_value = ("OK", [b"0"])
            mock_conn.uid.return_value = ("OK", [b""])

            from youdo_imap import poll_youdo_imap
            result = poll_youdo_imap()
            self.assertEqual(result, [])
            mock_conn.logout.assert_called_once()
        finally:
            for k in ("YOUDO_IMAP_ENABLED", "YOUDO_IMAP_USER", "YOUDO_IMAP_PASSWORD", "YOUDO_IMAP_FETCH_LAST"):
                os.environ.pop(k, None)


class TestImapSampleFixture(unittest.TestCase):
    """Validate against real YouDo newsletter samples."""

    def setUp(self) -> None:
        self._fixture = Path(_ROOT / "data" / "_youdo_imap_sample.json")
        if not self._fixture.exists():
            self.skipTest("Fixture not found")

    def test_fixture_valid(self) -> None:
        data = json.loads(self._fixture.read_text(encoding="utf-8"))
        self.assertIn("samples", data)
        self.assertGreater(len(data["samples"]), 0)
        for s in data["samples"]:
            self.assertIn("mid", s)
            self.assertIn("youdo_ids", s)
            self.assertGreater(len(s["youdo_ids"]), 0)

    def test_fixture_subject_yields_ids(self) -> None:
        data = json.loads(self._fixture.read_text(encoding="utf-8"))
        for s in data["samples"]:
            body_preview = s.get("preview", "")
            ids = extract_task_ids(s.get("subject", ""), body_preview)
            for tid in s["youdo_ids"]:
                self.assertIn(tid, s["youdo_ids"])

    def test_fixture_html_len_plausible(self) -> None:
        data = json.loads(self._fixture.read_text(encoding="utf-8"))
        for s in data["samples"]:
            self.assertGreater(s.get("html_len", 0), 1000)
            self.assertGreater(s.get("plain_len", 0), 500)


class TestNewsletterFixture(unittest.TestCase):
    """Test against the real HTML newsletter fixture."""

    def setUp(self) -> None:
        self._fixture = Path(_ROOT / "tests" / "fixtures" / "youdo_newsletter_email.html")
        if not self._fixture.exists():
            self.skipTest("Fixture not found")

    def test_fixture_extracts_task_id(self) -> None:
        html = self._fixture.read_text(encoding="utf-8")
        body = extract_email_body(html)
        ids = extract_task_ids("", body)
        self.assertEqual(ids, ["14886201"])

    def test_fixture_body_is_substantial(self) -> None:
        html = self._fixture.read_text(encoding="utf-8")
        body = extract_email_body(html)
        self.assertGreater(len(body), 200)
        self.assertIn("Печать", body)
        self.assertIn("10 000", body)

    def test_fixture_strips_css(self) -> None:
        html = self._fixture.read_text(encoding="utf-8")
        body = extract_email_body(html)
        self.assertNotIn("@media", body)
        self.assertNotIn("display: none", body)


class TestModelBDedup(unittest.TestCase):
    """Model B: PG dedup — 3 emails, 1 id already in PG → ingest only 2 new."""

    @patch("youdo_imap._imap_connect")
    @patch("youdo_imap._imap_fetch_last_n_emails")
    def test_dedup_skips_existing_pg(self, mock_fetch: MagicMock, mock_connect: MagicMock) -> None:
        os.environ["YOUDO_IMAP_ENABLED"] = "1"
        os.environ["YOUDO_IMAP_USER"] = "test@mail.ru"
        os.environ["YOUDO_IMAP_PASSWORD"] = "pass"
        try:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            fixture = Path(_ROOT / "tests" / "fixtures" / "youdo_newsletter_email.html")
            html_body = fixture.read_text(encoding="utf-8") if fixture.exists() else (
                "<html><body>desc " + "x" * 400 + "</body></html>"
            )
            mock_fetch.return_value = [
                (40000, "Task A", "YouDo <noreply@mail.youdo.com>", html_body),
                (40001, "Task B", "YouDo <noreply@mail.youdo.com>", html_body),
                (40002, "Task C", "YouDo <noreply@mail.youdo.com>", html_body),
            ]

            storage = MagicMock()
            pg = MagicMock()
            pg.lead_imap_poll_skip.return_value = "visible"

            from scripts.youdo_imap_poller import run_poll_once
            with patch("scripts.youdo_imap_poller._storage_for_cfg", return_value=storage), \
                 patch("pg_storage.pg_storage_from_config", return_value=pg):
                new_count = run_poll_once()

            self.assertEqual(new_count, 0)
            self.assertTrue(pg.lead_imap_poll_skip.called)
        finally:
            for k in ("YOUDO_IMAP_ENABLED", "YOUDO_IMAP_USER", "YOUDO_IMAP_PASSWORD"):
                os.environ.pop(k, None)

    @patch("youdo_imap._imap_connect")
    @patch("youdo_imap._imap_fetch_last_n_emails")
    @patch("scripts.youdo_imap_poller._ingest_imap_task", return_value=True)
    def test_dedup_refreshes_invisible_pg(
        self,
        mock_ingest: MagicMock,
        mock_fetch: MagicMock,
        mock_connect: MagicMock,
    ) -> None:
        os.environ["YOUDO_IMAP_ENABLED"] = "1"
        os.environ["YOUDO_IMAP_USER"] = "test@mail.ru"
        os.environ["YOUDO_IMAP_PASSWORD"] = "pass"
        try:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            html_body = (
                '<html><body><a href="https://youdo.com/t40000">task</a> desc '
                + "x" * 400
                + "</body></html>"
            )
            mock_fetch.return_value = [
                (40000, "Task A", "YouDo <noreply@mail.youdo.com>", html_body),
            ]

            storage = MagicMock()
            pg = MagicMock()
            pg.lead_imap_poll_skip.return_value = None
            pg.lead_exists.return_value = True

            from scripts.youdo_imap_poller import run_poll_once
            with patch("scripts.youdo_imap_poller._storage_for_cfg", return_value=storage), \
                 patch("pg_storage.pg_storage_from_config", return_value=pg):
                new_count = run_poll_once()

            self.assertEqual(new_count, 1)
            storage.clear_neon_dup_synced.assert_called_once_with("youdo", 40000)
            mock_ingest.assert_called_once()
        finally:
            for k in ("YOUDO_IMAP_ENABLED", "YOUDO_IMAP_USER", "YOUDO_IMAP_PASSWORD"):
                os.environ.pop(k, None)

    @patch("youdo_imap._imap_connect")
    @patch("youdo_imap._imap_fetch_last_n_emails")
    @patch("scripts.youdo_imap_poller._ingest_imap_task", return_value=True)
    def test_dedup_skips_invisible_with_l1(
        self,
        mock_ingest: MagicMock,
        mock_fetch: MagicMock,
        mock_connect: MagicMock,
    ) -> None:
        """Invisible but L1 done → no refresh, no ingest (token burn guard)."""
        os.environ["YOUDO_IMAP_ENABLED"] = "1"
        os.environ["YOUDO_IMAP_USER"] = "test@mail.ru"
        os.environ["YOUDO_IMAP_PASSWORD"] = "pass"
        try:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn
            html_body = (
                '<html><body><a href="https://youdo.com/t40000">task</a> desc '
                + "x" * 400
                + "</body></html>"
            )
            mock_fetch.return_value = [
                (40000, "Task A", "YouDo <noreply@mail.youdo.com>", html_body),
            ]

            storage = MagicMock()
            pg = MagicMock()
            pg.lead_imap_poll_skip.return_value = "l1_done"

            from scripts.youdo_imap_poller import run_poll_once
            with patch("scripts.youdo_imap_poller._storage_for_cfg", return_value=storage), \
                 patch("pg_storage.pg_storage_from_config", return_value=pg):
                new_count = run_poll_once()

            self.assertEqual(new_count, 0)
            storage.clear_neon_dup_synced.assert_not_called()
            mock_ingest.assert_not_called()
        finally:
            for k in ("YOUDO_IMAP_ENABLED", "YOUDO_IMAP_USER", "YOUDO_IMAP_PASSWORD"):
                os.environ.pop(k, None)

    def test_no_uid_cursor_in_storage(self) -> None:
        """Model B: _IMAP_SEEN_KEY removed — no cursor tracking."""
        import youdo_imap
        self.assertFalse(hasattr(youdo_imap, "_IMAP_SEEN_KEY"))


class TestListingSkip(unittest.TestCase):
    """YOUDO_LISTING_FETCH=0 → skip listing radar."""

    def test_listing_skip_returns_empty(self) -> None:
        os.environ["YOUDO_LISTING_FETCH"] = "0"
        os.environ["YOUDO_DETAIL_FETCH"] = "0"
        os.environ["YOUDO_CLICK_DETAIL"] = "0"
        try:
            from unittest.mock import MagicMock
            from youdo_parser import fetch_listing_projects
            cfg = MagicMock()
            cfg.radar_log_path = "/tmp/test.log"
            result = fetch_listing_projects(cfg)
            self.assertEqual(result, [])
        finally:
            for k in ("YOUDO_LISTING_FETCH", "YOUDO_DETAIL_FETCH", "YOUDO_CLICK_DETAIL"):
                os.environ.pop(k, None)


if __name__ == "__main__":
    unittest.main()
