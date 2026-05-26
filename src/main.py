"""Оркестрация: ленты FL/Kwork → SQLite → фильтр → [ИИ] → Telegram. TZ §4–5."""



from __future__ import annotations



import random

import time

from collections.abc import Callable

from pathlib import Path



from config import Config, load_config, radar_timestamp

from filters import ListingWordFilter, default_listing_filter

from fl_parser import FlListingError, fetch_listing_projects

from freelancehunt_parser import (
    FreelancehuntListingError,
    fetch_listing_projects as fetch_freelancehunt_listing,
)
from habr_career_parser import (
    HabrCareerListingError,
    fetch_listing_projects as fetch_habr_career_listing,
)
from kwork_parser import KworkListingError, fetch_listing_projects as fetch_kwork_listing_projects
from public_feed import public_feed_sources
from vc_ru_parser import VcRuListingError, fetch_listing_projects as fetch_vc_ru_listing

from lead_pipeline import process_new_listing, short_err

from listing import ListingProject

from pg_storage import NeonLeadStorage, pg_storage_from_config
from storage import ProjectStorage, storage_from_config

from bot_poll import try_poll_commands
from health_check import run_health_check
from radar_status import record_fl_kwork_cycle
from telegram_control import send_control_panel

# Опрос getUpdates между циклами и во время run_cycle (не ждать POLL_INTERVAL).
# Опрос getUpdates; 2 с ≈ ответ на кнопки за 2–4 с (два окна делят lock).
_TG_POLL_INTERVAL_SEC = 2

_LISTING_ERRORS = (
    FlListingError,
    KworkListingError,
    VcRuListingError,
    FreelancehuntListingError,
    HabrCareerListingError,
)

_P1_WEB_SOURCES: tuple[tuple[str, Callable[[Config], list[ListingProject]]], ...] = (
    ("vc_ru", fetch_vc_ru_listing),
    ("freelancehunt", fetch_freelancehunt_listing),
    ("habr_career", fetch_habr_career_listing),
)





def _echo(line: str) -> None:
    """Дублирует важные строки в консоль (окно start-radar.bat)."""
    print(line, flush=True)


def _append_log_line(log_path: Path, line: str, *, echo: bool = False) -> None:

    log_path = Path(log_path)

    parent = log_path.parent

    if str(parent) not in ("", "."):

        parent.mkdir(parents=True, exist_ok=True)

    text = line.rstrip("\n") + "\n"

    with log_path.open("a", encoding="utf-8") as f:

        f.write(text)

    if echo:

        _echo(line.rstrip("\n"))





def _log_cycle(

    log_path: Path,

    *,

    ts: str,

    cards_fl: int,

    cards_kwork: int,

    new_ids: int,

    notifications: int,

    errors: list[str],

) -> None:

    err_part = "; ".join(errors) if errors else "-"

    line = (
        f"{ts} карточки_fl={cards_fl} карточки_kwork={cards_kwork} "
        f"новых={new_ids} уведом={notifications} ош={err_part}"
    )

    _append_log_line(log_path, line, echo=True)





def _process_listings(
    projects: list[ListingProject],
    storage: ProjectStorage,
    word_filter: ListingWordFilter,
    cfg: Config,
    *,
    errors: list[str],
    pg: NeonLeadStorage | None = None,
    tg_poll_state: dict[str, float] | None = None,
) -> tuple[int, int]:
    """Обработка карточек одного источника; возвращает (new_ids, notifications)."""
    new_ids = 0
    notifications = 0

    for project in projects:
        if tg_poll_state is not None:
            _tg_poll_if_due(cfg, storage, tg_poll_state)
        was_new, notified = process_new_listing(
            project,
            storage,
            word_filter,
            cfg,
            errors=errors,
            pg=pg,
        )
        if was_new:
            new_ids += 1
        if notified:
            notifications += 1

    return new_ids, notifications





def _fetch_source(

    label: str,

    fetch_fn: Callable[[Config], list[ListingProject]],

    cfg: Config,

    errors: list[str],

) -> list[ListingProject] | None:

    try:

        return fetch_fn(cfg)

    except _LISTING_ERRORS as exc:

        errors.append(f"{label}:fetch:{short_err(exc)}")

        return None

    except Exception as exc:

        errors.append(f"{label}:fetch:{short_err(exc)}")

        return None





