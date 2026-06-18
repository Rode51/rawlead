"""O207b: TG wide filter soft-stop bypass for owner-labeled vacancies."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "scripts"))

from config import load_config  # noqa: E402
from filters import default_listing_filter  # noqa: E402
import tg_filter_replay as replay  # noqa: E402

_LABELED = _ROOT / "data" / "tg_history_sample_labeled.json"
_BEFORE = _ROOT / "data" / "tg_filter_replay_before.json"


def _labeled_rows() -> list[dict]:
    payload = json.loads(_LABELED.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else payload.get("rows") or []


def _vacancy_blocked_ids() -> list[int]:
    before = json.loads(_BEFORE.read_text(encoding="utf-8"))
    rows = _labeled_rows()
    return [
        int(row["msg_id"])
        for row, rep in zip(rows, before["rows"])
        if row.get("owner_label") == "vacancy" and rep.get("stage") == "filter"
    ]


@pytest.fixture
def live_filter():
    load_config()
    return default_listing_filter()


@pytest.fixture
def filter_wide() -> bool:
    return load_config().filter_wide


@pytest.mark.parametrize("msg_id", _vacancy_blocked_ids())
def test_vacancy_blocked_fixtures_pass(
    msg_id: int, live_filter, filter_wide: bool
) -> None:
    row = next(r for r in _labeled_rows() if r.get("msg_id") == msg_id)
    out = replay.replay_row(row, word_filter=live_filter, filter_wide=filter_wide)
    assert out["would_spam"] is False
    assert out["filter_pass"] is True
    assert out["stage"] == "pass"


@pytest.mark.parametrize(
    "row",
    [
        {
            "title": "#техспецgetcourse #техспецзапуск #salebot #amocrm #чатботы",
            "body_preview": "Бесплатный вебинар по настройке воронки",
            "parse_ok": True,
            "owner_label": "noise",
        },
        {
            "title": "#вакансия #монтажер #помогу #рислмейкер",
            "body_preview": "Предлагаю услуги видеомонтажа, портфолио в личке",
            "parse_ok": True,
            "owner_label": "noise",
        },
        {
            "title": "🎨 ИЩЕМ ДИЗАЙНЕРА В КОМАНДУ",
            "body_preview": (
                "Ищем дизайнера в команду. Разработка логотипов и баннеров."
            ),
            "parse_ok": True,
            "owner_label": "noise",
        },
        {
            "title": "Ищу проект",
            "body_preview": "Опытный разработчик, портфолио в личке",
            "parse_ok": True,
            "owner_label": "noise",
        },
        {
            "title": "11 июня начинается курс графического дизайна",
            "body_preview": "Научим делать логотипы с нуля, регистрируйтесь",
            "parse_ok": True,
            "owner_label": "noise",
        },
    ],
)
def test_noise_rows_still_blocked_or_spam(row: dict, live_filter, filter_wide: bool) -> None:
    out = replay.replay_row(row, word_filter=live_filter, filter_wide=filter_wide)
    assert out["stage"] in {"filter", "spam"}
    assert out["filter_pass"] is False


def test_full_labeled_replay_vacancy_blocked_zero(live_filter, filter_wide: bool) -> None:
    sample = {"rows": _labeled_rows()}
    report = replay.replay_sample(
        sample, word_filter=live_filter, filter_wide=filter_wide
    )
    blocked = [
        rep
        for row, rep in zip(_labeled_rows(), report["rows"])
        if row.get("owner_label") == "vacancy" and rep.get("stage") == "filter"
    ]
    assert blocked == []
