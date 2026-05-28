"""Legacy: Neon (read) → FILTERS_LEGACY → ИИ → @FLPARSINGBOT. Биржи пишет Site."""

from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    import msvcrt
else:
    msvcrt = None  # type: ignore

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CURSOR_PATH = _PROJECT_ROOT / "data" / "legacy_neon_cursor.json"
_consumer_lock_fh = None

from config import (
    Config,
    apply_profile_argv,
    legacy_neon_consumer_enabled,
    load_config,
    load_radar_env,
    radar_lock_path,
    radar_timestamp,
)
from filters import ListingWordFilter, default_listing_filter
from lead_pipeline import process_legacy_neon_listing, short_err
from radar_status import reset_neon_consumer_session, record_neon_consumer_cycle
from pg_storage import NeonLeadStorage, pg_storage_from_config
from storage import ProjectStorage, storage_from_config

from bot_poll import try_poll_commands
from health_check import run_health_check
from telegram_control import send_control_panel


def _consumer_lock_path() -> Path:
    apply_profile_argv()
    load_radar_env()
    return radar_lock_path("neon_legacy")


def _release_consumer_lock() -> None:
    global _consumer_lock_fh
    lock_path = _consumer_lock_path()
    if _consumer_lock_fh is not None:
        try:
            if msvcrt is not None:
                _consumer_lock_fh.seek(0)
                msvcrt.locking(_consumer_lock_fh.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        try:
            _consumer_lock_fh.close()
        except OSError:
            pass
        _consumer_lock_fh = None
    try:
        lock_path.unlink(missing_ok=True)
    except OSError:
        pass


def _acquire_consumer_lock() -> bool:
    global _consumer_lock_fh
    lock_path = _consumer_lock_path()
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
    _consumer_lock_fh = fh
    return True


def _echo(line: str) -> None:
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        pass


def _append_log_line(log_path: Path, line: str, *, echo: bool = False) -> None:
    log_path = Path(log_path)
    parent = log_path.parent
    if str(parent) not in ("", "."):
        parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line.rstrip("\n") + "\n")
    if echo:
        _echo(line.rstrip("\n"))


def _load_cursor(pg: NeonLeadStorage, errors: list[str]) -> int:
    if _CURSOR_PATH.is_file():
        try:
            raw = json.loads(_CURSOR_PATH.read_text(encoding="utf-8"))
            return int(raw.get("last_id", 0))
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    last_id = pg.max_lead_id(errors)
    _save_cursor(last_id)
    return last_id


def _save_cursor(last_id: int) -> None:
    _CURSOR_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CURSOR_PATH.write_text(
        json.dumps({"last_id": int(last_id)}, ensure_ascii=False),
        encoding="utf-8",
    )


def _poll_tg_commands(cfg: Config, storage: ProjectStorage) -> None:
    try:
        try_poll_commands(cfg, storage)
    except Exception as exc:
        _append_log_line(
            cfg.radar_log_path,
            f"{radar_timestamp()} тг:poll:{short_err(exc)}",
        )


def _sleep_with_tg_poll(
    cfg: Config, storage: ProjectStorage, seconds: int
) -> None:
    end = time.monotonic() + max(1, seconds)
    while time.monotonic() < end:
        _poll_tg_commands(cfg, storage)
        sleep_sec = max(0.0, min(2.0, end - time.monotonic()))
        if sleep_sec == 0.0:
            _append_log_line(
                cfg.radar_log_path,
                f"{radar_timestamp()} neon:tight-loop — sleep_sec = 0",
                echo=True,
            )
            sleep_sec = 0.05
        time.sleep(sleep_sec)


