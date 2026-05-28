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
    "main": (
        r"(?:uisness[\\/].*)?src[\\/](?:main|neon_legacy_consumer)\.py"
    ),
    "tg_main": r"(?:uisness[\\/].*)?scripts[\\/]tg_main\.py",
}
# Пульт /stop и kill без role — все воркеры радара
_ALL_MATCH = (
    r"(?:uisness[\\/].*)?(?:src[\\/](?:main|neon_legacy_consumer)\.py|"
    r"scripts[\\/]tg_main\.py|scripts[\\/]tg_join_daemon\.py|"
    r"scripts[\\/]tg_join_queue)"
)
_NEON_CONSUMER_MATCH = r"neon_legacy_consumer\.py"
# CommandLine без полного пути (system pythonw + scripts\radar_control.py)
_RADAR_CONTROL_MATCH = r"radar_control\.py"
# Пульт spawn'ит только .venv\Scripts\python.exe — system/Cursor воркеры = дубль
_VENV_EXE = re.compile(
    r"\.venv[\\/](?:Scripts[\\/]python(?:w)?\.exe|bin/python(?:3(?:\.\d+)?)?)",
    re.IGNORECASE,
)
_PROFILE_ARG = re.compile(r"--profile\s+(legacy|site)", re.IGNORECASE)


def _profile_from_cmd(cmd: str) -> str:
    m = _PROFILE_ARG.search(cmd)
    if m:
        return m.group(1).casefold()
    return "legacy"


def _current_profile() -> str:
    from config import load_radar_env, radar_profile

    load_radar_env()
    return radar_profile()


def _iter_python_procs():
    """Все python/pythonw (Windows) или python/python3 (Linux) процессы."""
    if sys.platform == "win32":
        names = frozenset(("python.exe", "pythonw.exe"))
    else:
        names = frozenset(("python", "python3"))
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (proc.info["name"] or "").lower()
            if name in names:
                yield proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


def _cmd_str(proc) -> str:
    """Cmdline как строка для regex-матча."""
    try:
        return " ".join(proc.cmdline())
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return ""


def _is_venv_interpreter(cmd: str) -> bool:
    return bool(_VENV_EXE.search(cmd))


def _is_project_radar_cmd(cmd: str) -> bool:
    """main/tg_main из корня репо — воркер пульта, даже если exe не .venv\\Scripts\\python."""
    if not cmd:
        return False
    base = re.escape(str(_PROJECT_ROOT))
    main_rx = re.compile(
        rf"{base}[\\/]src[\\/](?:main|neon_legacy_consumer)\.py",
        re.IGNORECASE,
    )
    tg_rx = re.compile(rf"{base}[\\/]scripts[\\/]tg_main\.py", re.IGNORECASE)
    return bool(main_rx.search(cmd) or tg_rx.search(cmd))


def _is_trusted_radar_worker(cmd: str) -> bool:
    return _is_venv_interpreter(cmd) or _is_project_radar_cmd(cmd)


def _is_real_radar_worker(cmd: str) -> bool:
    """Дочерний процесс venv-shim: system/home python + скрипт из корня проекта."""
    return _is_project_radar_cmd(cmd) and not _is_venv_interpreter(cmd)


