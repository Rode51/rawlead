"""Оркестрация: ленты FL/Kwork → SQLite → фильтр → [ИИ] → Telegram. TZ §4–5."""

from __future__ import annotations

import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections.abc import Callable
from pathlib import Path

if sys.platform == "win32":
    import msvcrt
else:
    msvcrt = None  # type: ignore

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_main_lock_fh = None

from config import (
    Config,
    apply_profile_argv,
    bot_poll_external,
    load_config,
    load_radar_env,
    radar_lock_path,
    radar_timestamp,
)
from filters import ListingWordFilter, default_listing_filter
from fl_parser import FlListingError, fetch_listing_projects
from habr_career_parser import (
    HabrCareerListingError,
    fetch_listing_projects as fetch_habr_career_listing,
)
from kwork_parser import KworkListingError, fetch_listing_projects as fetch_kwork_listing_projects
from public_feed import public_feed_sources
from vc_ru_parser import VcRuListingError, fetch_listing_projects as fetch_vc_ru_listing

from l1_pool import L1Pool
from delist_checker import run_delist_batch
from lead_pipeline import drain_l1_backlog, process_new_listing, short_err
from listing import ListingProject
from pg_storage import NeonLeadStorage, pg_storage_from_config
from radar_cycle_log import (
    CycleSummary,
    SourceCycleStats,
    begin_site_rollup_cycle,
    commit_site_rollup_cycle,
    emit_site_rollup_line,
    record_cycle_summary,
    reset_neon_cycle_counters,
    reset_site_rollup_emit_clock,
    site_rollup_emit_due,
)
from storage import ProjectStorage, storage_from_config

from bot_poll import try_poll_commands
from health_check import run_health_check
from telegram_control import send_control_panel

# Опрос getUpdates между циклами и во время run_cycle (не ждать POLL_INTERVAL).
_TG_POLL_INTERVAL_SEC = 2
_DELIST_INTERVAL_SEC = 3600
_DELIST_LAST_RUN_KEY = "delist_last_run_epoch"

_LISTING_ERRORS = (
    FlListingError,
    KworkListingError,
    VcRuListingError,
    HabrCareerListingError,
)

_P1_WEB_SOURCES: tuple[tuple[str, Callable[[Config], list[ListingProject]]], ...] = (
    ("vc_ru", fetch_vc_ru_listing),
    ("habr_career", fetch_habr_career_listing),
)


def _main_lock_path() -> Path:
    apply_profile_argv()
    load_radar_env()
    return radar_lock_path("main")