def run_neon_cycle(
    cfg: Config,
    storage: ProjectStorage,
    word_filter: ListingWordFilter,
    pg: NeonLeadStorage,
) -> None:
    errors: list[str] = []
    after_id = _load_cursor(pg, errors)
    rows = pg.fetch_exchange_leads_after(after_id, limit=40, errors=errors)
    ts = radar_timestamp()
    if not rows:
        _append_log_line(
            cfg.radar_log_path,
            f"{ts} neon:цикл │ выборка 0 │ новых 0 │ в бот 0",
            echo=True,
        )
        for err in errors:
            _append_log_line(cfg.radar_log_path, f"{ts} neon:ошибка {err}")
        return

    new_ids = 0
    to_bot = 0
    max_id = after_id
    for row in rows:
        max_id = max(max_id, row.lead_id)
        project = row.to_listing()
        was_new, notified = process_legacy_neon_listing(
            project,
            storage,
            word_filter,
            cfg,
            errors=errors,
        )
        if was_new:
            new_ids += 1
        if notified:
            to_bot += 1

    _save_cursor(max_id)
    record_neon_consumer_cycle(
        storage,
        sample_size=len(rows),
        new_ids=new_ids,
        to_bot=to_bot,
    )
    _append_log_line(
        cfg.radar_log_path,
        f"{ts} neon:цикл │ выборка {len(rows):3d} │ новых {new_ids:3d} │ в бот {to_bot:3d}",
        echo=True,
    )
    for err in errors:
        if err.startswith("pg:"):
            continue
        if " skip:" in err:
            _append_log_line(cfg.radar_log_path, f"{ts} neon:skip {err}")
            continue
        _append_log_line(cfg.radar_log_path, f"{ts} neon:прочее {err}")


def main() -> None:
    apply_profile_argv()
    load_radar_env()
    if not legacy_neon_consumer_enabled():
        print(
            "neon_legacy_consumer: RADAR_EXCHANGES_ENABLED=1 — биржи на Site; "
            "legacy не запускает consumer",
            flush=True,
        )
        raise SystemExit(0)

    cfg = load_config()
    pg = pg_storage_from_config(cfg)
    if pg is None or not pg.enabled:
        print(
            "neon_legacy_consumer: нужен DATABASE_URL (read Neon с Site)",
            flush=True,
        )
        raise SystemExit(1)

    storage = storage_from_config(cfg)
    word_filter = default_listing_filter()
    interval_sec = max(1, cfg.poll_interval_minutes * 60)

    _echo(f"=== RawLead Neon [{cfg.radar_profile}] ({radar_timestamp()}, Иркутск) ===")
    _echo(f"Лог: {cfg.radar_log_path.resolve()}")
    _echo(f"Курсор: {_CURSOR_PATH.resolve()}")
    _echo(
        f"Интервал: {cfg.poll_interval_minutes} мин | "
        f"ИИ: {'вкл' if cfg.ai_active else 'выкл'} | "
        f"Фильтр: {'широкий' if cfg.filter_wide else 'узкий'} | "
        f"Neon: read-only"
    )
    _echo("Окно не закрывать. Ctrl+C = стоп.")
    _echo("---")

    ts0 = radar_timestamp()
    reset_neon_consumer_session(storage)
    _append_log_line(cfg.radar_log_path, f"{ts0} neon:старт", echo=True)

    try:
        send_control_panel(cfg)
    except Exception as exc:
        _append_log_line(
            cfg.radar_log_path,
            f"{radar_timestamp()} тг:панель:{short_err(exc)}",
        )

    while True:
        _poll_tg_commands(cfg, storage)

        try:
            run_health_check(cfg, storage, log_path=cfg.radar_log_path, force=False)
        except Exception as exc:
            _append_log_line(
                cfg.radar_log_path,
                f"{radar_timestamp()} здравье:ошибка {short_err(exc)}",
            )

        if storage.is_radar_paused():
            ts = radar_timestamp()
            _append_log_line(cfg.radar_log_path, f"{ts} neon:пауза", echo=True)
            _sleep_with_tg_poll(cfg, storage, random.randint(10, 15))
            continue

        try:
            run_neon_cycle(cfg, storage, word_filter, pg)
        except Exception as exc:
            ts = radar_timestamp()
            _append_log_line(
                cfg.radar_log_path,
                f"{ts} neon:цикл:ошибка {short_err(exc)}",
                echo=True,
            )

        _sleep_with_tg_poll(cfg, storage, interval_sec)


if __name__ == "__main__":
    if not _acquire_consumer_lock():
        try:
            cfg = load_config()
            log_path = cfg.radar_log_path
        except Exception:
            log_path = _PROJECT_ROOT / "data" / "radar_legacy.log"
        msg = f"{radar_timestamp()} neon:дубль:второй consumer — уже работает"
        print("[!] Второй neon_legacy_consumer — уже запущен", flush=True)
        _append_log_line(log_path, msg)
        raise SystemExit(1)
    try:
        main()
    finally:
        _release_consumer_lock()
