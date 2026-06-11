"""O122/O180: delist env, redirect detection, gone markers."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from delist_checker import (
    delist_batch_limit,
    delist_grace_hours,
    delist_interval_sec,
    load_delist_last_stats,
    run_delist_batch,
    save_delist_run,
)
from exchange_delist import check_source_page_gone
from fl_parser import check_project_page_gone
from freelance_ru_parser import check_project_page_gone as freelance_ru_check_gone
from freelancejob_parser import check_project_page_gone as freelancejob_check_gone
from kwork_parser import check_project_page_gone as kwork_check_gone
from pchyol_parser import check_project_page_gone as pchyol_check_gone
from youdo_parser import check_project_page_gone as youdo_check_gone


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
        assert delist_batch_limit() == 80
        assert delist_interval_sec() == 900
        assert delist_grace_hours() == 6


def test_delist_env_override() -> None:
    with patch.dict(
        "os.environ",
        {
            "DELIST_BATCH_LIMIT": "55",
            "DELIST_INTERVAL_SEC": "1200",
            "DELIST_GRACE_HOURS": "12",
        },
        clear=True,
    ):
        assert delist_batch_limit() == 55
        assert delist_interval_sec() == 1200
        assert delist_grace_hours() == 12


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


def test_youdo_gone_marker() -> None:
    cfg = _Cfg()
    html = "<html><body>Задание закрыто, исполнитель уже выбран</body></html>"
    with patch(
        "youdo_parser.fetch_youdo_detail_snapshot",
        return_value=(html, "https://youdo.com/t12345"),
    ):
        assert youdo_check_gone("https://youdo.com/t12345", cfg) is True


def test_youdo_redirect_away_is_gone() -> None:
    cfg = _Cfg()
    html = (
        "<html><body>Страница была удалена. Возможно, она была перемещена.</body></html>"
    )
    with patch(
        "youdo_parser.fetch_youdo_detail_snapshot",
        return_value=(html, "https://youdo.com/?page-deleted"),
    ):
        assert youdo_check_gone("https://youdo.com/t14828937", cfg) is True


def test_youdo_closed_for_responses() -> None:
    """t14828621: closed for responses but page shell still has __next_data__."""
    cfg = _Cfg()
    html = (
        '<html><body><span>Закрыто для откликов</span>'
        '<div id="taskDescription">live task body</div>'
        '<script id="__NEXT_DATA__">{"props":{"pageProps":{"task":{"id":14828621}}}}</script>'
        "</body></html>"
    )
    with patch(
        "youdo_parser.fetch_youdo_detail_snapshot",
        return_value=(html, "https://youdo.com/t14828621"),
    ):
        assert youdo_check_gone("https://youdo.com/t14828621", cfg) is True


def test_youdo_deleted_marker_with_next_data_shell() -> None:
    """Homepage shell after redirect must not false-negative on __next_data__."""
    cfg = _Cfg()
    html = (
        '<html><body>Страница была удалена или доступ к ней ограничен.</body>'
        '<script id="__NEXT_DATA__">{"props":{}}</script></html>'
    )
    with patch(
        "youdo_parser.fetch_youdo_detail_snapshot",
        return_value=(html, "https://youdo.com/?page-deleted"),
    ):
        assert youdo_check_gone("https://youdo.com/t14828937", cfg) is True


def test_youdo_alive_page() -> None:
    cfg = _Cfg()
    html = (
        '<html><script id="__NEXT_DATA__">{"props":{"pageProps":{"task":{"description":"live"}}}}'
        "</script></html>"
    )
    with patch(
        "youdo_parser.fetch_youdo_detail_snapshot",
        return_value=(html, "https://youdo.com/t99001"),
    ):
        assert youdo_check_gone("https://youdo.com/t99001", cfg) is False


def test_youdo_in_progress_sbr() -> None:
    """t14827772: in-progress + SBR reserved — not open for offers."""
    cfg = _Cfg()
    next_data = {
        "props": {
            "initialState": {
                "taskState": {
                    "taskInfo": {"id": 14827772, "sbrDealState": 10, "offerPrice": 299},
                    "taskStatuses": {
                        "isOpen": False,
                        "isClosed": False,
                        "isInProcess": True,
                        "isFinished": False,
                        "isClosedForOffers": False,
                        "code": "PendingApprovement",
                        "flag": "process",
                        "text": "Выполняется",
                    },
                }
            }
        }
    }
    html = (
        "<html><body>"
        '<span class="TaskStatusChip_root__x">Выполняется</span>'
        "<div>Зарезервировано 299 ₽</div>"
        '<div id="taskDescription">Описание задания</div>'
        f'<script id="__NEXT_DATA__">{json.dumps(next_data, ensure_ascii=False)}</script>'
        "</body></html>"
    )
    with patch(
        "youdo_parser.fetch_youdo_detail_snapshot",
        return_value=(html, "https://youdo.com/t14827772"),
    ):
        assert youdo_check_gone("https://youdo.com/t14827772", cfg) is True


def test_youdo_live_description_not_gone() -> None:
    """Open task body may say «выполняется удаленно» — must stay alive."""
    cfg = _Cfg()
    html = (
        "<html><body>"
        '<div id="taskDescription">'
        "Нужен специалист: работа выполняется удаленно из дома, график гибкий."
        "</div>"
        '<script id="__NEXT_DATA__">{"props":{"pageProps":{"task":{"description":"live"}}}}'
        "</script></body></html>"
    )
    with patch(
        "youdo_parser.fetch_youdo_detail_snapshot",
        return_value=(html, "https://youdo.com/t99002"),
    ):
        assert youdo_check_gone("https://youdo.com/t99002", cfg) is False


def test_youdo_http_404() -> None:
    cfg = _Cfg()
    resp = MagicMock(status_code=404, encoding="utf-8", url="https://youdo.com/t404")
    resp.content = b"not found"
    from html_fetch import HtmlFetchError

    with patch(
        "youdo_parser.fetch_youdo_detail_snapshot",
        side_effect=HtmlFetchError("browser"),
    ):
        with patch(
            "exchange_proxy.exchange_alive_proxy_urls",
            return_value=["http://proxy/"],
        ):
            with patch("youdo_parser.requests.get", return_value=resp):
                assert youdo_check_gone("https://youdo.com/t404", cfg) is True


def test_freelance_ru_gone_redirect() -> None:
    cfg = _Cfg()
    resp = MagicMock(status_code=200, encoding="utf-8")
    resp.url = "https://freelance.ru/project/search"
    resp.content = b"<html>search</html>"
    with patch("freelance_ru_parser.exchange_get", return_value=resp):
        assert (
            freelance_ru_check_gone("https://freelance.ru/task/view/555", cfg) is True
        )


def test_freelance_ru_alive() -> None:
    cfg = _Cfg()
    resp = MagicMock(status_code=200, encoding="utf-8")
    resp.url = "https://freelance.ru/task/view/555"
    resp.content = b"<html><div class='task-view__description'>live</div></html>"
    with patch("freelance_ru_parser.exchange_get", return_value=resp):
        assert freelance_ru_check_gone("https://freelance.ru/task/view/555", cfg) is False


def test_freelancejob_gone_marker() -> None:
    cfg = _Cfg()
    resp = MagicMock(status_code=200, encoding="utf-8", url="https://www.freelancejob.ru/vacancy/77/")
    resp.content = "<html>вакансия закрыта</html>".encode()
    with patch("freelancejob_parser.exchange_get", return_value=resp):
        assert freelancejob_check_gone("https://www.freelancejob.ru/vacancy/77/", cfg) is True


def test_pchyol_alive() -> None:
    cfg = _Cfg()
    resp = MagicMock(status_code=200, encoding="utf-8")
    resp.url = "https://pchel.net/jobs/design/logo-101/"
    resp.content = b"<html><div class='project-text'>live order</div></html>"
    with patch("pchyol_parser.exchange_get", return_value=resp):
        assert pchyol_check_gone("https://pchel.net/jobs/design/logo-101/", cfg) is False


def test_tg_source_skipped() -> None:
    cfg = _Cfg()
    assert check_source_page_gone("tg:-100123", "https://t.me/example/1", cfg) is None
    assert check_source_page_gone("tg", "https://t.me/example/1", cfg) is None
