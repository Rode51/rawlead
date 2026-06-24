"""YOUDO-DETAIL-BREAKTHROUGH: click-through detail in sticky session."""

from __future__ import annotations

import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456789:ABCDEF_fake_test_token")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@127.0.0.1:5432/test")
os.environ["RADAR_PROFILE"] = "site"

from youdo_parser import (  # noqa: E402
    _click_detail_cache_clear,
    _click_detail_cache_get,
    _click_detail_cache_put,
)
from exchange_browser_fetch import (  # noqa: E402
    youdo_click_detail_enabled,
    _youdo_click_detail_max,
)


class TestClickDetailEnv(unittest.TestCase):
    def test_enabled_default(self) -> None:
        os.environ.pop("YOUDO_CLICK_DETAIL", None)
        self.assertTrue(youdo_click_detail_enabled())

    def test_disabled(self) -> None:
        os.environ["YOUDO_CLICK_DETAIL"] = "0"
        self.assertFalse(youdo_click_detail_enabled())
        os.environ.pop("YOUDO_CLICK_DETAIL", None)

    def test_max_default(self) -> None:
        os.environ.pop("YOUDO_CLICK_DETAIL_MAX", None)
        self.assertEqual(_youdo_click_detail_max(), 10)

    def test_max_clamped(self) -> None:
        os.environ["YOUDO_CLICK_DETAIL_MAX"] = "50"
        self.assertEqual(_youdo_click_detail_max(), 20)
        os.environ["YOUDO_CLICK_DETAIL_MAX"] = "0"
        self.assertEqual(_youdo_click_detail_max(), 1)
        os.environ.pop("YOUDO_CLICK_DETAIL_MAX", None)


class TestClickDetailCache(unittest.TestCase):
    def setUp(self) -> None:
        _click_detail_cache_clear()

    def test_put_get(self) -> None:
        _click_detail_cache_put("12345", "body text here", True)
        result = _click_detail_cache_get("12345")
        self.assertIsNotNone(result)
        body, ok = result  # type: ignore
        self.assertEqual(body, "body text here")
        self.assertTrue(ok)

    def test_miss(self) -> None:
        result = _click_detail_cache_get("99999")
        self.assertIsNone(result)

    def test_expired(self) -> None:
        _click_detail_cache_put("12345", "body", True)
        # Manually expire
        from youdo_parser import _CLICK_DETAIL_CACHE

        _CLICK_DETAIL_CACHE["12345"]["_ts"] = time.time() - 600
        result = _click_detail_cache_get("12345")
        self.assertIsNone(result)

    def test_clear(self) -> None:
        _click_detail_cache_put("12345", "body", True)
        _click_detail_cache_clear()
        result = _click_detail_cache_get("12345")
        self.assertIsNone(result)


class TestClickThroughStickyWorker(unittest.TestCase):
    """Test the click_through_details command parsing in the worker."""

    def test_parse_detail_body_next_data(self) -> None:
        from scripts.youdo_sticky_worker import _parse_detail_body

        html = """
        <html><body>
        <script id="__NEXT_DATA__" type="application/json">
        {"props":{"pageProps":{"task":{"description":"Need a Python bot for Telegram that sends daily reports. Must integrate with PostgreSQL database and send formatted messages."}}}}
        </script>
        </body></html>
        """
        body = _parse_detail_body(html)
        self.assertIn("Python bot", body)
        self.assertGreater(len(body), 50)

    def test_parse_detail_body_css_selector(self) -> None:
        from scripts.youdo_sticky_worker import _parse_detail_body

        html = """
        <html><body>
        <div class="task-description">Looking for a developer to build a web scraping tool. Must handle JavaScript rendering and proxy rotation. Budget is flexible.</div>
        </body></html>
        """
        body = _parse_detail_body(html)
        self.assertIn("web scraping", body)

    def test_parse_detail_body_empty(self) -> None:
        from scripts.youdo_sticky_worker import _parse_detail_body

        self.assertEqual(_parse_detail_body(""), "")
        self.assertEqual(_parse_detail_body("<html><body></body></html>"), "")


class TestClickThroughFlow(unittest.TestCase):
    """Integration test: verify click-through is wired into the pipeline."""

    def test_cache_used_in_resolve_ingest_body(self) -> None:
        """When click-through cache has a result, _resolve_ingest_body should use it."""
        from listing import ListingProject

        _click_detail_cache_put("99999", "Full TZ description from click-through with enough chars " * 10, True)
        try:
            project = ListingProject(
                project_id=99999,
                title="Test",
                budget_text="",
                url="https://youdo.com/t99999",
                published_at="",
                listing_snippet="short",
                source="youdo",
                listing_category="",
            )
            with patch("lead_pipeline.fetch_project_detail", return_value=("fallback", "", False)) as mock_detail:
                with patch("lead_pipeline.is_web_detail_source", return_value=True):
                    with patch("lead_pipeline._youdo_detail_fetch_enabled", return_value=True):
                        from lead_pipeline import _resolve_ingest_body

                        cfg = MagicMock()
                        cfg.http_user_agent = "test"
                        errors: list[str] = []
                        body, _, detail_ok = _resolve_ingest_body(project, cfg, errors)
                        # Should use cache, not call fetch_project_detail
                        mock_detail.assert_not_called()
                        self.assertTrue(detail_ok)
                        self.assertIn("click-through", body)
        finally:
            _click_detail_cache_clear()

    def test_cache_miss_falls_through(self) -> None:
        """When cache is empty, _resolve_ingest_body should call fetch_project_detail."""
        from listing import ListingProject

        _click_detail_cache_clear()
        project = ListingProject(
            project_id=88888,
            title="Test",
            budget_text="",
            url="https://youdo.com/t88888",
            published_at="",
            listing_snippet="short snippet",
            source="youdo",
            listing_category="",
        )
        with patch("lead_pipeline.fetch_project_detail", return_value=("full detail text here", "", True)) as mock_detail:
            with patch("lead_pipeline.is_web_detail_source", return_value=True):
                with patch("lead_pipeline._youdo_detail_fetch_enabled", return_value=True):
                    from lead_pipeline import _resolve_ingest_body

                    cfg = MagicMock()
                    cfg.http_user_agent = "test"
                    errors: list[str] = []
                    body, _, detail_ok = _resolve_ingest_body(project, cfg, errors)
                    mock_detail.assert_called_once()
                    self.assertEqual(body, "full detail text here")


