"""O207-t5: filter replay on fixture posts (no Telethon)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "scripts"))

from filters import ListingWordFilter  # noqa: E402
import tg_filter_replay as replay  # noqa: E402


@pytest.fixture
def wide_filter() -> ListingWordFilter:
    return ListingWordFilter(
        take=("разработка", "бот"),
        stop=("казино",),
    )


def test_replay_spam_cv_post(wide_filter: ListingWordFilter) -> None:
    row = {
        "account": "acc1",
        "chat_id": -1001,
        "msg_id": 1,
        "chat_title": "Test",
        "title": "Ищу проект",
        "body_preview": "Опытный разработчик ищу заказчиков, портфолио в личке",
        "parse_ok": True,
    }
    out = replay.replay_row(row, word_filter=wide_filter, filter_wide=True)
    assert out["would_spam"] is True
    assert out["filter_pass"] is False
    assert out["stage"] == "spam"


def test_replay_filter_stop_word(wide_filter: ListingWordFilter) -> None:
    row = {
        "account": "acc1",
        "chat_id": -1001,
        "msg_id": 2,
        "chat_title": "Test",
        "title": "Нужен сайт",
        "body_preview": "Требуется лендинг без казино тематики",
        "parse_ok": True,
    }
    out = replay.replay_row(row, word_filter=wide_filter, filter_wide=True)
    assert out["would_spam"] is False
    assert out["filter_pass"] is False
    assert out["filter_reason"] == "stop:казино"
    assert out["stage"] == "filter"


def test_replay_passes_filter(wide_filter: ListingWordFilter) -> None:
    row = {
        "account": "acc1",
        "chat_id": -1001,
        "msg_id": 3,
        "chat_title": "Test",
        "title": "Нужен телеграм бот",
        "body_preview": "Требуется разработка бота для приёма заявок, бюджет 30к",
        "parse_ok": True,
        "owner_label": "vacancy",
    }
    out = replay.replay_row(row, word_filter=wide_filter, filter_wide=True)
    assert out["would_spam"] is False
    assert out["filter_pass"] is True
    assert out["stage"] == "pass"
    assert out["owner_label"] == "vacancy"


def test_replay_sample_summary(wide_filter: ListingWordFilter) -> None:
    sample = {
        "rows": [
            {
                "title": "Ищу проект",
                "body_preview": "ищу заказчиков портфолио",
                "parse_ok": True,
            },
            {
                "title": "Сайт",
                "body_preview": "казино лендинг",
                "parse_ok": True,
            },
            {
                "title": "Бот",
                "body_preview": "разработка telegram bot",
                "parse_ok": True,
            },
        ]
    }
    report = replay.replay_sample(sample, word_filter=wide_filter, filter_wide=True)
    s = report["summary"]
    assert s["would_spam"] == 1
    assert s["would_skip_filter"] == 1
    assert s["would_pass_filter"] == 1
    assert s["total"] == 3
