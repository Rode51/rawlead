"""O64–O67 unit tests."""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ai_analyze import (
    ai_last_error,
    draft_fail_per_hour,
    draft_stats_24h,
    note_ai_error,
    note_draft_request,
)
from delist_checker import _check_gone
from fl_parser import check_project_page_gone
from listing import SOURCE_FL
from radar_status import (
    _format_ai_health_line,
    _format_l1_source_counts,
    _query_l1_backlog_by_source,
)


class _Cfg:
    radar_profile: str = "site"
    http_user_agent: str = "test"


def test_format_l1_source_counts() -> None:
    line = _format_l1_source_counts({"fl": 3, "kwork": 1, "tg": 0})
    assert line == "fl:3 kwork:1 tg:0"


def test_format_ai_health_line() -> None:
    line = _format_ai_health_line("site:сводка │ 10мин │ l1 2 │ l2 0 │ is_visible 1")
    assert "ИИ: L1 ok" in line
    assert "draft fail" in line


def test_draft_fail_per_hour() -> None:
    while draft_stats_24h()["draft_ok"] or draft_stats_24h()["draft_fail"]:
        note_draft_request(False)
    note_draft_request(False)
    note_draft_request(False)
    assert draft_fail_per_hour() == 2


def test_ai_last_error() -> None:
    note_ai_error("OpenRouter 429")
    assert ai_last_error() == "OpenRouter 429"


def test_fl_gone_markers() -> None:
    from unittest.mock import MagicMock, patch

    cfg = _Cfg()
    resp = MagicMock()
    resp.status_code = 200
    resp.encoding = "utf-8"
    resp.content = "<html>проект закрыт</html>".encode("utf-8")
    with patch("fl_parser.requests.get", return_value=resp):
        assert check_project_page_gone("https://fl.ru/projects/1/", cfg) is True


def test_check_gone_fl_source() -> None:
    from unittest.mock import patch

    cfg = _Cfg()
    with patch("delist_checker.fl_page_gone", return_value=True) as mock:
        assert _check_gone(SOURCE_FL, "https://fl.ru/projects/1/", cfg) is True
        mock.assert_called_once()


def test_legacy_poll_interval_config() -> None:
    from config import Config

    cfg = Config(
        fl_projects_url="https://fl.ru/",
        kwork_projects_url="",
        poll_interval_minutes=10,
        legacy_neon_poll_sec=60,
        telegram_bot_token="x",
        telegram_chat_id="1",
        sqlite_path=Path("data/projects.db"),
        radar_log_path=Path("data/radar.log"),
        http_user_agent="test",
        tg_proxy_url="http://127.0.0.1:8080",
        ai_enabled=False,
        ai_api_key="",
        ai_api_key_l1_b="",
        ai_model="m",
        ai_model_summary="m",
        ai_model_premium="m",
        ai_model_shared_draft="m",
        ai_model_judge="m",
        ai_provider="openrouter",
        min_budget_rub=0,
        ai_notify_skip=False,
        filter_wide=False,
        database_url="",
        radar_profile="legacy",
        ai_mode="legacy",
        filters_md_path=Path("docs/ops/FILTERS_LEGACY.md"),
        site_notify_on_ai_unavailable=False,
        site_notify_owner=False,
        radar_conveyor=False,
        l1_batch_per_cycle=40,
        l1_max_workers=3,
        l1_backlog_drain=False,
        match_push_enabled=False,
        stars_enabled=False,
        stars_price_xtr=300,
        stars_subscription_days=30,
    )
    assert cfg.legacy_neon_poll_sec == 60