def _release_main_lock() -> None:
    global _main_lock_fh
    lock_path = _main_lock_path()
    if _main_lock_fh is not None:
        try:
            if msvcrt is not None:
                _main_lock_fh.seek(0)
                msvcrt.locking(_main_lock_fh.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        try:
            _main_lock_fh.close()
        except OSError:
            pass
        _main_lock_fh = None
    try:
        lock_path.unlink(missing_ok=True)
    except OSError:
        pass


def _acquire_main_lock() -> bool:
    global _main_lock_fh
    lock_path = _main_lock_path()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fh = open(lock_path, "a+b")
    except OSError:
        return False
    if msvcrt is not None:
        try:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            fh.close()
            return False
    _main_lock_fh = fh
    return True


def _log_main_lock_busy() -> None:
    try:
        cfg = load_config()
        log_path = cfg.radar_log_path
    except Exception:
        log_path = _PROJECT_ROOT / "data" / "radar.log"
    msg = f"{radar_timestamp()} радар:дубль:второй main — уже работает"
    print("[!] Второй запуск main — уже работает окно RawLead — биржи", flush=True)
    _append_log_line(log_path, msg)


def _enter_main_single_instance() -> bool:
    if _acquire_main_lock():
        return True
    _log_main_lock_busy()
    return False


def _echo(line: str) -> None:
    """Дублирует важные строки в консоль (окно start-radar.bat)."""
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        pass  # cp1251 при spawn с пульта; radar.log уже в utf-8


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


def _process_listings(
    projects: list[ListingProject],
    storage: ProjectStorage,
    word_filter: ListingWordFilter,
    cfg: Config,
    *,
    errors: list[str],
    pg: NeonLeadStorage | None = None,
    tg_poll_state: dict[str, float] | None = None,
    stats: SourceCycleStats | None = None,
    l1_pool: L1Pool | None = None,
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
            stats=stats,
            l1_pool=l1_pool,
        )
        if was_new:
            new_ids += 1
        if notified:
            notifications += 1

    return new_ids, notifications


def _fetch_listings_parallel(
    cfg: Config,
    enabled_sources: set[str],
    errors: list[str],
) -> dict[str, list[ListingProject] | None]:
    """Параллельный fetch FL + Kwork (только сеть, без SQLite)."""
    tasks: dict[str, Callable[[], list[ListingProject]]] = {}
    if "fl" in enabled_sources:
        tasks["fl"] = lambda: fetch_listing_projects(cfg)
    if "kwork" in enabled_sources and cfg.kwork_projects_url:
        tasks["kwork"] = lambda: fetch_kwork_listing_projects(cfg)
    out: dict[str, list[ListingProject] | None] = {k: None for k in tasks}
    if not tasks:
        return out
    with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
        future_map = {pool.submit(fn): label for label, fn in tasks.items()}
        for future in as_completed(future_map):
            label = future_map[future]
            try:
                out[label] = future.result()
            except (FlListingError, KworkListingError) as exc:
                errors.append(f"{label}:fetch:{short_err(exc)}")
            except Exception as exc:
                errors.append(f"{label}:fetch:{short_err(exc)}")
    return out


def _fetch_source(
    label: str,
    fetch_fn: Callable[[Config], list[ListingProject]],
    cfg: Config,
    errors: list[str],
    stats: SourceCycleStats | None = None,
) -> list[ListingProject] | None:
    try:
        return fetch_fn(cfg)
    except _LISTING_ERRORS as exc:
        msg = short_err(exc)
        errors.append(f"{label}:fetch:{msg}")
        if stats is not None:
            stats.fetch_error = msg
        return None
    except Exception as exc:
        msg = short_err(exc)
        errors.append(f"{label}:fetch:{msg}")
        if stats is not None:
            stats.fetch_error = msg
        return None


def _log_source_line(log_path: Path, stats: SourceCycleStats) -> None:
    _append_log_line(log_path, stats.format_line(), echo=True)


def _collect_misc_errors(errors: list[str], summary: CycleSummary) -> None:
    """Ошибки без skip:* / fetch: — в конец цикла (не дублировать воронку)."""
    for err in errors:
        if ":fetch:" in err or " skip:" in err:
            continue
        if err not in summary.misc_errors:
            summary.misc_errors.append(err)


def run_cycle(
    cfg: Config,
    storage: ProjectStorage,
    word_filter: ListingWordFilter,
    pg: NeonLeadStorage | None = None,
) -> None:
    """Один проход: FL, затем Kwork (если URL задан) → storage → фильтр → TG."""

    from ai_analyze import reset_cycle_ai_counters

    reset_cycle_ai_counters()
    reset_neon_cycle_counters()
    if cfg.radar_profile == "site":
        begin_site_rollup_cycle()
    ts = radar_timestamp()
    cycle_t0 = time.monotonic()
    errors: list[str] = []
    summary = CycleSummary(ts=ts)
    enabled_sources = set(public_feed_sources())

    _append_log_line(cfg.radar_log_path, summary.format_header(), echo=True)

    tg_poll_state: dict[str, float] = {"last": 0.0}
    _tg_poll_if_due(cfg, storage, tg_poll_state)

    l1_pool: L1Pool | None = None
    if (
        cfg.radar_profile == "site"
        and pg is not None
        and pg.enabled
        and cfg.ai_active
        and cfg.ai_uses_l1_l2
    ):
        l1_pool = L1Pool(cfg, pg, errors=errors)

    prefetched = _fetch_listings_parallel(cfg, enabled_sources, errors)

    if "fl" in enabled_sources:
        stats_fl = summary.ensure("fl")
        fl_projects = prefetched.get("fl")
        if fl_projects is None and not any(e.startswith("fl:fetch:") for e in errors):
            fl_projects = _fetch_source("fl", fetch_listing_projects, cfg, errors, stats_fl)
        if fl_projects is None:
            for err in errors:
                if err.startswith("fl:fetch:"):
                    stats_fl.fetch_error = err.split(":", 2)[-1][:120]
                    break
        _tg_poll_if_due(cfg, storage, tg_poll_state)
        if fl_projects is not None:
            stats_fl.downloaded = len(fl_projects)
            n, notify = _process_listings(
                fl_projects,
                storage,
                word_filter,
                cfg,
                errors=errors,
                pg=pg,
                tg_poll_state=tg_poll_state,
                stats=stats_fl,
                l1_pool=l1_pool,
            )
            stats_fl.new_ids = n
            stats_fl.to_bot = notify
            summary.total_to_bot += notify
        _log_source_line(cfg.radar_log_path, stats_fl)

    _tg_poll_if_due(cfg, storage, tg_poll_state)

    if "kwork" in enabled_sources:
        stats_kwork = summary.ensure("kwork")
        if cfg.kwork_projects_url:
            kwork_projects = prefetched.get("kwork")
            if kwork_projects is None and not any(
                e.startswith("kwork:fetch:") for e in errors
            ):
                kwork_projects = _fetch_source(
                    "kwork", fetch_kwork_listing_projects, cfg, errors, stats_kwork
                )
            if kwork_projects is not None:
                stats_kwork.downloaded = len(kwork_projects)
                n, notify = _process_listings(
                    kwork_projects,
                    storage,
                    word_filter,
                    cfg,
                    errors=errors,
                    pg=pg,
                    tg_poll_state=tg_poll_state,
                    stats=stats_kwork,
                    l1_pool=l1_pool,
                )
                stats_kwork.new_ids = n
                stats_kwork.to_bot = notify
                summary.total_to_bot += notify
        _log_source_line(cfg.radar_log_path, stats_kwork)

    _tg_poll_if_due(cfg, storage, tg_poll_state)

    for source_label, fetch_fn in _P1_WEB_SOURCES:
        if source_label not in enabled_sources:
            continue
        stats_web = summary.ensure(source_label)
        _tg_poll_if_due(cfg, storage, tg_poll_state)
        web_projects = _fetch_source(source_label, fetch_fn, cfg, errors, stats_web)
        if web_projects is not None:
            stats_web.downloaded = len(web_projects)
            n, notify = _process_listings(
                web_projects,
                storage,
                word_filter,
                cfg,
                errors=errors,
                pg=pg,
                tg_poll_state=tg_poll_state,
                stats=stats_web,
                l1_pool=l1_pool,
            )
            stats_web.new_ids = n
            stats_web.to_bot = notify
            summary.total_to_bot += notify
        _log_source_line(cfg.radar_log_path, stats_web)

    _tg_poll_if_due(cfg, storage, tg_poll_state)

    if l1_pool is not None:
        l1_done = l1_pool.drain()
        if l1_done > 0:
            _append_log_line(
                cfg.radar_log_path,
                f"pipeline:L1 pool done={l1_done} workers={cfg.l1_max_workers}",
                echo=True,
            )

    if cfg.l1_backlog_drain and pg is not None and cfg.ai_active:
        l1_n = drain_l1_backlog(
            cfg,
            pg,
            word_filter,
            errors=errors,
            limit=cfg.l1_batch_per_cycle,
        )
        if l1_n > 0:
            _append_log_line(
                cfg.radar_log_path,
                f"конвейер:L1={l1_n} (batch≤{cfg.l1_batch_per_cycle})",
                echo=True,
            )

    _maybe_run_delist_batch(cfg, pg, storage, errors)

    _collect_misc_errors(errors, summary)
    summary.sync_neon_from_globals()
    summary.cycle_sec = max(0.0, time.monotonic() - cycle_t0)
    if cfg.radar_profile == "site":
        commit_site_rollup_cycle(summary)
    record_cycle_summary(storage, summary)

    _append_log_line(
        cfg.radar_log_path,
        summary.format_footer(elapsed_sec=time.monotonic() - cycle_t0),
        echo=True,
    )
    if summary.misc_errors:
        _append_log_line(
            cfg.radar_log_path,
            f"Прочее: {'; '.join(summary.misc_errors[:5])}",
            echo=True,
        )
    if cfg.radar_profile == "site":
        _maybe_log_site_rollup(cfg, storage)


def _poll_and_log_tg_commands(cfg: Config, storage: ProjectStorage) -> None:
    if bot_poll_external():
        return
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


def _maybe_run_delist_batch(
    cfg: Config,
    pg: NeonLeadStorage | None,
    storage: ProjectStorage,
    errors: list[str],
) -> None:
    if cfg.radar_profile != "site" or pg is None or not pg.enabled:
        return
    now = time.time()
    raw = storage.get_setting(_DELIST_LAST_RUN_KEY, "0").strip()
    try:
        last = float(raw)
    except ValueError:
        last = 0.0
    if now - last < _DELIST_INTERVAL_SEC:
        return
    stats = run_delist_batch(cfg, pg, errors=errors)
    storage.set_setting(_DELIST_LAST_RUN_KEY, str(now))
    if stats["checked"] or stats["delisted"]:
        _append_log_line(
            cfg.radar_log_path,
            f"delist: checked={stats['checked']} delisted={stats['delisted']} "
            f"skipped={stats['skipped']}",
            echo=True,
        )


def _maybe_log_site_rollup(cfg: Config, storage: ProjectStorage) -> None:
    if cfg.radar_profile != "site" or not site_rollup_emit_due():
        return
    line = emit_site_rollup_line(storage)
    _append_log_line(cfg.radar_log_path, line, echo=True)


def _sleep_with_tg_poll(
    cfg: Config,
    storage: ProjectStorage,
    total_sec: int,
    *,
    chunk_sec: int = _TG_POLL_INTERVAL_SEC,
) -> None:
    """Между циклами: сначала getUpdates, затем корочный sleep (не один раз на POLL_INTERVAL)."""
    deadline = time.monotonic() + max(0.0, float(total_sec))
    while True:
        _poll_and_log_tg_commands(cfg, storage)
        if cfg.radar_profile == "site":
            _maybe_log_site_rollup(cfg, storage)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(float(chunk_sec), remaining))


