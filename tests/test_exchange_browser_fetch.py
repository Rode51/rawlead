"""Shared Playwright instance: FL persistent + YouDo ephemeral in one radar cycle."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import MagicMock, patch

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

import exchange_browser_fetch as ebf  # noqa: E402
from exchange_browser_fetch import (  # noqa: E402
    _abort_youdo_lean_route,
    _DEFAULT_UA,
    _abort_heavy_route,
    _clear_stale_asyncio_loop,
    _fetch_youdo_ephemeral,
    _get_youdo_playwright,
    _is_stale_browser_process,
    _on_playwright_thread,
    _should_abort_playwright_request,
    cleanup_stale_browser_processes,
    close_all_browser_contexts,
    fetch_listing_html_browser,
    fetch_listing_html_browser_slots_wall_clock,
    fetch_youdo_detail_html,
    invalidate_browser_slot,
    pick_browser_user_agent,
    reset_playwright_thread_for_tests,
    youdo_browser_backend,
)


def _html_ok() -> str:
    card = '<a data-id="99001" href="https://youdo.com/t99001">Task</a>'
    return "<html><body>" + card + ("x" * 2000) + "</body></html>"


def _detail_html_ok() -> str:
    payload = '{"props":{"pageProps":{"task":{"description":"detail body"}}}}'
    script = f'<script id="__NEXT_DATA__" type="application/json">{payload}</script>'
    return (
        "<html><body>"
        + script
        + '<a href="https://youdo.com/t99001">task</a>'
        + ("y" * 2500)
        + "</body></html>"
    )


class TestExchangeBrowserFetch(unittest.TestCase):
    def tearDown(self) -> None:
        reset_playwright_thread_for_tests()

    @patch("exchange_browser_fetch._youdo_jitter_sleep")
    @patch("exchange_browser_fetch._warm_youdo_home")
    @patch("exchange_browser_fetch._playwright_proxy", return_value={"server": "http://1.2.3.4:8000"})
    def test_youdo_ephemeral_uses_shared_playwright_launch(
        self, _mock_px: MagicMock, _mock_warm: MagicMock, _mock_jitter: MagicMock
    ) -> None:
        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.content.return_value = _html_ok()
        mock_ctx = MagicMock()
        mock_ctx.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_ctx
        mock_pw.chromium.launch.return_value = mock_browser

        with patch("exchange_browser_fetch._get_youdo_playwright", return_value=mock_pw) as get_pw:
            with patch("exchange_browser_fetch.youdo_ephemeral", return_value=True):
                with patch("patchright.sync_api.sync_playwright") as sync_pr:
                    with patch("playwright.sync_api.sync_playwright") as sync_pw:
                        html = ebf._fetch_youdo_ephemeral(
                            "https://youdo.com/tasks-all-opened-all",
                            user_agent="FLRadar/bot",
                            timeout_sec=45.0,
                            proxy_url="http://u:p@1.2.3.4:8000",
                        )

        get_pw.assert_called_once()
        sync_pr.assert_not_called()
        sync_pw.assert_not_called()
        launch_kw = mock_pw.chromium.launch.call_args.kwargs
        self.assertTrue(launch_kw.get("headless"))
        self.assertEqual(launch_kw.get("proxy"), {"server": "http://1.2.3.4:8000"})
        self.assertIn("--disable-blink-features=AutomationControlled", launch_kw.get("args", []))
        ctx_kw = mock_browser.new_context.call_args.kwargs
        self.assertEqual(ctx_kw.get("locale"), "ru-RU")
        self.assertEqual(ctx_kw.get("timezone_id"), "Europe/Moscow")
        self.assertNotIn("flradar", str(ctx_kw.get("user_agent", "")).casefold())
        mock_ctx.route.assert_not_called()
        mock_ctx.add_init_script.assert_called_once()
        mock_browser.close.assert_called_once()
        self.assertGreater(len(html), 1500)

    def test_should_abort_heavy_and_tracker(self) -> None:
        req_img = MagicMock(resource_type="image", url="https://youdo.com/x.png")
        req_doc = MagicMock(resource_type="document", url="https://youdo.com/tasks")
        req_tag = MagicMock(resource_type="script", url="https://mc.yandex.ru/metrika/tag.js")
        req_tracker = MagicMock(resource_type="xhr", url="https://youdo.com/tracker/event")
        self.assertTrue(_should_abort_playwright_request(req_img))
        self.assertFalse(_should_abort_playwright_request(req_doc))
        self.assertTrue(_should_abort_playwright_request(req_tag))
        self.assertTrue(_should_abort_playwright_request(req_tracker))

    @patch("exchange_browser_fetch._jitter_sleep")
    @patch("exchange_browser_fetch._playwright_proxy", return_value=None)
    @patch(
        "exchange_browser_fetch.exchange_primary_proxy_url",
        return_value="http://u:p@5.6.7.8:8000",
    )
    def test_fl_browser_then_youdo_one_playwright_instance(
        self,
        _mock_primary: MagicMock,
        _mock_px: MagicMock,
        _mock_jitter: MagicMock,
    ) -> None:
        mock_pw = MagicMock()
        mock_persistent = MagicMock()
        mock_page_fl = MagicMock()
        mock_page_fl.content.return_value = _html_ok()
        mock_persistent.new_page.return_value = mock_page_fl
        mock_pw.chromium.launch_persistent_context.return_value = mock_persistent

        mock_browser = MagicMock()
        mock_page_yd = MagicMock()
        mock_page_yd.content.return_value = _html_ok()
        mock_ctx = MagicMock()
        mock_ctx.new_page.return_value = mock_page_yd
        mock_browser.new_context.return_value = mock_ctx
        mock_pw.chromium.launch.return_value = mock_browser

        sync_starts: list[str] = []

        def fake_get_playwright():
            if ebf._PLAYWRIGHT is None:
                sync_starts.append("start")
                ebf._PLAYWRIGHT = mock_pw
            return ebf._PLAYWRIGHT

        profile_root = Path(tempfile.mkdtemp())
        with patch.dict("os.environ", {"FL_LISTING_SUBPROCESS": "0"}):
            with patch("exchange_browser_fetch._data_root", return_value=profile_root):
                with patch("exchange_browser_fetch._profile_key", return_value="fl_slot0"):
                    with patch(
                        "exchange_browser_fetch._get_playwright",
                        side_effect=fake_get_playwright,
                    ):
                        with patch("playwright.sync_api.sync_playwright") as sync_pw:
                            fetch_listing_html_browser(
                                "fl",
                                "https://www.fl.ru/projects/",
                                user_agent=_DEFAULT_UA,
                                timeout_sec=30.0,
                            )
                        with patch("exchange_browser_fetch.youdo_ephemeral", return_value=True):
                            with patch("exchange_browser_fetch._warm_youdo_home"):
                                with patch("exchange_browser_fetch._youdo_jitter_sleep"):
                                    with patch(
                                        "exchange_browser_fetch._get_youdo_playwright",
                                        return_value=mock_pw,
                                    ):
                                        _fetch_youdo_ephemeral(
                                            "https://youdo.com/tasks-all-opened-all",
                                            user_agent="FLRadar/bot",
                                            timeout_sec=45.0,
                                            proxy_url="http://u:p@1.2.3.4:8000",
                                        )
                        sync_pw.assert_not_called()
                        self.assertEqual(sync_starts, ["start"])
                        mock_pw.chromium.launch_persistent_context.assert_called_once()
                        mock_pw.chromium.launch.assert_called_once()

    def test_youdo_browser_backend_default_patchright(self) -> None:
        with patch.dict("os.environ", {}, clear=False):
            os.environ.pop("YOUDO_BROWSER", None)
            self.assertEqual(youdo_browser_backend(), "patchright")

    def test_youdo_get_playwright_uses_patchright_module(self) -> None:
        mock_inst = MagicMock()
        mock_sync = MagicMock(return_value=MagicMock(start=MagicMock(return_value=mock_inst)))
        ebf._YOUDO_PW = None
        with patch.dict("os.environ", {"YOUDO_BROWSER": "patchright"}):
            with patch("patchright.sync_api.sync_playwright", mock_sync):
                got = _get_youdo_playwright()
        self.assertIs(got, mock_inst)
        mock_sync.assert_called_once()

    def test_youdo_browser_backend_camoufox(self) -> None:
        with patch.dict("os.environ", {"YOUDO_BROWSER": "camoufox"}):
            self.assertEqual(youdo_browser_backend(), "camoufox")

    def test_youdo_get_playwright_uses_playwright_for_camoufox(self) -> None:
        mock_inst = MagicMock()
        mock_sync = MagicMock(return_value=MagicMock(start=MagicMock(return_value=mock_inst)))
        ebf._YOUDO_PW = None
        with patch.dict("os.environ", {"YOUDO_BROWSER": "camoufox"}):
            with patch("playwright.sync_api.sync_playwright", mock_sync):
                got = _get_youdo_playwright()
        self.assertIs(got, mock_inst)
        mock_sync.assert_called_once()

    def test_pick_browser_user_agent_rejects_flradar(self) -> None:
        ua = pick_browser_user_agent("Mozilla/5.0 (compatible; FLRadar/1.0)")
        self.assertNotIn("flradar", ua.casefold())
        self.assertTrue("Chrome" in ua or "Firefox" in ua or "Safari" in ua)

    def test_pick_browser_user_agent_keeps_explicit(self) -> None:
        custom = "Mozilla/5.0 CustomBrowser/99.0"
        self.assertEqual(pick_browser_user_agent(custom), custom)

    def test_is_stale_browser_process(self) -> None:
        self.assertTrue(
            _is_stale_browser_process(
                "chrome-headless",
                "/ms-playwright/chromium-1234/chrome-linux/chrome --headless",
            )
        )
        self.assertFalse(_is_stale_browser_process("python3", "src/main.py --profile site"))

    @patch("exchange_browser_fetch._browser_process_tree", return_value={99999})
    def test_cleanup_stale_browser_processes(self, _mock_tree: MagicMock) -> None:
        stale = MagicMock()
        stale.info = {
            "pid": 4242,
            "username": "rawlead",
            "name": "chrome-headless",
            "cmdline": ["/ms-playwright/chromium/chrome", "--headless"],
        }

        keeper = MagicMock()
        keeper.info = {
            "pid": 1111,
            "username": "rawlead",
            "name": "python3",
            "cmdline": ["python3", "src/main.py"],
        }

        with patch("psutil.process_iter", return_value=[stale, keeper]):
            with patch("getpass.getuser", return_value="rawlead"):
                killed = cleanup_stale_browser_processes()

        self.assertEqual(killed, 1)
        stale.kill.assert_called_once()
        keeper.kill.assert_not_called()

    @patch("exchange_browser_fetch._jitter_sleep")
    @patch("exchange_browser_fetch._playwright_proxy", return_value=None)
    @patch(
        "exchange_browser_fetch.exchange_primary_proxy_url",
        return_value="http://u:p@5.6.7.8:8000",
    )
    def test_fetch_closes_context_after_page(
        self,
        _mock_primary: MagicMock,
        _mock_px: MagicMock,
        _mock_jitter: MagicMock,
    ) -> None:
        mock_pw = MagicMock()
        mock_persistent = MagicMock()
        mock_page = MagicMock()
        mock_page.content.return_value = _html_ok()
        mock_persistent.new_page.return_value = mock_page
        mock_pw.chromium.launch_persistent_context.return_value = mock_persistent

        profile_root = Path(tempfile.mkdtemp())
        with patch.dict("os.environ", {"FL_LISTING_SUBPROCESS": "0"}):
            with patch("exchange_browser_fetch._data_root", return_value=profile_root):
                with patch("exchange_browser_fetch._profile_key", return_value="fl_slot0"):
                    with patch("exchange_browser_fetch._get_playwright", return_value=mock_pw):
                        fetch_listing_html_browser(
                            "fl",
                            "https://www.fl.ru/projects/",
                            user_agent=_DEFAULT_UA,
                            timeout_sec=30.0,
                        )
        mock_persistent.close.assert_called_once()
        self.assertEqual(ebf._CONTEXTS, {})

    def test_invalidate_browser_slot_wipes_profile(self) -> None:
        profile_root = Path(tempfile.mkdtemp())
        key_name = "fl_1_2_3_4_8000"
        key_dir = profile_root / key_name
        key_dir.mkdir(parents=True)
        (key_dir / "cookies.sqlite").write_text("x", encoding="utf-8")
        with patch("exchange_browser_fetch._data_root", return_value=profile_root):
            with patch("exchange_browser_fetch._profile_key", return_value=key_name):
                invalidate_browser_slot(
                    "fl",
                    "http://u:p@1.2.3.4:8000",
                    wipe_disk=True,
                )
        self.assertFalse(key_dir.exists())

    @patch("exchange_browser_fetch._youdo_jitter_sleep")
    @patch("exchange_browser_fetch._maybe_warm_youdo_home")
    @patch("exchange_browser_fetch._playwright_proxy", return_value=None)
    @patch(
        "exchange_browser_fetch.exchange_primary_proxy_url",
        return_value="http://u:p@1.2.3.4:8000",
    )
    @patch("exchange_browser_fetch.fetch_youdo_html_browser")
    def test_slots_wall_clock_from_foreign_thread(
        self,
        mock_fetch: MagicMock,
        _mock_primary: MagicMock,
        _mock_px: MagicMock,
        _mock_warm: MagicMock,
        _mock_jitter: MagicMock,
    ) -> None:
        mock_fetch.return_value = _html_ok()
        pw_threads: list[bool] = []

        def run_from_ephemeral() -> str:
            with ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(
                    fetch_listing_html_browser_slots_wall_clock,
                    "youdo",
                    "https://youdo.com/tasks-all-opened-all",
                    user_agent=_DEFAULT_UA,
                    timeout_sec=30.0,
                    wall_clock_sec=60.0,
                ).result()

        with patch("exchange_browser_fetch._get_playwright") as get_pw:
            get_pw.side_effect = lambda: (
                pw_threads.append(_on_playwright_thread()) or MagicMock()
            )
            html = run_from_ephemeral()

        self.assertEqual(html, mock_fetch.return_value)
        self.assertTrue(all(pw_threads))
        mock_fetch.assert_called_once()

    @patch("exchange_browser_fetch._youdo_jitter_sleep")
    @patch("exchange_browser_fetch._maybe_warm_youdo_home_async")
    @patch("exchange_browser_fetch._playwright_proxy", return_value=None)
    @patch(
        "exchange_browser_fetch.exchange_primary_proxy_url",
        return_value="http://u:p@1.2.3.4:8000",
    )
    @patch("exchange_browser_fetch.exchange_alive_proxy_urls")
    @patch("exchange_browser_fetch.subprocess.run")
    def test_camoufox_slots_wall_clock_ephemeral_on_pw_thread(
        self,
        mock_run: MagicMock,
        mock_alive: MagicMock,
        _mock_primary: MagicMock,
        _mock_px: MagicMock,
        _mock_warm: MagicMock,
        _mock_jitter: MagicMock,
    ) -> None:
        """O190 t0i: camoufox listing via subprocess worker on PW thread."""
        mock_alive.return_value = ["http://u:p@1.2.3.4:8000"]
        pw_threads: list[bool] = []
        worker_calls: list[list[str]] = []

        def fake_subprocess(cmd, **_kwargs):
            worker_calls.append(cmd)
            pw_threads.append(_on_playwright_thread())
            proc = MagicMock()
            proc.returncode = 0
            proc.stdout = json.dumps({"html": _html_ok()})
            proc.stderr = ""
            return proc

        mock_run.side_effect = fake_subprocess

        def run_from_worker() -> str:
            with ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(
                    fetch_listing_html_browser_slots_wall_clock,
                    "youdo",
                    "https://youdo.com/tasks-all-opened-all",
                    user_agent=_DEFAULT_UA,
                    timeout_sec=30.0,
                    wall_clock_sec=60.0,
                ).result()

        with patch.dict("os.environ", {"YOUDO_BROWSER": "camoufox"}):
            html = run_from_worker()

        self.assertEqual(html, _html_ok())
        self.assertTrue(pw_threads)
        self.assertTrue(all(pw_threads))
        self.assertTrue(worker_calls)
        self.assertIn("youdo_fetch_worker.py", worker_calls[0][1])

    @patch("exchange_browser_fetch._jitter_sleep")
    @patch("exchange_browser_fetch._playwright_proxy", return_value=None)
    @patch(
        "exchange_browser_fetch.exchange_primary_proxy_url",
        return_value="http://u:p@1.2.3.4:8000",
    )
    @patch("exchange_browser_fetch.subprocess.run")
    def test_fl_listing_subprocess_on_pw_thread(
        self,
        mock_run: MagicMock,
        _mock_primary: MagicMock,
        _mock_px: MagicMock,
        _mock_jitter: MagicMock,
    ) -> None:
        """O193: FL listing via fl_fetch_worker subprocess on PW thread."""
        pw_threads: list[bool] = []
        worker_calls: list[list[str]] = []

        def fake_subprocess(cmd, **_kwargs):
            worker_calls.append(cmd)
            pw_threads.append(_on_playwright_thread())
            proc = MagicMock()
            proc.returncode = 0
            proc.stdout = json.dumps(
                {"ok": True, "html": _html_ok(), "html_len": len(_html_ok())}
            )
            proc.stderr = ""
            return proc

        mock_run.side_effect = fake_subprocess

        def run_fl() -> str:
            with ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(
                    fetch_listing_html_browser,
                    "fl",
                    "https://www.fl.ru/projects/",
                    user_agent=_DEFAULT_UA,
                    timeout_sec=30.0,
                ).result()

        with patch.dict("os.environ", {"FL_LISTING_SUBPROCESS": "1"}):
            html = run_fl()

        self.assertEqual(html, _html_ok())
        self.assertTrue(all(pw_threads))
        self.assertTrue(worker_calls)
        self.assertIn("fl_fetch_worker.py", worker_calls[0][1])

    @patch("exchange_browser_fetch._youdo_jitter_sleep")
    @patch("exchange_browser_fetch._playwright_proxy", return_value=None)
    @patch(
        "exchange_browser_fetch.exchange_primary_proxy_url",
        return_value="http://u:p@1.2.3.4:8000",
    )
    @patch("exchange_browser_fetch.subprocess.run")
    def test_camoufox_detail_subprocess_on_pw_thread(
        self,
        mock_run: MagicMock,
        _mock_primary: MagicMock,
        _mock_px: MagicMock,
        _mock_jitter: MagicMock,
    ) -> None:
        """O194: YouDo detail via youdo_fetch_worker subprocess (no sync PW in radar)."""
        pw_threads: list[bool] = []
        worker_calls: list[list[str]] = []

        def fake_subprocess(cmd, **_kwargs):
            worker_calls.append(cmd)
            pw_threads.append(_on_playwright_thread())
            proc = MagicMock()
            proc.returncode = 0
            proc.stdout = json.dumps({"html": _detail_html_ok()})
            proc.stderr = ""
            return proc

        mock_run.side_effect = fake_subprocess

        def run_detail() -> str:
            with ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(
                    fetch_youdo_detail_html,
                    "https://youdo.com/t99001",
                    user_agent=_DEFAULT_UA,
                    timeout_sec=30.0,
                ).result()

        with patch.dict("os.environ", {"YOUDO_BROWSER": "camoufox", "YOUDO_EPHEMERAL": "0"}):
            html = run_detail()

        self.assertIn("__NEXT_DATA__", html)
        self.assertTrue(all(pw_threads))
        self.assertTrue(worker_calls)
        cmd = worker_calls[0]
        self.assertIn("youdo_fetch_worker", str(cmd))
        self.assertIn("--stage", cmd)
        self.assertIn("detail", cmd)

    @patch("exchange_browser_fetch._youdo_jitter_sleep")
    @patch("exchange_browser_fetch._playwright_proxy", return_value=None)
    def test_ephemeral_from_foreign_thread(
        self,
        _mock_px: MagicMock,
        _mock_jitter: MagicMock,
    ) -> None:
        mock_pw = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.content.return_value = _html_ok()
        mock_ctx = MagicMock()
        mock_ctx.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_ctx
        mock_pw.chromium.launch.return_value = mock_browser
        pw_threads: list[bool] = []

        def get_pw_side_effect() -> MagicMock:
            pw_threads.append(_on_playwright_thread())
            return mock_pw

        with patch(
            "exchange_browser_fetch._get_youdo_playwright",
            side_effect=get_pw_side_effect,
        ):
            with ThreadPoolExecutor(max_workers=1) as pool:
                html = pool.submit(
                    _fetch_youdo_ephemeral,
                    "https://youdo.com/tasks-all-opened-all",
                    user_agent=_DEFAULT_UA,
                    timeout_sec=45.0,
                    proxy_url="http://u:p@1.2.3.4:8000",
                ).result()

        self.assertEqual(html, _html_ok())
        self.assertTrue(pw_threads)
        self.assertTrue(all(pw_threads))


    def test_playwright_sync_clears_loop_in_worker(self) -> None:
        caller_tid = threading.get_ident()
        clear_tids: list[int] = []
        real_clear = _clear_stale_asyncio_loop

        def track_clear() -> None:
            clear_tids.append(threading.get_ident())
            real_clear()

        def noop() -> str:
            return "ok"

        with patch("exchange_browser_fetch._clear_stale_asyncio_loop", side_effect=track_clear):
            with patch("exchange_browser_fetch._on_playwright_thread", return_value=False):
                result = ebf._playwright_sync(noop)

        self.assertEqual(result, "ok")
        self.assertGreaterEqual(len(clear_tids), 2)
        self.assertTrue(any(tid != caller_tid for tid in clear_tids))


if __name__ == "__main__":
    unittest.main()
