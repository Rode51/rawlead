"""O121-w3-acc2: acc2 join-bootstrap при legacy chat_ids и 0 listen после v2 filter."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

import tg_monitor as mon  # noqa: E402


def test_needs_join_bootstrap_empty_file_with_pending():
    assert mon._needs_join_bootstrap(
        pending=6,
        join_in_main=True,
        file_chat_ids=[],
    )


def test_needs_join_bootstrap_legacy_zero_listen():
    legacy = [1111111111, 2222222222]
    assert mon._needs_join_bootstrap(
        pending=6,
        join_in_main=True,
        file_chat_ids=legacy,
        listen_ids=[],
    )


def test_needs_join_bootstrap_no_pending():
    assert not mon._needs_join_bootstrap(
        pending=0,
        join_in_main=True,
        file_chat_ids=[],
    )


def test_needs_join_bootstrap_join_disabled():
    assert not mon._needs_join_bootstrap(
        pending=6,
        join_in_main=False,
        file_chat_ids=[],
    )


def test_needs_join_bootstrap_has_listen_ids():
    assert not mon._needs_join_bootstrap(
        pending=6,
        join_in_main=True,
        file_chat_ids=[100, 200],
        listen_ids=[100],
    )


def test_run_monitor_schedules_join_loop_acc2_legacy_filter(tmp_path):
    """acc2: legacy ids в файле, v2 pending, filter → 0 listen → _join_loop в tasks."""

    async def _run() -> list[str]:
        log_path = tmp_path / "radar_site.log"
        legacy_ids = [1111111111, 2222222222, 3333333333]
        acfg = SimpleNamespace(account="acc2", chat_ids=legacy_ids)
        tg_cfg = SimpleNamespace(accounts=[acfg], radar_log_path=log_path)

        mock_client = MagicMock()
        mock_client.run_until_disconnected = AsyncMock()
        mock_client.disconnect = AsyncMock()
        mock_client.get_me = AsyncMock()
        mock_client.on = MagicMock(return_value=lambda fn: fn)

        join_accounts: list[str] = []

        async def fake_join_loop(account, client, chat_ids, log_path_arg, storage):
            join_accounts.append(account.strip().lower())

        async def fast_gather(*tasks):
            await asyncio.sleep(0)
            for task in tasks:
                if not task.done():
                    task.cancel()
            return []

        with (
            patch.object(mon, "load_config", return_value=MagicMock()),
            patch.object(mon, "load_tg_monitor_config", return_value=tg_cfg),
            patch.object(mon, "storage_from_config", return_value=MagicMock()),
            patch.object(mon, "pg_storage_from_config", return_value=MagicMock()),
            patch.object(mon, "default_listing_filter", return_value=MagicMock()),
            patch.object(mon, "load_chat_registry_from_queue", return_value={}),
            patch.object(
                mon,
                "load_tg_join_config",
                return_value=SimpleNamespace(
                    daemon_interval_sec=0.01,
                    queue_csv=tmp_path / "queue.csv",
                ),
            ),
            patch.object(mon, "_pending_join_by_account", return_value={"acc2": 6}),
            patch.object(mon, "tg_join_in_tg_main", return_value=True),
            patch.object(mon, "connect_client", AsyncMock(return_value=mock_client)),
            patch.object(mon, "ensure_bot_started", AsyncMock()),
            patch.object(mon, "filter_listen_chat_ids", return_value=[]),
            patch.object(mon, "is_night_window", return_value=False),
            patch.object(mon, "_join_loop", fake_join_loop),
            patch.object(mon, "record_tg_monitor_start"),
            patch.object(mon, "record_tg_acc_ready"),
            patch.object(mon, "record_tg_skip"),
            patch.object(asyncio, "gather", fast_gather),
        ):
            await mon.run_monitor()
        return join_accounts

    assert asyncio.run(_run()) == ["acc2"]
