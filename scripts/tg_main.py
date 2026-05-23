"""Только мониторинг Telegram-чатов (фаза 1). Не заменяет python src/main.py."""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    import msvcrt
else:
    msvcrt = None  # type: ignore

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from bot_poll import try_poll_commands  # noqa: E402
from config import (  # noqa: E402
    load_config,
    load_tg_monitor_config,
    radar_timestamp,
    telethon_monitor_accounts,
)
from storage import storage_from_config  # noqa: E402
from health_check import (  # noqa: E402
    mark_tg_monitor_started,
    run_health_check,
    write_tg_monitor_pulse,
)
from radar_status import reset_tg_session_stats  # noqa: E402
from proxy_probe import wait_active_monitor_proxies_live  # noqa: E402
from tg_monitor import reconnect_delay_sec, run_monitor  # noqa: E402

_POLL_SEC = 2.0
_HEARTBEAT_SEC = 120.0
_TG_MAIN_LOCK = _ROOT / "data" / ".tg_main.lock"
_tg_main_lock_fh = None


def _release_single_instance() -> None:
    global _tg_main_lock_fh
    if _tg_main_lock_fh is not None:
        try:
            if msvcrt is not None:
                _tg_main_lock_fh.seek(0)
                msvcrt.locking(_tg_main_lock_fh.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        try:
            _tg_main_lock_fh.close()
        except OSError:
            pass
        _tg_main_lock_fh = None
    try:
        _TG_MAIN_LOCK.unlink(missing_ok=True)
    except OSError:
        pass


def _acquire_single_instance() -> bool:
    global _tg_main_lock_fh
    _TG_MAIN_LOCK.parent.mkdir(parents=True, exist_ok=True)
    try:
        fh = open(_TG_MAIN_LOCK, "a+b")
    except OSError:
        return True
    if msvcrt is not None:
        try:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            fh.close()
            print(
                "[!] Второй запуск tg_main — уже работает окно RawLead — TG",
                flush=True,
            )
            return False
    _tg_main_lock_fh = fh
    return True


def _append_log(log_path: Path, line: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line.rstrip("\n") + "\n")
    print(line.rstrip("\n"), flush=True)


def _poll_bot(cfg, storage, log_path: Path) -> None:
    ts = radar_timestamp()
    for line in try_poll_commands(cfg, storage):
        if "HTTP 409" in line:
            print(
                "[!] Telegram 409: два getUpdates с одним ботом "
                "(stop-radar.bat, закрой uvicorn/Cursor)",
                flush=True,
            )
        echo = line.startswith("тг:команда:") or "HTTP 409" in line or "тг:бот:" in line
        if echo:
            _append_log(log_path, f"{ts} {line}")


async def _bot_poll_loop(cfg, storage, log_path: Path) -> None:
    while True:
        await asyncio.to_thread(_poll_bot, cfg, storage, log_path)
        await asyncio.sleep(_POLL_SEC)


async def _write_pulse(cfg, storage, log_path: Path) -> None:
    ts = radar_timestamp()
    _append_log(log_path, f"{ts} тг:пульс")
    write_tg_monitor_pulse(storage)
    await asyncio.to_thread(
        run_health_check, cfg, storage, log_path=log_path, force=False
    )


async def _heartbeat_loop(cfg, storage, log_path: Path) -> None:
    while True:
        await _write_pulse(cfg, storage, log_path)
        await asyncio.sleep(_HEARTBEAT_SEC)


def _log_start() -> None:
    tg_cfg = load_tg_monitor_config()
    ts = radar_timestamp()
    print(f"=== TG-монитор {ts} (Иркутск) ===", flush=True)
    parts = [f"{ac.account}={len(ac.chat_ids)}" for ac in tg_cfg.accounts if ac.chat_ids]
    chats_line = ", ".join(parts) if parts else "0"
    print(
        f"Чатов: {chats_line} | переподключение день/ночь: "
        f"{tg_cfg.reconnect_sec}с / {tg_cfg.reconnect_night_sec}с",
        flush=True,
    )
    print("Кнопки Пауза/Статус: окно «биржи» ИЛИ это окно (общий бот)", flush=True)
    print("Ctrl+C = стоп. FL/Kwork: окно python src/main.py", flush=True)


async def _ensure_proxies_live(log_path: Path, tg_cfg) -> None:
    delay = float(reconnect_delay_sec(tg_cfg))

    def _log(msg: str) -> None:
        _append_log(log_path, f"{radar_timestamp()} {msg}")

    await asyncio.to_thread(
        wait_active_monitor_proxies_live,
        log_fn=_log,
        sleep_sec=delay,
    )


async def _loop() -> None:
    cfg = load_config()
    storage = storage_from_config(cfg)
    tg_cfg = load_tg_monitor_config()
    log_path = tg_cfg.radar_log_path

    ts = radar_timestamp()
    _append_log(log_path, f"{ts} тг:старт")
    mark_tg_monitor_started(storage)
    reset_tg_session_stats(storage, telethon_monitor_accounts())

    poll_task = asyncio.create_task(_bot_poll_loop(cfg, storage, log_path))
    beat_task = asyncio.create_task(_heartbeat_loop(cfg, storage, log_path))

    await _ensure_proxies_live(log_path, tg_cfg)

    try:
        while True:
            try:
                await run_monitor()
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                ts_err = radar_timestamp()
                delay = reconnect_delay_sec(tg_cfg)
                _append_log(
                    log_path,
                    f"{ts_err} тг:монитор ошибка: {exc!r}; переподключение через {delay}с",
                )
                await _ensure_proxies_live(log_path, tg_cfg)
    finally:
        poll_task.cancel()
        beat_task.cancel()
        _release_single_instance()


if __name__ == "__main__":
    _log_start()
    if not _acquire_single_instance():
        raise SystemExit(1)
    try:
        asyncio.run(_loop())
    except KeyboardInterrupt:
        print("TG-монитор остановлен.", flush=True)
    finally:
        _release_single_instance()
