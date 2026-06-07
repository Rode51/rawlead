"""O122: delist env, redirect detection, gone markers."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from delist_checker import (
    delist_batch_limit,
    delist_interval_sec,
    load_delist_last_stats,
    run_delist_batch,
    save_delist_run,
)
from fl_parser import check_project_page_gone
from kwork_parser import check_project_page_gone as kwork_check_gone


class _Cfg:
    http_user_agent = "test"


class _Storage:
    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def get_setting(self, key: str, default: str = "") -> str:
        return self._data.get(key, default)

    def set_setting(self, key: str, value: str) -> None:
        self._data[key] = value


def test_delist_env_defaults() -> None:
    with patch.dict("os.environ", {}, clear=True):
        assert delist_batch_limit() == 40
        assert delist_interval_sec() == 1800


def test_delist_env_override() -> None:
    with patch.dict(
        "os.environ",
        {"DELIST_BATCH_LIMIT": "55", "DELIST_INTERVAL_SEC": "900"},
        clear=True,
    ):
        assert delist_batch_limit() == 55
        assert delist_interval_sec() == 900


def test_save_and_load_delist_stats() -> None:
    storage = _Storage()
    save_delist_run(storage, {"checked": 12, "delisted": 3, "skipped": 1}, epoch=1_700_000_000.0)
    stats = load_delist_last_stats(storage)
    assert stats["checked"] == 12
    assert stats["delisted"] == 3
    assert stats["skipped"] == 1
    assert stats["last_run_at"] is not None
    raw = storage.get_setting("delist_last_stats_json")
    assert json.loads(raw)["delisted"] == 3


def test_fl_redirect_away_is_gone() -> None:
    cfg = _Cfg()
    resp = MagicMock()
    resp.status_code = 200
    resp.encoding = "utf-8"
    resp.url = "https://www.fl.ru/projects/"
    resp.content = b"<html><body>FL projects list</body></html>"
    with patch("fl_parser.exchange_get", return_value=resp):
        assert check_project_page_gone("https://www.fl.ru/projects/12345/", cfg) is True


def test_fl_live_page_not_gone() -> None:
    cfg = _Cfg()
    resp = MagicMock()
    resp.status_code = 200
    resp.encoding = "utf-8"
    resp.url = "https://www.fl.ru/projects/12345/"
    resp.content = b"<html><div class='fl-project-content'>live</div></html>"
    with patch("fl_parser.exchange_get", return_value=resp):
        assert check_project_page_gone("https://www.fl.ru/projects/12345/", cfg) is False


def test_fl_new_gone_marker() -> None:
    cfg = _Cfg()
    resp = MagicMock()
    resp.status_code = 200
    resp.encoding = "utf-8"
    resp.url = "https://www.fl.ru/projects/99/"
    resp.content = "<html>закрыт для откликов</html>".encode()
    with patch("fl_parser.exchange_get", return_value=resp):
        assert check_project_page_gone("https://www.fl.ru/projects/99/", cfg) is True


def test_run_delist_batch_respects_limit() -> None:
    cfg = _Cfg()
    pg = MagicMock()
    pg.fetch_visible_for_source_recheck.return_value = []
    stats = run_delist_batch(cfg, pg, limit=15)
    pg.fetch_visible_for_source_recheck.assert_called_once()
    assert pg.fetch_visible_for_source_recheck.call_args.kwargs["limit"] == 15
    assert stats == {"checked": 0, "delisted": 0, "skipped": 0}


def test_kwork_redirect_away_is_gone() -> None:
    cfg = MagicMock(http_user_agent="test")
    resp = MagicMock(status_code=200, encoding="utf-8")
    resp.url = "https://kwork.ru/"
    resp.content = b"<html><body>kwork home</body></html>"
    with patch("kwork_parser.exchange_get", return_value=resp):
        assert kwork_check_gone("https://kwork.ru/projects/3190279/view", cfg) is True
