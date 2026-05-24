"""Один экземпляр main.py / tg_main.py — убить чужие процессы uisness (Windows)."""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

import psutil

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_LOG = _PROJECT_ROOT / "data" / "radar.log"

# role=main | tg_main — только свой скрипт (uisness в пути опционален: system pythonw + rel path)
_ROLE_MATCH = {
    "main": r"(?:uisness[\\/].*)?src[\\/]main\.py",
    "tg_main": r"(?:uisness[\\/].*)?scripts[\\/]tg_main\.py",
}
# Пульт /stop и kill без role — все воркеры радара
_ALL_MATCH = (
    r"(?:uisness[\\/].*)?(?:src[\\/]main\.py|scripts[\\/]tg_main\.py|"
    r"scripts[\\/]tg_join_daemon\.py|scripts[\\/]tg_join_queue)"
)
# CommandLine без полного пути (system pythonw + scripts\radar_control.py)
_RADAR_CONTROL_MATCH = r"radar_control\.py"


def _iter_python_procs():
    """Все python/pythonw процессы на Windows."""
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (proc.info["name"] or "").lower()
            if name in ("python.exe", "pythonw.exe"):
                yield proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


def _cmd_str(proc) -> str:
    """Cmdline как строка для regex-матча."""
    try:
        return " ".join(proc.cmdline())
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return ""


def _kill_matching(pattern: str, except_pid: int | None = None) -> list[int]:
    killed: list[int] = []
    rx = re.compile(pattern, re.IGNORECASE)
    for proc in _iter_python_procs():
        if except_pid is not None and proc.pid == except_pid:
            continue
        if rx.search(_cmd_str(proc)):
            try:
                proc.kill()
                killed.append(proc.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    return killed


def count_radar_workers() -> tuple[int, int]:
    """Число процессов main.py и tg_main.py (Windows)."""
    if sys.platform != "win32":
        return 0, 0
    main_rx = re.compile(_ROLE_MATCH["main"], re.IGNORECASE)
    tg_rx = re.compile(_ROLE_MATCH["tg_main"], re.IGNORECASE)
    mc = tc = 0
    for proc in _iter_python_procs():
        cmd = _cmd_str(proc)
        if main_rx.search(cmd):
            mc += 1
        if tg_rx.search(cmd):
            tc += 1
    return mc, tc


def log_duplicate_kills(
    killed: list[int],
    *,
    log_path: Path | None = None,
    source: str = "guard",
) -> None:
    if not killed:
        return
    path = Path(log_path) if log_path else _DEFAULT_LOG
    try:
        from config import radar_timestamp
    except Exception:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
    else:
        ts = radar_timestamp()
    pids = ",".join(str(p) for p in killed)
    line = f"{ts} радар:дубль:убиты PID {pids} ({source})"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)


def kill_all_radar_control() -> list[int]:
    """Завершить все radar_control (перед чистым стартом из bat)."""
    if sys.platform != "win32":
        return []
    killed = _kill_matching(_RADAR_CONTROL_MATCH)
    if killed:
        log_duplicate_kills(killed, source="radar_control:all")
    return killed


def kill_other_radar_control(*, except_pid: int | None = None) -> list[int]:
    """Завершить чужие radar_control.py (зависший API на :18765)."""
    if sys.platform != "win32":
        return []
    pid = int(except_pid if except_pid is not None else os.getpid())
    killed = _kill_matching(_RADAR_CONTROL_MATCH, except_pid=pid)
    if killed:
        log_duplicate_kills(killed, source="radar_control:other")
    return killed


def kill_duplicate_radar_workers(
    *,
    role: str | None = None,
    except_pid: int | None = None,
    log_path: Path | None = None,
    log_source: str = "guard",
) -> list[int]:
    """Завершить чужие uisness main/tg_main/join. role — только свой скрипт; без role — все воркеры."""
    if sys.platform != "win32":
        return []
    pid = int(except_pid if except_pid is not None else os.getpid())
    if role is not None:
        match = _ROLE_MATCH.get(role)
        if not match:
            return []
    else:
        match = _ALL_MATCH
    killed = _kill_matching(match, except_pid=pid)
    if killed:
        log_duplicate_kills(killed, log_path=log_path, source=log_source)
    return killed


def wait_radar_workers_stopped(*, timeout_sec: float = 8.0) -> bool:
    """Дождаться 0 main и 0 tg_main (после stop / перед spawn)."""
    if sys.platform != "win32":
        return True
    deadline = time.monotonic() + max(0.5, float(timeout_sec))
    while time.monotonic() < deadline:
        mc, tc = count_radar_workers()
        if mc == 0 and tc == 0:
            return True
        kill_duplicate_radar_workers(log_source="wait")
        time.sleep(0.35)
    mc, tc = count_radar_workers()
    return mc == 0 and tc == 0
