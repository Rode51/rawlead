"""Оркестрация: ленты FL/Kwork → SQLite → фильтр → [ИИ] → Telegram. TZ §4–5."""

from __future__ import annotations

import os
import inspect
import random
import socket
import sys
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
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
from freelance_ru_parser import (
    FreelanceRuListingError,
    fetch_listing_projects as fetch_freelance_ru_listing,
)
from freelancejob_parser import (
    FreelancejobListingError,
    fetch_listing_projects as fetch_freelancejob_listing,
)
from pchyol_parser import PchyolListingError, fetch_listing_projects as fetch_pchyol_listing, filter_new_pchyol_projects
from habr_career_parser import (
    HabrCareerListingError,
    fetch_listing_projects as fetch_habr_career_listing,
)
from kwork_parser import KworkListingError, fetch_listing_projects as fetch_kwork_listing_projects
from youdo_parser import YoudoListingError, fetch_listing_projects as fetch_youdo_listing
from public_feed import public_feed_sources
from vc_ru_parser import VcRuListingError, fetch_listing_projects as fetch_vc_ru_listing

from l1_pool import L1Pool
from delist_checker import delist_interval_sec, maybe_run_delist_batch
from feed_retention import run_feed_retention_batch
from trial_subscription import run_trial_maintenance
from exchange_health import (
    GREEN_MAX_MIN,
    append_health_log,
    format_health_log_line,
    load_health,
    maybe_send_red_alert,
    record_fetch,
    record_ok_ping,
)
from lead_pipeline import drain_l1_backlog, drain_tools_backlog, process_new_listing, short_err
from listing import ListingProject
from pg_storage import NeonLeadStorage, pg_storage_from_config
from radar_cycle_log import (
    CycleSummary,
    SourceCycleStats,
    take_listing_metrics,
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
_FEED_RETENTION_LAST_RUN_KEY = "feed_retention_last_run_epoch"


class CycleWatchdogError(RuntimeError):
    """Site cycle exceeded RADAR_CYCLE_WALL_SEC (O160)."""


def _env_float(name: str, default: float, *, minimum: float = 0.0) -> float:
    raw = os.getenv(name, str(default)).strip()
    try:
        return max(float(raw), minimum)
    except ValueError:
        return default


def _radar_source_fetch_wall_sec(source: str = "") -> float:
    """Per-source wall must cover internal browser retry budget (O179 YouDo 330s)."""
    base = _env_float("RADAR_SOURCE_FETCH_WALL_SEC", 180.0, minimum=1.0)
    if (source or "").strip().lower() == "youdo":
        try:
            from youdo_parser import youdo_source_fetch_wall_sec

            return max(base, youdo_source_fetch_wall_sec())
        except Exception:
            pass
    return base


def _radar_cycle_wall_sec() -> float:
    base = _env_float("RADAR_CYCLE_WALL_SEC", 600.0, minimum=0.0)
    if "youdo" in public_feed_sources():
        return max(base, 900.0)
    return base


def _sd_notify(message: str) -> None:
    """systemd sd_notify — no-op without NOTIFY_SOCKET (O160 L6a)."""
    addr = os.environ.get("NOTIFY_SOCKET", "").strip()
    if not addr:
        return
    if addr[0] == "@":
        addr = "\0" + addr[1:]
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock.connect(addr)
        sock.sendall(message.encode())
        sock.close()
    except OSError:
        pass


class _CycleWatchdog:
    def __init__(self, wall_sec: float, log_path: Path) -> None:
        self._wall = wall_sec
        self._log_path = log_path
        self._fired = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._wall <= 0:
            return
        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="radar-cycle-watchdog",
        )
        self._thread.start()

    def _run(self) -> None:
        if self._stop.wait(self._wall):
            return
        _safe_close_browser_contexts()
        msg = f"{radar_timestamp()} цикл:watchdog:kill elapsed>{int(self._wall)}s"
        _append_log_line(self._log_path, msg, echo=True)
        self._fired.set()

    def check(self) -> None:
        if self._fired.is_set():
            raise CycleWatchdogError(f"cycle watchdog after {int(self._wall)}s")

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)