def run_cycle(

    cfg: Config,

    storage: ProjectStorage,

    word_filter: ListingWordFilter,

    pg: NeonLeadStorage | None = None,

) -> None:

    """Один проход: FL, затем Kwork (если URL задан) → storage → фильтр → TG."""

    ts = radar_timestamp()

    errors: list[str] = []

    cards_fl = 0

    cards_kwork = 0

    new_ids = 0

    notifications = 0



    _append_log_line(cfg.radar_log_path, f"{ts} цикл:старт")

    tg_poll_state: dict[str, float] = {"last": 0.0}
    _tg_poll_if_due(cfg, storage, tg_poll_state)

    fl_projects = _fetch_source("fl", fetch_listing_projects, cfg, errors)
    _tg_poll_if_due(cfg, storage, tg_poll_state)

    if fl_projects is not None:

        cards_fl = len(fl_projects)

        n, notify = _process_listings(
            fl_projects,
            storage,
            word_filter,
            cfg,
            errors=errors,
            pg=pg,
            tg_poll_state=tg_poll_state,
        )

        new_ids += n

        notifications += notify

    _tg_poll_if_due(cfg, storage, tg_poll_state)

    if cfg.kwork_projects_url:

        kwork_projects = _fetch_source(

            "kwork", fetch_kwork_listing_projects, cfg, errors

        )

        if kwork_projects is not None:

            cards_kwork = len(kwork_projects)

            n, notify = _process_listings(
                kwork_projects,
                storage,
                word_filter,
                cfg,
                errors=errors,
                pg=pg,
                tg_poll_state=tg_poll_state,
            )

            new_ids += n

            notifications += notify

    _tg_poll_if_due(cfg, storage, tg_poll_state)

    enabled_sources = public_feed_sources()
    for source_label, fetch_fn in _P1_WEB_SOURCES:
        if source_label not in enabled_sources:
            continue
        _tg_poll_if_due(cfg, storage, tg_poll_state)
        web_projects = _fetch_source(source_label, fetch_fn, cfg, errors)
        if web_projects is not None:
            n, notify = _process_listings(
                web_projects,
                storage,
                word_filter,
                cfg,
                errors=errors,
                pg=pg,
                tg_poll_state=tg_poll_state,
            )
            new_ids += n
            notifications += notify

    _tg_poll_if_due(cfg, storage, tg_poll_state)

    record_fl_kwork_cycle(
        storage,
        cards_fl=cards_fl,
        cards_kwork=cards_kwork,
        new_ids=new_ids,
        notifications=notifications,
        errors=errors,
    )

    _log_cycle(

        cfg.radar_log_path,

        ts=ts,

        cards_fl=cards_fl,

        cards_kwork=cards_kwork,

        new_ids=new_ids,

        notifications=notifications,

        errors=errors,

    )





def _poll_and_log_tg_commands(cfg: Config, storage: ProjectStorage) -> None:
    for line in try_poll_commands(cfg, storage):
        ts = radar_timestamp()
        full = f"{ts} {line}"
        echo = "тг:бот:" in line or line.startswith("тг:команда:")
        if "HTTP 409" in line:
            _echo(
                "[!] Telegram 409: два процесса с одним ботом "
                "(stop-radar.bat, закрой Cursor/uvicorn)"
            )
        _append_log_line(cfg.radar_log_path, full, echo=echo)


def _tg_poll_if_due(
    cfg: Config,
    storage: ProjectStorage,
    state: dict[str, float],
) -> None:
    """getUpdates во время долгого цикла (ИИ/парсинг), не реже чем раз в ~5 с."""
    now = time.monotonic()
    last = state.get("last", 0.0)
    if last <= 0.0 or now - last >= _TG_POLL_INTERVAL_SEC:
        _poll_and_log_tg_commands(cfg, storage)
        state["last"] = now


def _sleep_with_tg_poll(
    cfg: Config,
    storage: ProjectStorage,
    total_sec: int,
    *,
    chunk_sec: int = _TG_POLL_INTERVAL_SEC,
) -> None:
    """Между циклами: сначала getUpdates, затем короткий sleep (не один раз на POLL_INTERVAL)."""
    deadline = time.monotonic() + max(0.0, float(total_sec))
    while True:
        _poll_and_log_tg_commands(cfg, storage)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(float(chunk_sec), remaining))


def main() -> None:

    cfg = load_config()

    storage = storage_from_config(cfg)

    pg = pg_storage_from_config(cfg)

    word_filter = default_listing_filter()

    interval_sec = max(1, cfg.poll_interval_minutes * 60)

    _echo(f"=== RawLead запущен ({radar_timestamp()}, Иркутск) ===")
    _echo(f"Лог: {cfg.radar_log_path.resolve()}")
    _echo(
        f"Интервал: {cfg.poll_interval_minutes} мин | "
        f"ИИ: {'вкл' if cfg.ai_active else 'выкл'} | "
        f"Фильтр: {'широкий' if cfg.filter_wide else 'узкий'} | "
        f"Пауза: {'да' if storage.is_radar_paused() else 'нет'} | "
        f"Neon: {'вкл' if pg is not None else 'выкл'}"
    )
    _echo("Окно не закрывать. Пауза — кнопка в TG. Ctrl+C = стоп.")
    _echo("уведом=0 при новых=0 — заказы уже в базе, это нормально.")
    _echo("---")

    ts0 = radar_timestamp()
    _append_log_line(cfg.radar_log_path, f"{ts0} радар:старт", echo=True)

    try:
        send_control_panel(cfg)
    except Exception as exc:
        ts = radar_timestamp()
        _append_log_line(
            cfg.radar_log_path,
            f"{ts} тг:панель:{short_err(exc)}",
        )

    while True:

        _poll_and_log_tg_commands(cfg, storage)

        try:
            run_health_check(cfg, storage, log_path=cfg.radar_log_path, force=False)
        except Exception as exc:
            ts_h = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            _append_log_line(
                cfg.radar_log_path,
                f"{ts_h} здравье:ошибка {short_err(exc)}",
            )

        if storage.is_radar_paused():

            ts = radar_timestamp()

            _append_log_line(cfg.radar_log_path, f"{ts} цикл:пауза", echo=True)

            _sleep_with_tg_poll(cfg, storage, random.randint(10, 15))

            continue

        try:

            run_cycle(cfg, storage, word_filter, pg)

        except Exception as exc:

            ts = radar_timestamp()

            _log_cycle(

                cfg.radar_log_path,

                ts=ts,

                cards_fl=0,

                cards_kwork=0,

                new_ids=0,

                notifications=0,

                errors=[f"cycle:{short_err(exc)}"],

            )

        _sleep_with_tg_poll(cfg, storage, interval_sec)





if __name__ == "__main__":

    import sys



    if len(sys.argv) >= 2 and sys.argv[1] == "--telegram-smoke":

        from tg_smoke import run_smoke



        raise SystemExit(run_smoke())

    main()

