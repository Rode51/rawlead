"""O266: YouDo sticky browser session — warm reload vs cold goto."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from exchange_browser_fetch import (  # noqa: E402
    _fetch_youdo_sticky_listing,
    _youdo_sticky_max_age_sec,
    _youdo_sticky_session_enabled,
    reset_youdo_sticky_for_tests,
    youdo_browser_teardown,
    youdo_sticky_session_warm,
)
from html_fetch import HtmlFetchError  # noqa: E402

_LISTING = "https://youdo.com/tasks-all-opened-all"
_PROXY = "http://185.147.128.237:8000:u1:p1"
_VALID_HTML = (
    "<html><body>"
    + "x" * 9000
    + '<a data-id="1" href="/t/1">task</a></body></html>'
)


class _FakeStickyProc:
    def __init__(self) -> None:
        self.returncode: int | None = None
        self.stdin_lines: list[str] = []
        self.responses: list[dict] = []
        self._resp_idx = 0
        self.killed = False

    def poll(self) -> int | None:
        return self.returncode

    @property
    def stdin(self) -> MagicMock:
        mock = MagicMock()

        def _write(data: str) -> None:
            self.stdin_lines.append(data.strip())

        mock.write = _write
        mock.flush = MagicMock()
        return mock

    @property
    def stdout(self) -> MagicMock:
        mock = MagicMock()

        def _readline() -> str:
            if self._resp_idx >= len(self.responses):
                return ""
            line = json.dumps(self.responses[self._resp_idx], ensure_ascii=False)
            self._resp_idx += 1
            return line + "\n"

        mock.readline = _readline
        return mock

    @property
    def stderr(self) -> MagicMock:
        mock = MagicMock()
        mock.read = MagicMock(return_value="")
        return mock

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9

    def wait(self, timeout: float | None = None) -> int:
        self.returncode = 0
        return 0


@pytest.fixture(autouse=True)
def _reset_sticky() -> None:
    reset_youdo_sticky_for_tests()


def test_sticky_env_gate_default_on() -> None:
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("YOUDO_STICKY_SESSION", None)
        assert _youdo_sticky_session_enabled() is True


def test_sticky_env_gate_off() -> None:
    with patch.dict(os.environ, {"YOUDO_STICKY_SESSION": "0"}, clear=False):
        assert _youdo_sticky_session_enabled() is False


@patch("exchange_browser_fetch._youdo_is_camoufox", return_value=True)
@patch("exchange_browser_fetch._fetch_youdo_ephemeral")
def test_sticky_disabled_falls_back_to_ephemeral(
    mock_ephemeral: MagicMock,
    _mock_camoufox: MagicMock,
) -> None:
    mock_ephemeral.return_value = _VALID_HTML
    with patch.dict(os.environ, {"YOUDO_STICKY_SESSION": "0"}, clear=False):
        html = _fetch_youdo_sticky_listing(
            _LISTING,
            user_agent="Mozilla/5.0",
            timeout_sec=60.0,
            proxy_url=_PROXY,
        )
    assert html == _VALID_HTML
    mock_ephemeral.assert_called_once()


@patch("exchange_browser_fetch._on_playwright_thread", return_value=True)
@patch("exchange_browser_fetch._youdo_is_camoufox", return_value=True)
@patch("exchange_browser_fetch._youdo_sticky_spawn_worker")
def test_cold_then_warm_uses_goto_then_reload(
    mock_spawn: MagicMock,
    _mock_cf: MagicMock,
    _mock_pw: MagicMock,
) -> None:
    proc = _FakeStickyProc()
    proc.responses = [
        {"html": _VALID_HTML, "stage": "sticky_goto", "goto_ms": 12000},
        {"html": _VALID_HTML, "stage": "sticky_reload", "goto_ms": 800},
    ]
    mock_spawn.return_value = proc

    with patch.dict(os.environ, {"YOUDO_STICKY_SESSION": "1"}, clear=False):
        html1 = _fetch_youdo_sticky_listing(
            _LISTING,
            user_agent="Mozilla/5.0",
            timeout_sec=60.0,
            proxy_url=_PROXY,
        )
        assert "data-id" in html1
        assert youdo_sticky_session_warm() is True

        html2 = _fetch_youdo_sticky_listing(
            _LISTING,
            user_agent="Mozilla/5.0",
            timeout_sec=60.0,
            proxy_url=_PROXY,
        )
        assert "data-id" in html2

    cmds = [json.loads(line) for line in proc.stdin_lines]
    assert cmds[0]["cmd"] == "goto"
    assert cmds[1]["cmd"] == "reload"
    assert mock_spawn.call_count == 1


@patch("exchange_browser_fetch._on_playwright_thread", return_value=True)
@patch("exchange_browser_fetch._youdo_is_camoufox", return_value=True)
@patch("exchange_browser_fetch._youdo_sticky_spawn_worker")
def test_warm_reload_antibot_teardown_and_cold_retry(
    mock_spawn: MagicMock,
    _mock_cf: MagicMock,
    _mock_pw: MagicMock,
) -> None:
    first = _FakeStickyProc()
    first.responses = [
        {"html": _VALID_HTML, "stage": "sticky_goto", "goto_ms": 10000},
        {"error": "ServicePipe antibot challenge (youdo).", "stage": "sticky_reload"},
    ]
    second = _FakeStickyProc()
    second.responses = [
        {"html": _VALID_HTML, "stage": "sticky_goto", "goto_ms": 11000},
    ]
    mock_spawn.side_effect = [first, second]

    with patch.dict(os.environ, {"YOUDO_STICKY_SESSION": "1"}, clear=False):
        _fetch_youdo_sticky_listing(
            _LISTING,
            user_agent="Mozilla/5.0",
            timeout_sec=60.0,
            proxy_url=_PROXY,
        )
        html = _fetch_youdo_sticky_listing(
            _LISTING,
            user_agent="Mozilla/5.0",
            timeout_sec=60.0,
            proxy_url=_PROXY,
        )
    assert "data-id" in html
    all_cmds = []
    for p in (first, second):
        all_cmds.extend(json.loads(line)["cmd"] for line in p.stdin_lines)
    assert "reload" in all_cmds
    assert all_cmds.count("goto") >= 2


@patch("exchange_browser_fetch._on_playwright_thread", return_value=True)
@patch("exchange_browser_fetch._youdo_is_camoufox", return_value=True)
@patch("exchange_browser_fetch._youdo_sticky_spawn_worker")
def test_proxy_change_spawns_new_worker(
    mock_spawn: MagicMock,
    _mock_cf: MagicMock,
    _mock_pw: MagicMock,
) -> None:
    proc1 = _FakeStickyProc()
    proc1.responses = [
        {"html": _VALID_HTML, "stage": "sticky_goto", "goto_ms": 9000},
    ]
    proc2 = _FakeStickyProc()
    proc2.responses = [
        {"html": _VALID_HTML, "stage": "sticky_goto", "goto_ms": 9000},
    ]
    mock_spawn.side_effect = [proc1, proc2]
    other_proxy = "http://185.147.130.67:8000:u2:p2"

    with patch.dict(os.environ, {"YOUDO_STICKY_SESSION": "1"}, clear=False):
        _fetch_youdo_sticky_listing(
            _LISTING,
            user_agent="Mozilla/5.0",
            timeout_sec=60.0,
            proxy_url=_PROXY,
        )
        _fetch_youdo_sticky_listing(
            _LISTING,
            user_agent="Mozilla/5.0",
            timeout_sec=60.0,
            proxy_url=other_proxy,
        )

    assert mock_spawn.call_count == 2
    assert proc1.killed or any("teardown" in line for line in proc1.stdin_lines)


@patch("exchange_browser_fetch.cleanup_stale_youdo_browser_processes", return_value=0)
@patch("exchange_browser_fetch.close_all_browser_contexts")
@patch("exchange_browser_fetch._abort_playwright_worker")
@patch("exchange_browser_fetch._on_playwright_thread", return_value=True)
@patch("exchange_browser_fetch._youdo_is_camoufox", return_value=True)
@patch("exchange_browser_fetch._youdo_sticky_spawn_worker")
def test_hard_reset_teardown_kills_sticky(
    mock_spawn: MagicMock,
    _mock_cf: MagicMock,
    _mock_pw: MagicMock,
    _mock_abort: MagicMock,
    _mock_close: MagicMock,
    _mock_cleanup: MagicMock,
) -> None:
    proc = _FakeStickyProc()
    proc.responses = [{"html": _VALID_HTML, "stage": "sticky_goto", "goto_ms": 5000}]
    mock_spawn.return_value = proc

    with patch.dict(os.environ, {"YOUDO_STICKY_SESSION": "1"}, clear=False):
        _fetch_youdo_sticky_listing(
            _LISTING,
            user_agent="Mozilla/5.0",
            timeout_sec=60.0,
            proxy_url=_PROXY,
        )
        assert youdo_sticky_session_warm() is True
        youdo_browser_teardown()
        assert youdo_sticky_session_warm() is False

    assert proc.killed or any("teardown" in line for line in proc.stdin_lines)


@patch("exchange_browser_fetch._on_playwright_thread", return_value=True)
@patch("exchange_browser_fetch._youdo_is_camoufox", return_value=True)
@patch("exchange_browser_fetch._youdo_sticky_spawn_worker")
def test_max_age_exceeded_cold_goto(
    mock_spawn: MagicMock,
    _mock_cf: MagicMock,
    _mock_pw: MagicMock,
) -> None:
    proc1 = _FakeStickyProc()
    proc1.responses = [
        {"html": _VALID_HTML, "stage": "sticky_goto", "goto_ms": 5000},
    ]
    proc2 = _FakeStickyProc()
    proc2.responses = [
        {"html": _VALID_HTML, "stage": "sticky_goto", "goto_ms": 6000},
    ]
    mock_spawn.side_effect = [proc1, proc2]

    with patch.dict(
        os.environ,
        {"YOUDO_STICKY_SESSION": "1", "YOUDO_STICKY_MAX_AGE_SEC": "60"},
        clear=False,
    ):
        _fetch_youdo_sticky_listing(
            _LISTING,
            user_agent="Mozilla/5.0",
            timeout_sec=60.0,
            proxy_url=_PROXY,
        )
        import exchange_browser_fetch as ebf

        with ebf._YOUDO_STICKY_LOCK:
            ebf._YOUDO_STICKY_LAST_VALID = time.time() - _youdo_sticky_max_age_sec() - 1
        _fetch_youdo_sticky_listing(
            _LISTING,
            user_agent="Mozilla/5.0",
            timeout_sec=60.0,
            proxy_url=_PROXY,
        )

    cmds = [json.loads(line)["cmd"] for line in proc1.stdin_lines]
    cmds += [json.loads(line)["cmd"] for line in proc2.stdin_lines]
    assert cmds.count("goto") == 2
    assert "reload" not in cmds


@patch("youdo_parser.youdo_hard_reset_on_fail_enabled", return_value=True)
@patch("youdo_parser._youdo_hard_reset_fail_threshold", return_value=1)
@patch("youdo_parser._get_youdo_fail_streak", return_value=0)
@patch("youdo_parser._bump_youdo_fail_streak", return_value=1)
@patch("youdo_parser.youdo_hard_reset")
def test_on_fetch_fail_skips_hard_reset_when_sticky_warm_streak1(
    mock_reset: MagicMock,
    _mock_bump: MagicMock,
    _mock_get: MagicMock,
    _mock_thr: MagicMock,
    _mock_enabled: MagicMock,
) -> None:
    from config import Config
    from youdo_parser import _on_youdo_fetch_fail

    cfg = MagicMock(spec=Config)
    storage = MagicMock()
    with patch("exchange_browser_fetch.youdo_sticky_session_warm", return_value=True):
        with patch("youdo_parser.set_youdo_cooldown") as mock_cd:
            _on_youdo_fetch_fail(cfg, storage)
    mock_reset.assert_not_called()
    mock_cd.assert_called_once()