_LISTING_ERRORS = (
    FlListingError,
    KworkListingError,
    VcRuListingError,
    HabrCareerListingError,
    YoudoListingError,
    FreelanceRuListingError,
    FreelancejobListingError,
    PchyolListingError,
)

_P1_WEB_SOURCES: tuple[tuple[str, Callable[[Config], list[ListingProject]]], ...] = (
    ("youdo", fetch_youdo_listing),
    ("freelance_ru", fetch_freelance_ru_listing),
    ("freelancejob", fetch_freelancejob_listing),
    ("pchyol", fetch_pchyol_listing),
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


def _safe_close_browser_contexts() -> None:
    """O190 t0j: never abort radar cycle on Playwright teardown."""
    try:
        from exchange_browser_fetch import close_all_browser_contexts

        close_all_browser_contexts()
    except Exception as exc:
        logger = __import__("logging").getLogger(__name__)
        logger.warning("close_all_browser_contexts skipped: %s", exc)


def _commit_youdo_fetch_gate(
    cfg: Config,
    storage: ProjectStorage,
    stats: SourceCycleStats,
    *,
    ts: str,
) -> None:
    """O190 t0j: fetch_end + health:youdo before slow post-fetch steps."""
    if stats.fetch_error or stats.parsed_cards < 50:
        return
    _record_source_health(storage, "youdo", stats, ts=ts, cfg=cfg)
    health = load_health(storage, "youdo")
    append_health_log(
        cfg.radar_log_path,
        format_health_log_line("youdo", health, fetch_ok=True),
    )


def _fetch_source(
    label: str,
    fetch_fn: Callable[..., list[ListingProject]],
    cfg: Config,
    errors: list[str],
    stats: SourceCycleStats | None = None,
    *,
    storage: ProjectStorage | None = None,
) -> list[ListingProject] | None:
    if storage is not None:
        flag_key = f"restart_source_{label.strip().lower()}"
        if storage.get_setting(flag_key, "0") == "1":
            if label.strip().lower() == "youdo":
                from youdo_parser import youdo_hard_reset

                youdo_hard_reset(reason="restart_source_flag", storage=storage)
            else:
                _safe_close_browser_contexts()
            storage.set_setting(flag_key, "0")
            _append_log_line(
                cfg.radar_log_path,
                f"fetch:{label} restart_source → browser contexts closed",
                echo=True,
            )

    wall = _radar_source_fetch_wall_sec(label)

    def _run_fetch() -> list[ListingProject] | None:
        try:
            kwargs: dict[str, object] = {}
            if storage is not None and "storage" in inspect.signature(fetch_fn).parameters:
                kwargs["storage"] = storage
            return fetch_fn(cfg, **kwargs)
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

    pool = ThreadPoolExecutor(max_workers=1)
    fut = pool.submit(_run_fetch)
    try:
        return fut.result(timeout=wall)
    except FuturesTimeout:
        if (label or "").strip().lower() == "youdo":
            try:
                from exchange_browser_fetch import youdo_browser_teardown

                youdo_browser_teardown()
            except Exception:
                _safe_close_browser_contexts()
        else:
            _safe_close_browser_contexts()
        msg = f"source wall-clock {int(wall)}s"
        errors.append(f"{label}:fetch:{msg}")
        if stats is not None:
            stats.fetch_error = msg
        _append_log_line(
            cfg.radar_log_path,
            f"fetch:{label} TIMEOUT → wall-clock kill after {int(wall)}s",
            echo=True,
        )
        return None
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def _log_source_line(log_path: Path, stats: SourceCycleStats) -> None:
    _append_log_line(log_path, stats.format_line(), echo=True)


def _record_source_health(
    storage: ProjectStorage,
    source: str,
    stats: SourceCycleStats,
    *,
    ts: str,
    cfg: Config | None = None,
) -> None:
    if source == "youdo":
        try:
            from youdo_parser import youdo_consume_cycle_skip

            if youdo_consume_cycle_skip(storage) == "fetch_every_n":
                return
        except Exception:
            pass

    ok = not stats.fetch_error
    parsed_cards = stats.parsed_cards if ok and stats.parsed_cards >= 0 else None
    if source == "youdo" and ok and parsed_cards == 0:
        ok = False
        stats.fetch_error = stats.fetch_error or "antibot SPA shell parsed=0"
    health = record_fetch(
        storage,
        source,
        ok=ok,
        error_msg=stats.fetch_error,
        downloaded=stats.downloaded,
        new_ids=stats.new_ids,
        parsed_cards=parsed_cards,
        ts=ts,
    )
    if source == "youdo" and cfg is not None:
        try:
            from youdo_parser import log_youdo_fetch_end

            log_youdo_fetch_end(cfg, stats, health)
        except Exception:
            pass
    try:
        from exchange_trace import log_exchange_trace

        log_exchange_trace(
            source,
            stage="cycle_end",
            parsed=stats.parsed_cards if stats.parsed_cards >= 0 else "",
            fresh=stats.downloaded,
            new_ids=stats.new_ids,
            err=stats.fetch_error or "",
        )
    except Exception:
        pass
    maybe_send_red_alert(storage, source, health, fetch_failed=not ok)


def _log_cycle_health_lines(
    cfg: Config,
    storage: ProjectStorage,
    summary: CycleSummary,
    *,
    lag_report: dict[str, dict[str, float | int]] | None = None,
) -> None:
    for sid, st in summary.sources.items():
        health = load_health(storage, sid)
        lag_row = (lag_report or {}).get(sid) or {}
        p50 = float(lag_row.get("ingest_p50_sec", 0.0) or 0.0)
        lag_min = int(p50 // 60) if p50 > 0 else None
        line = format_health_log_line(
            sid,
            health,
            fetch_ok=not st.fetch_error,
            ingest_lag_p50_min=lag_min,
        )
        append_health_log(cfg.radar_log_path, line)


def _should_fetch_secondary(storage: ProjectStorage) -> bool:
    """O99: secondary (YouDo, Пчёл, …) реже — не блокирует hot FL/Kwork."""
    every = max(1, int(os.getenv("SECONDARY_FETCH_EVERY_N_CYCLES", "1") or "1"))
    if every <= 1:
        return True
    raw = storage.get_setting("main_cycle_count", "0") or "0"
    try:
        n = int(raw) + 1
    except ValueError:
        n = 1
    storage.set_setting("main_cycle_count", str(n))
    return (n - 1) % every == 0


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
    watchdog = _CycleWatchdog(_radar_cycle_wall_sec(), cfg.radar_log_path)
    watchdog.start()

    try:
        _run_cycle_body(
            cfg,
            storage,
            word_filter,
            pg,
            ts=ts,
            cycle_t0=cycle_t0,
            errors=errors,
            summary=summary,
            enabled_sources=enabled_sources,
            watchdog=watchdog,
        )
    finally:
        from exchange_browser_fetch import cleanup_stale_browser_processes

        _safe_close_browser_contexts()
        try:
            cleanup_stale_browser_processes()
        except Exception:
            pass
        watchdog.stop()


def _run_cycle_body(
    cfg: Config,
    storage: ProjectStorage,
    word_filter: ListingWordFilter,
    pg: NeonLeadStorage | None,
    *,
    ts: str,
    cycle_t0: float,
    errors: list[str],
    summary: CycleSummary,
    enabled_sources: set[str],
    watchdog: _CycleWatchdog,
) -> None:
    """Inner site cycle — separated for O160 watchdog try/finally."""

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

    if "fl" in enabled_sources:
        stats_fl = summary.ensure("fl")
        fl_projects = _fetch_source(
            "fl", fetch_listing_projects, cfg, errors, stats_fl, storage=storage
        )
        if fl_projects is None:
            for err in errors:
                if err.startswith("fl:fetch:"):
                    stats_fl.fetch_error = err.split(":", 2)[-1][:120]
                    break
        _tg_poll_if_due(cfg, storage, tg_poll_state)
        if fl_projects is not None:
            stats_fl.parsed_cards = take_listing_metrics("fl")[0]
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
        _record_source_health(storage, "fl", stats_fl, ts=ts, cfg=cfg)

    watchdog.check()
    _tg_poll_if_due(cfg, storage, tg_poll_state)

    if "kwork" in enabled_sources:
        stats_kwork = summary.ensure("kwork")
        if cfg.kwork_projects_url:
            kwork_projects = _fetch_source(
                "kwork",
                fetch_kwork_listing_projects,
                cfg,
                errors,
                stats_kwork,
                storage=storage,
            )
            if kwork_projects is not None:
                stats_kwork.parsed_cards = take_listing_metrics("kwork")[0]
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
        _record_source_health(storage, "kwork", stats_kwork, ts=ts, cfg=cfg)

    watchdog.check()
    _tg_poll_if_due(cfg, storage, tg_poll_state)

    if l1_pool is not None:
        l1_hot = l1_pool.drain(shutdown=False)
        if l1_hot > 0:
            _append_log_line(
                cfg.radar_log_path,
                f"pipeline:L1 hot done={l1_hot} workers={cfg.l1_max_workers}",
                echo=True,
            )

    fetch_secondary = _should_fetch_secondary(storage)
    watchdog.check()
    if not fetch_secondary:
        _append_log_line(
            cfg.radar_log_path,
            "fetch:secondary skip (SECONDARY_FETCH_EVERY_N_CYCLES)",
            echo=False,
        )

    for source_label, fetch_fn in _P1_WEB_SOURCES:
        if source_label not in enabled_sources:
            continue
        if not fetch_secondary:
            continue
        stats_web = summary.ensure(source_label)
        _tg_poll_if_due(cfg, storage, tg_poll_state)
        web_projects = _fetch_source(
            source_label, fetch_fn, cfg, errors, stats_web, storage=storage
        )
        if web_projects is not None:
            stats_web.parsed_cards = len(web_projects)
            if source_label == "youdo":
                _commit_youdo_fetch_gate(cfg, storage, stats_web, ts=ts)
            if source_label == "pchyol":
                web_projects = filter_new_pchyol_projects(web_projects, storage)
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
            if source_label == "youdo":
                _append_log_line(
                    cfg.radar_log_path,
                    f"youdo:ingest done={stats_web.downloaded} new={n}",
                    echo=True,
                )
        _log_source_line(cfg.radar_log_path, stats_web)
        _record_source_health(storage, source_label, stats_web, ts=ts, cfg=cfg)
        watchdog.check()

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

    tools_batch = int(os.getenv("TOOLS_BATCH_PER_CYCLE", "8") or "8")
    if (
        os.getenv("TOOLS_BACKLOG_DRAIN", "0").strip().lower() in ("1", "true", "yes")
        and pg is not None
        and cfg.ai_active
        and cfg.radar_profile == "site"
    ):
        tools_n = drain_tools_backlog(cfg, pg, errors=errors, limit=tools_batch)
        if tools_n > 0:
            _append_log_line(
                cfg.radar_log_path,
                f"конвейер:tools={tools_n} (batch≤{tools_batch})",
                echo=True,
            )

    _maybe_run_delist_batch(cfg, pg, storage, errors)
    _maybe_run_feed_retention_batch(cfg, pg, storage, errors)
    _maybe_run_trial_maintenance(cfg, storage, errors)

    _collect_misc_errors(errors, summary)
    summary.sync_neon_from_globals()
    summary.cycle_sec = max(0.0, time.monotonic() - cycle_t0)
    if cfg.radar_profile == "site":
        commit_site_rollup_cycle(summary)
    record_cycle_summary(storage, summary)
    if cfg.radar_profile == "site":
        from healthchecks import ping_after_site_cycle

        ping_after_site_cycle(summary, storage)
    storage.set_setting("status_main_last_cycle_at", summary.ts)
    for src in sorted(enabled_sources):
        st = summary.sources.get(src)
        ok = bool(st and not st.fetch_error)
        storage.set_setting(f"status_fetch_ok_{src}", "1" if ok else "0")
    lag_report: dict[str, dict[str, float | int]] | None = None
    if pg is not None and pg.enabled:
        snap = pg.ingest_ops_snapshot(errors)
        lag_report = pg.ingest_lag_report(errors=errors)
        newest = ""
        newest_gap = None
        for src in ("fl", "kwork", "tg"):
            row = snap.get(src) or {}
            ins_ts = str(row.get("last_insert_at", "")).strip()
            gap = int(row.get("last_insert_gap_sec", 0) or 0)
            if ins_ts and (newest_gap is None or gap < newest_gap):
                newest = ins_ts
                newest_gap = gap
            if src == "tg" and gap <= GREEN_MAX_MIN * 60:
                record_ok_ping(storage, "tg", ts=summary.ts)
        if newest:
            storage.set_setting("status_neon_last_insert_at", newest)
        for src, row in snap.items():
            gap = int(row.get("last_insert_gap_sec", 0) or 0)
            if gap <= GREEN_MAX_MIN * 60 and src in summary.sources:
                record_ok_ping(storage, src, ts=summary.ts)

    _log_cycle_health_lines(cfg, storage, summary, lag_report=lag_report)

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


def _maybe_run_trial_maintenance(
    cfg: Config,
    storage: ProjectStorage,
    errors: list[str],
) -> None:
    stats = run_trial_maintenance(cfg, storage, errors=errors)
    if stats.get("expired") or stats.get("reminders"):
        _append_log_line(
            cfg.radar_log_path,
            f"trial: expired={stats.get('expired', 0)} reminders={stats.get('reminders', 0)}",
            echo=True,
        )


def _maybe_run_delist_batch(
    cfg: Config,
    pg: NeonLeadStorage | None,
    storage: ProjectStorage,
    errors: list[str],
) -> None:
    stats = maybe_run_delist_batch(cfg, pg, storage, errors)
    if stats and (stats["checked"] or stats["delisted"]):
        _append_log_line(
            cfg.radar_log_path,
            f"delist: checked={stats['checked']} delisted={stats['delisted']} "
            f"skipped={stats['skipped']}",
            echo=True,
        )


def _maybe_run_feed_retention_batch(
    cfg: Config,
    pg: NeonLeadStorage | None,
    storage: ProjectStorage,
    errors: list[str],
) -> None:
    if cfg.radar_profile != "site" or pg is None or not pg.enabled:
        return
    now = time.time()
    raw = storage.get_setting(_FEED_RETENTION_LAST_RUN_KEY, "0").strip()
    try:
        last = float(raw)
    except ValueError:
        last = 0.0
    if now - last < delist_interval_sec():
        return
    stats = run_feed_retention_batch(pg, errors=errors)
    storage.set_setting(_FEED_RETENTION_LAST_RUN_KEY, str(now))
    if stats["hidden"]:
        _append_log_line(
            cfg.radar_log_path,
            f"feed_retention: hidden={stats['hidden']}",
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
    from config import database_url_kind, require_database_url

    try:
        db_kind = database_url_kind(require_database_url())
    except Exception:
        db_kind = database_url_kind()
    _echo(f"=== RawLead [{cfg.radar_profile}] ({radar_timestamp()}, Иркутск) db={db_kind} ===")
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
    from exchange_browser_fetch import cleanup_stale_browser_processes

    n_killed = cleanup_stale_browser_processes()
    if n_killed:
        _append_log_line(
            cfg.radar_log_path,
            f"{ts0} browser:cleanup killed={n_killed}",
            echo=True,
        )
    if cfg.radar_profile == "site":
        reset_site_rollup_emit_clock()

    _sd_notify("READY=1")

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
        except CycleWatchdogError as exc:
            ts = radar_timestamp()
            from healthchecks import ping_cycle_overrun

            ping_cycle_overrun()
            _log_failed_cycle(cfg.radar_log_path, storage, ts, exc)
        except Exception as exc:
            ts = radar_timestamp()
            _log_failed_cycle(cfg.radar_log_path, storage, ts, exc)

        _sd_notify("WATCHDOG=1")
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
