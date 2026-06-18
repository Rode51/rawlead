"""O206-t3b/t3c: per-acc handler heartbeat + watchdog helpers."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from public_feed import TG_TEST_GROUP_RAW_ID, tg_test_group_chat_keys  # noqa: E402
import tg_monitor as mon  # noqa: E402


def test_test_group_peer_ok_matches_supergroup_peer() -> None:
    peers = {-1005177575757}
    assert mon._test_group_peer_ok(peers)


def test_test_group_peer_ok_false_for_unrelated() -> None:
    assert not mon._test_group_peer_ok({-1001234567890})


def test_deaf_seconds_uses_started_at_when_no_events() -> None:
    now = 1000.0
    sess = mon._MonitorSession("acc1", MagicMock(), {1}, started_at=900.0)
    assert mon._deaf_seconds(sess, now=now) == pytest.approx(100.0)


def test_deaf_seconds_uses_last_event_when_present() -> None:
    now = 1000.0
    sess = mon._MonitorSession(
        "acc1",
        MagicMock(),
        {1},
        started_at=100.0,
        last_event_at=950.0,
    )
    assert mon._deaf_seconds(sess, now=now) == pytest.approx(50.0)


def test_in_test_group_dialogs_false_when_empty() -> None:
    async def _run() -> None:
        client = MagicMock()

        async def _dialogs():
            for _item in []:
                yield _item

        client.iter_dialogs = MagicMock(return_value=_dialogs())
        assert not await mon._in_test_group_dialogs(client)

    import asyncio

    asyncio.run(_run())


def test_log_handler_registered_writes_handler_ok(tmp_path: Path) -> None:
    log_path = tmp_path / "radar_site.log"
    keys = tg_test_group_chat_keys()
    peer = next(iter(keys))
    sess = mon._MonitorSession(
        "acc1",
        MagicMock(),
        {peer},
        file_listen_ids=[TG_TEST_GROUP_RAW_ID],
    )
    mon._log_handler_registered(sess, log_path)
    assert sess.handler_registered
    line = log_path.read_text(encoding="utf-8")
    assert "тг:монитор:acc1:handler_ok" in line
    assert "test_group_peer=1" in line
    assert "test_group_file=1" in line


def test_client_connected_sync_is_connected() -> None:
    client = MagicMock()
    client.is_connected = MagicMock(return_value=True)
    assert mon._client_connected(client)
    client.is_connected.assert_called_once_with()


def test_client_connected_false_on_error() -> None:
    client = MagicMock()
    client.is_connected = MagicMock(side_effect=RuntimeError("boom"))
    assert not mon._client_connected(client)


def test_reconnect_session_wakes_only_target(tmp_path: Path) -> None:
    async def _run() -> None:
        log_path = tmp_path / "radar_site.log"
        storage = MagicMock()
        c1 = MagicMock()
        c1.is_connected = MagicMock(return_value=False)
        c1.connect = AsyncMock()
        c1.catch_up = AsyncMock()
        c1.get_me = AsyncMock(return_value=SimpleNamespace(id=1))
        c1.disconnect = AsyncMock()
        c2 = MagicMock()
        c2.disconnect = AsyncMock()
        s1 = mon._MonitorSession("acc1", c1, {1})
        s2 = mon._MonitorSession("acc2", c2, {2})
        await mon._reconnect_session(
            s1,
            log_path,
            storage,
            reason="disconnect",
        )
        c1.connect.assert_awaited_once()
        c2.disconnect.assert_not_called()
        text = log_path.read_text(encoding="utf-8")
        assert "тг:монитор:acc1:reconnect" in text
        assert "тг:монитор:acc1:sync ok" in text

    import asyncio

    asyncio.run(_run())


def test_watchdog_loop_continues_after_reconnect(tmp_path: Path) -> None:
    async def _run() -> None:
        log_path = tmp_path / "radar_site.log"
        storage = MagicMock()
        client = MagicMock()
        client.is_connected = MagicMock(return_value=False)
        client.connect = AsyncMock()
        client.catch_up = AsyncMock()
        client.get_me = AsyncMock(return_value=SimpleNamespace(id=1))
        sess = mon._MonitorSession("acc1", client, {1})
        sleeps: list[float] = []

        async def _fake_sleep(sec: float) -> None:
            sleeps.append(sec)
            if len(sleeps) >= 3:
                raise asyncio.CancelledError

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(mon.asyncio, "sleep", _fake_sleep)
            mp.setattr(mon, "_ACC_PULSE_SEC", 0.01)
            task = asyncio.create_task(
                mon._acc_watchdog_loop([sess], log_path, storage)
            )
            with pytest.raises(asyncio.CancelledError):
                await task

        text = log_path.read_text(encoding="utf-8")
        assert text.count("тг:пульс:acc1") >= 2
        assert "тг:монитор:acc1:reconnect" in text

    import asyncio

    asyncio.run(_run())


def test_wake_client_updates_calls_catch_up(tmp_path: Path) -> None:
    async def _run() -> None:
        log_path = tmp_path / "radar_site.log"
        storage = MagicMock()
        client = MagicMock()
        client.is_connected = MagicMock(return_value=True)
        client.catch_up = AsyncMock()
        client.get_me = AsyncMock(return_value=SimpleNamespace(id=1))
        sess = mon._MonitorSession("acc1", client, {1})
        await mon._wake_client_updates(sess, log_path, storage)
        client.catch_up.assert_awaited_once()
        assert "тг:монитор:acc1:sync ok" in log_path.read_text(encoding="utf-8")

    import asyncio

    asyncio.run(_run())