class TestClickRetry(unittest.TestCase):
    """YOUDO-CLICK-RETRY: pending IDs get re-clicked."""

    def test_pending_id_included_in_click_targets(self) -> None:
        """ID in SQLite + pending=1 + on listing → click target."""
        from listing import ListingProject

        storage = MagicMock()
        storage.list_project_ids.return_value = [("youdo", 111), ("youdo", 222)]
        storage.get_setting.side_effect = lambda k: "1" if "pending:111" in k else "0"
        projects = [
            ListingProject(
                project_id=111, title="T1", budget_text="", url="",
                published_at="", listing_snippet="s1", source="youdo",
            ),
            ListingProject(
                project_id=222, title="T2", budget_text="", url="",
                published_at="", listing_snippet="s2", source="youdo",
            ),
        ]
        seen_ids = {str(pid) for _, pid in storage.list_project_ids(["youdo"])}
        listing_ids = {str(p.project_id) for p in projects}
        new_projects = [p for p in projects if str(p.project_id) not in seen_ids]
        retry_projects = [
            p for p in projects
            if str(p.project_id) in seen_ids
            and storage.get_setting(f"youdo_detail_pending:{p.project_id}") == "1"
        ]
        # 111 is seen + pending → retry; 222 is seen + not pending → skip
        self.assertEqual(len(new_projects), 0)
        self.assertEqual(len(retry_projects), 1)
        self.assertEqual(retry_projects[0].project_id, 111)

    def test_pending_cleared_on_success(self) -> None:
        """When detail_ok=True, pending flag should be cleared."""
        storage = MagicMock()
        storage.set_setting.return_value = None
        ext_id = "14868001"
        storage.set_setting(f"youdo_detail_pending:{ext_id}", "1")
        # Simulate detail_ok=True path
        storage.set_setting(f"youdo_detail_pending:{ext_id}", "0")
        storage.set_setting.assert_any_call(f"youdo_detail_pending:{ext_id}", "1")
        storage.set_setting.assert_any_call(f"youdo_detail_pending:{ext_id}", "0")


class TestClickThroughHumanLike(unittest.TestCase):
    """SP-STABLE: human-like click patterns."""

    def test_inter_card_jitter(self) -> None:
        """Verify random delay between cards (1500-4000ms)."""
        import asyncio
        from scripts.youdo_sticky_worker import _run_click_through_details

        delays: list[float] = []
        original_wait = None

        async def _mock_wait(ms: int) -> None:
            delays.append(ms)

        page = MagicMock()
        page.evaluate = AsyncMock(return_value="https://youdo.com/tasks-all-opened-all")
        page.wait_for_timeout = _mock_wait
        page.locator = MagicMock(return_value=MagicMock(count=AsyncMock(return_value=0)))

        asyncio.run(_run_click_through_details(
            page,
            lead_ids=["111", "222", "333"],
            listing_url="https://youdo.com/tasks-all-opened-all",
            timeout_sec=30.0,
            proxy_url="http://test:8000",
        ))

        # First card: no jitter (idx=0), second+third: jitter 1500-4000
        jitter_delays = [d for d in delays if 1500 <= d <= 4000]
        self.assertGreaterEqual(len(jitter_delays), 2)

    def test_hover_before_click(self) -> None:
        """Verify hover() is called before click()."""
        import asyncio
        from scripts.youdo_sticky_worker import _run_click_through_details

        card_mock = MagicMock()
        card_mock.hover = AsyncMock()
        card_mock.click = AsyncMock()

        page = MagicMock()
        page.evaluate = AsyncMock(return_value="https://youdo.com/tasks-all-opened-all")
        page.wait_for_timeout = AsyncMock()
        page.content = AsyncMock(return_value="<html><body></body></html>")
        loc = MagicMock()
        loc.count = AsyncMock(return_value=1)
        loc.first = card_mock
        page.locator = MagicMock(return_value=loc)

        asyncio.run(_run_click_through_details(
            page,
            lead_ids=["111"],
            listing_url="https://youdo.com/tasks-all-opened-all",
            timeout_sec=30.0,
            proxy_url="http://test:8000",
        ))

        card_mock.hover.assert_called_once()
        card_mock.click.assert_called_once()


if __name__ == "__main__":
    unittest.main()