def expand_spawn_keep_pids(pids: set[int] | None) -> set[int]:
    """popen.pid + дерево потомков (Windows: .venv exe → system python + main.py)."""
    expanded: set[int] = set(pids or ())
    for pid in list(expanded):
        if pid <= 0:
            continue
        try:
            proc = psutil.Process(pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        for child in proc.children(recursive=True):
            try:
                name = (child.name() or "").lower()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            if name in ("python.exe", "pythonw.exe"):
                expanded.add(child.pid)
    return expanded


def _kill_pids(pids: list[int]) -> list[int]:
    killed: list[int] = []
    for pid in pids:
        try:
            psutil.Process(pid).kill()
            killed.append(pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return killed


def _worker_groups(
    profile: str | None = None,
) -> tuple[list[tuple[int, bool, str]], list[tuple[int, bool, str]]]:
    """(pid, is_venv, cmdline) для main и tg_main одного RADAR_PROFILE."""
    want = profile or _current_profile()
    main_rx = re.compile(_ROLE_MATCH["main"], re.IGNORECASE)
    tg_rx = re.compile(_ROLE_MATCH["tg_main"], re.IGNORECASE)
    mains: list[tuple[int, bool, str]] = []
    tgs: list[tuple[int, bool, str]] = []
    for proc in _iter_python_procs():
        cmd = _cmd_str(proc)
        if not cmd:
            continue
        if _profile_from_cmd(cmd) != want:
            continue
        venv = _is_venv_interpreter(cmd)
        if main_rx.search(cmd):
            mains.append((proc.pid, venv, cmd))
        if tg_rx.search(cmd):
            tgs.append((proc.pid, venv, cmd))
    return mains, tgs


def _pick_worker_to_keep(
    group: list[tuple[int, bool, str]], keep_pids: set[int]
) -> int | None:
    if not group:
        return None

    def rank(item: tuple[int, bool, str]) -> tuple:
        pid, venv, cmd = item
        return (
            pid in keep_pids,
            venv,
            not _is_real_radar_worker(cmd),
            pid,
        )

    return max(group, key=rank)[0]


def _count_logical_group(group: list[tuple[int, bool, str]]) -> int:
    """Число воркеров для spawn-check: дубли venv+system или 2+ main не схлопываем."""
    if not group:
        return 0
    venv_n = sum(1 for _pid, venv, _cmd in group if venv)
    system_n = len(group) - venv_n
    if venv_n and system_n:
        return len(group)
    if len(group) > 1:
        return len(group)
    return 1


def kill_non_venv_radar_workers(
    *,
    keep_pids: set[int] | None = None,
    log_path: Path | None = None,
    log_source: str = "guard:non_venv",
    profile: str | None = None,
) -> list[int]:
    """Убить main/tg_main/radar_control вне .venv (дубль system+venv)."""
    if sys.platform != "win32":
        return []
    want_profile = profile or _current_profile()
    keep = keep_pids or set()
    mains, tgs = _worker_groups(want_profile)
    pids: list[int] = []
    for pid, _venv, cmd in mains + tgs:
        if pid in keep:
            continue
        if _is_venv_interpreter(cmd):
            continue
        pids.append(pid)
    ctrl_rx = re.compile(_RADAR_CONTROL_MATCH, re.IGNORECASE)
    for proc in _iter_python_procs():
        if proc.pid in keep:
            continue
        cmd = _cmd_str(proc)
        if not ctrl_rx.search(cmd):
            continue
        if _profile_from_cmd(cmd) != want_profile:
            continue
        if _is_venv_interpreter(cmd):
            continue
        pids.append(proc.pid)
    killed = _kill_pids(pids)
    if killed:
        log_duplicate_kills(killed, log_path=log_path, source=log_source)
    return killed


def trim_radar_workers_to_pair(
    *,
    keep_pids: set[int] | None = None,
    log_path: Path | None = None,
    log_source: str = "guard:trim",
) -> list[int]:
    """Оставить не больше 1 main и 1 tg; приоритет keep_pids, затем .venv, затем новый PID."""
    if sys.platform != "win32":
        return []
    keep = keep_pids or set()
    mains, tgs = _worker_groups()
    to_kill: list[int] = []
    for group in (mains, tgs):
        if len(group) <= 1:
            continue
        keep_pid = _pick_worker_to_keep(group, keep)
        if keep_pid is None:
            continue
        to_kill.extend(pid for pid, _, _ in group if pid != keep_pid)
    killed = _kill_pids(to_kill)
    if killed:
        log_duplicate_kills(killed, log_path=log_path, source=log_source)
    return killed


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


def count_radar_workers(profile: str | None = None) -> tuple[int, int]:
    """Число логических воркеров main.py и tg_main.py (Windows), один профиль."""
    if sys.platform != "win32":
        return 0, 0
    mains, tgs = _worker_groups(profile)
    return _count_logical_group(mains), _count_logical_group(tgs)


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


def kill_neon_legacy_consumers(
    *,
    profile: str | None = None,
    keep_pids: set[int] | None = None,
    log_path: Path | None = None,
    log_source: str = "guard:neon_consumer",
) -> list[int]:
    """Завершить neon_legacy_consumer (orphan pythonw после Stop). profile=None — все профили."""
    if sys.platform != "win32":
        return []
    keep = set(keep_pids or ())
    rx = re.compile(_NEON_CONSUMER_MATCH, re.IGNORECASE)
    killed: list[int] = []
    for proc in _iter_python_procs():
        if proc.pid in keep:
            continue
        cmd = _cmd_str(proc)
        if not rx.search(cmd):
            continue
        if profile is not None and _profile_from_cmd(cmd) != profile.casefold():
            continue
        try:
            proc.kill()
            killed.append(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if killed:
        log_duplicate_kills(killed, log_path=log_path, source=log_source)
    return killed


def kill_all_radar_control(*, profile: str | None = None) -> list[int]:
    """Завершить radar_control + main/tg_main/join профиля (любой python.exe)."""
    if sys.platform != "win32":
        return []
    want = profile or _current_profile()
    rx = re.compile(_RADAR_CONTROL_MATCH, re.IGNORECASE)
    killed: list[int] = []
    for proc in _iter_python_procs():
        cmd = _cmd_str(proc)
        if not rx.search(cmd):
            continue
        if _profile_from_cmd(cmd) != want:
            continue
        try:
            proc.kill()
            killed.append(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    # keep_pids={-1}: не оставлять os.getpid() — убить и system, и venv воркеры
    killed.extend(
        kill_duplicate_radar_workers(
            keep_pids={-1},
            profile=want,
            log_source="kill_all:workers",
        )
    )
    killed.extend(
        kill_non_venv_radar_workers(
            keep_pids={-1},
            profile=want,
            log_source="kill_all:non_venv",
        )
    )
    if want == "legacy":
        killed.extend(
            kill_neon_legacy_consumers(
                profile=want,
                keep_pids={-1},
                log_source="kill_all:neon_consumer",
            )
        )
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
    keep_pids: set[int] | None = None,
    log_path: Path | None = None,
    log_source: str = "guard",
    profile: str | None = None,
) -> list[int]:
    """Завершить чужие uisness main/tg_main/join. role — только свой скрипт; без role — все воркеры."""
    if sys.platform != "win32":
        return []
    want_profile = profile or _current_profile()
    keep = set(keep_pids or ())
    if except_pid is not None:
        keep.add(int(except_pid))
    elif not keep:
        keep.add(os.getpid())
    keep = expand_spawn_keep_pids(keep)
    if role is not None:
        match = _ROLE_MATCH.get(role)
        if not match:
            return []
    else:
        match = _ALL_MATCH
    rx = re.compile(match, re.IGNORECASE)
    killed: list[int] = []
    for proc in _iter_python_procs():
        if proc.pid in keep:
            continue
        cmd = _cmd_str(proc)
        if not rx.search(cmd):
            continue
        if _profile_from_cmd(cmd) != want_profile:
            continue
        try:
            proc.kill()
            killed.append(proc.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    if killed:
        log_duplicate_kills(killed, log_path=log_path, source=log_source)
    return killed


def release_stale_worker_locks() -> None:
    """Снять lock-файлы воркеров после stop/kill, если процессов не осталось."""
    if sys.platform != "win32":
        return
    time.sleep(0.25)
    from config import load_radar_env, radar_lock_path

    load_radar_env()
    mc, _tc = count_radar_workers()
    if mc == 0:
        for lock_name in ("main", "neon_legacy"):
            try:
                radar_lock_path(lock_name).unlink(missing_ok=True)
            except OSError:
                pass
    try:
        from health_check import try_release_stale_tg_main_lock

        try_release_stale_tg_main_lock()
    except Exception:
        pass


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