def _log_failed_cycle(
    log_path: Path,
    storage: ProjectStorage,
    ts: str,
    exc: BaseException,
) -> None:
    summary = CycleSummary(ts=ts)
    summary.misc_errors.append(f"cycle:{short_err(exc)}")
    _append_log_line(log_path, summary.format_header(), echo=True)
    for stats in summary.iter_sources():
        _append_log_line(log_path, stats.format_line(), echo=True)
    _append_log_line(log_path, summary.format_footer(), echo=True)
    _append_log_line(
        log_path,
        f"Прочее: {summary.misc_errors[0]}",
        echo=True,
    )
    record_cycle_summary(storage, summary)


def main() -> None:
    from config import radar_exchanges_enabled

    apply_profile_argv()
    load_radar_env()
    if not radar_exchanges_enabled():
        print(
            "main.py: RADAR_EXCHANGES_ENABLED=0 — биржи крутит Site; "
            "legacy использует neon_legacy_consumer.py",
            flush=True,
        )
        raise SystemExit(0)

    cfg = load_config()
    storage = storage_from_config(cfg)
    pg = pg_storage_from_config(cfg)
    word_filter = default_listing_filter()
    interval_sec = max(1, cfg.poll_interval_minutes * 60)
    _echo(f"=== RawLead [{cfg.radar_profile}] ({radar_timestamp()}, Иркутск) ===")
    _echo(f"Лог: {cfg.radar_log_path.resolve()}")
    _echo(
        f"Профиль: {cfg.radar_profile} | ИИ: "
        f"{'L1/L2' if cfg.ai_uses_l1_l2 else 'legacy (один разбор)'}"
    )
    _echo(
        f"Интервал: {cfg.poll_interval_minutes} мин | "
        f"Конвейер: {'вкл' if cfg.radar_conveyor else 'выкл'} | "
        f"L1 pool: {cfg.l1_max_workers} | "
        f"Backlog drain: {'вкл' if cfg.l1_backlog_drain else 'выкл'} | "
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
    if cfg.radar_profile == "site":
        reset_site_rollup_emit_clock()

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
            ts_h = radar_timestamp()
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
            _log_failed_cycle(cfg.radar_log_path, storage, ts, exc)

        _sleep_with_tg_poll(cfg, storage, interval_sec)


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--telegram-smoke":
        from tg_smoke import run_smoke

        raise SystemExit(run_smoke())
    if not _enter_main_single_instance():
        raise SystemExit(1)
    try:
        main()
    finally:
        _release_main_lock()
