"""HTTP API пульта RawLead: subprocess, lock, логи, статус.

Запуск: .venv\\Scripts\\python.exe scripts\\radar_control.py
Порт: RADAR_CONTROL_PORT (по умолчанию 18765)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

if sys.platform == "win32":
    import msvcrt

    CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
    fcntl = None  # type: ignore
else:
    msvcrt = None  # type: ignore
    CREATE_NO_WINDOW = 0
    try:
        import fcntl
    except ImportError:
        fcntl = None  # type: ignore

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

def _venv_python(root: Path) -> Path:
    if sys.platform == "win32":
        return root / ".venv" / "Scripts" / "python.exe"
    return root / ".venv" / "bin" / "python"


_PYTHON = _venv_python(_ROOT)
_LOG_JOIN = _ROOT / "data" / "tg_join.log"
_TAIL_LINES = 800
_DEFAULT_PORT = 18765
_WORKER_LOG_MAX_BYTES = 5 * 1024 * 1024
_LOCK_PATH: Path | None = None
_OPS_LOCK_PATH: Path | None = None
_LOG_RADAR: Path | None = None
_RADAR_PROFILE = "legacy"


def _init_profile_paths() -> None:
    global _LOCK_PATH, _OPS_LOCK_PATH, _LOG_RADAR, _RADAR_PROFILE
    from config import apply_profile_argv, load_config, load_radar_env, radar_lock_path

    apply_profile_argv()
    _RADAR_PROFILE = load_radar_env()
    _LOCK_PATH = radar_lock_path("radar_desktop")
    _OPS_LOCK_PATH = radar_lock_path("radar_ops")
    _LOG_RADAR = load_config().radar_log_path


from process_guard import (
    count_radar_workers,
    expand_spawn_keep_pids,
    kill_all_radar_control,
    kill_duplicate_radar_workers,
    kill_neon_legacy_consumers,
    kill_non_venv_radar_workers,
    wait_radar_workers_stopped,
)

_lock_fh = None
_ops_lock_fh = None


def _cors_allowed_origins() -> list[str]:
    raw = os.environ.get("RADAR_CORS_ORIGINS", "").strip()
    if not raw:
        return []
    return [o.strip() for o in raw.split(",") if o.strip()]


def _try_file_lock(fh, *, non_blocking: bool = True) -> bool:
    if msvcrt is not None:
        fh.seek(0)
        msvcrt.locking(
            fh.fileno(),
            msvcrt.LK_NBLCK if non_blocking else msvcrt.LK_LOCK,
            1,
        )
        return True
    if fcntl is not None:
        flags = fcntl.LOCK_EX
        if non_blocking:
            flags |= fcntl.LOCK_NB
        fcntl.flock(fh.fileno(), flags)
        return True
    return True


def _try_file_unlock(fh) -> None:
    if msvcrt is not None:
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
    elif fcntl is not None:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


@contextmanager
def _radar_ops_lock():
    """Межпроцессный lock: два radar_control не гоняют /start (4 воркера)."""
    global _ops_lock_fh
    assert _OPS_LOCK_PATH is not None
    _OPS_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = None
    try:
        fh = open(_OPS_LOCK_PATH, "a+b")
        _try_file_lock(fh)
        _ops_lock_fh = fh
        yield True
    except OSError:
        yield False
    finally:
        if fh is not None:
            try:
                _try_file_unlock(fh)
            except OSError:
                pass
            fh.close()
        _ops_lock_fh = None


def _acquire_single_instance() -> bool:
    global _lock_fh
    assert _LOCK_PATH is not None
    _LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        fh = open(_LOCK_PATH, "a+b")
    except OSError:
        return False
    if msvcrt is not None or fcntl is not None:
        try:
            fh.seek(0)
            _try_file_lock(fh)
        except OSError:
            fh.close()
            return False
    _lock_fh = fh
    return True


def _release_lock() -> None:
    global _lock_fh
    if _lock_fh is not None:
        try:
            _try_file_unlock(_lock_fh)
        except OSError:
            pass
        _lock_fh.close()
        _lock_fh = None


def _rotate_worker_log(path: Path) -> None:
    try:
        if path.is_file() and path.stat().st_size > _WORKER_LOG_MAX_BYTES:
            backup = path.with_suffix(path.suffix + ".1")
            if backup.is_file():
                backup.unlink()
            path.rename(backup)
    except OSError:
        pass


def _worker_log_path(log_key: str) -> Path:
    base = _LOG_RADAR or (_ROOT / "data" / "radar.log")
    return base.with_name(f"{base.stem}_{log_key}{base.suffix}")


def _hidden_popen(args: list[str], cwd: Path, *, log_key: str = "worker") -> subprocess.Popen:
    log_path = _worker_log_path(log_key)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _rotate_worker_log(log_path)
    kwargs: dict = {"cwd": str(cwd)}
    try:
        log_fh = open(log_path, "a", encoding="utf-8", buffering=1)
        kwargs["stdout"] = log_fh
        kwargs["stderr"] = log_fh
    except OSError:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        kwargs["startupinfo"] = si
        kwargs["creationflags"] = CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
    return subprocess.Popen(args, **kwargs)


def _log_start_failure(exc: BaseException) -> None:
    import traceback

    path = _ROOT / "data" / "radar_control_start.log"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} [{_RADAR_PROFILE}] ---\n")
            fh.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    except OSError:
        pass


def _release_stale_tg_lock() -> None:
    try:
        from process_guard import release_stale_worker_locks

        release_stale_worker_locks()
    except Exception:
        pass


def _release_stale_neon_consumer_lock() -> None:
    """Снять .neon_legacy_* lock если consumer не бежит (иначе spawn → exit 1 → стоп)."""
    try:
        from config import legacy_neon_consumer_enabled, radar_lock_path
        from process_guard import count_radar_workers

        if not legacy_neon_consumer_enabled():
            return
        mc, _ = count_radar_workers(_RADAR_PROFILE)
        if mc > 0:
            return
        radar_lock_path("neon_legacy").unlink(missing_ok=True)
    except Exception:
        pass


def _tail_utf8(path: Path, max_lines: int) -> str:
    if not path.is_file():
        return f"(файл пока нет: {path.name})\n"
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return f"Ошибка чтения: {exc}\n"
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    if len(lines) > max_lines:
        lines = lines[-max_lines:]
    return "\n".join(lines) + ("\n" if lines else "")


@dataclass
class ChildSpec:
    key: str
    label: str
    rel_script: str
    popen: subprocess.Popen | None = None

    def script_path(self) -> Path:
        return _ROOT / self.rel_script.replace("/", "\\")


@dataclass
class RadarController:
    children: list[ChildSpec] = field(default_factory=list)
    _starting: bool = False
    _ui_expanded: bool = False
    _ever_started: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def _tg_enabled(self) -> bool:
        from config import radar_tg_enabled

        return radar_tg_enabled()

    def _exchanges_enabled(self) -> bool:
        from config import radar_exchanges_enabled

        return radar_exchanges_enabled()

    def _neon_consumer_enabled(self) -> bool:
        from config import legacy_neon_consumer_enabled

        return legacy_neon_consumer_enabled()

    def _expected_workers(self) -> tuple[int, int]:
        """(main|neon_consumer, tg_main) — site: (1,1); legacy: (1,0) consumer."""
        exp_main = 0
        if self._exchanges_enabled():
            exp_main = 1
        elif self._neon_consumer_enabled():
            exp_main = 1
        exp_tg = 1 if self._tg_enabled() else 0
        return exp_main, exp_tg

    def _spawn_children(self) -> list[ChildSpec]:
        specs: list[ChildSpec] = []
        if self._exchanges_enabled():
            specs.append(ChildSpec("exchanges", "Биржи", "src/main.py"))
        elif self._neon_consumer_enabled():
            specs.append(
                ChildSpec("exchanges", "Neon", "src/neon_legacy_consumer.py")
            )
        if self._tg_enabled():
            specs.append(ChildSpec("tg", "TG", "scripts/tg_main.py"))
        return specs

    def _lamp_specs(self) -> list[ChildSpec]:
        specs = list(self.children)
        if not any(s.key == "exchanges" for s in specs):
            if self._exchanges_enabled():
                specs.insert(
                    0, ChildSpec("exchanges", "Биржи", "src/main.py")
                )
            elif self._neon_consumer_enabled():
                specs.insert(
                    0,
                    ChildSpec("exchanges", "Neon", "src/neon_legacy_consumer.py"),
                )
        if not any(s.key == "tg" for s in specs):
            specs.append(ChildSpec("tg", "TG", "scripts/tg_main.py"))
        return specs

    def _spawn_keep_pids(self) -> set[int]:
        keep: set[int] = set()
        for spec in self.children:
            if spec.popen is not None and spec.popen.poll() is None:
                keep.add(spec.popen.pid)
        return expand_spawn_keep_pids(keep)

    def __post_init__(self) -> None:
        if not self.children:
            self.children = self._spawn_children()

    def _is_alive(self, spec: ChildSpec) -> bool:
        if spec.key == "exchanges" and not self._exchanges_enabled():
            if not self._neon_consumer_enabled():
                return False
        if spec.popen is not None and spec.popen.poll() is None:
            return True
        mc, tc = count_radar_workers(_RADAR_PROFILE)
        if spec.key == "exchanges":
            return mc > 0
        if spec.key == "tg":
            return tc > 0
        return False

    def workers_running(self) -> bool:
        return any(self._is_alive(s) for s in self.children)

    def set_ui_expanded(self, expanded: bool) -> None:
        with self._lock:
            self._ui_expanded = expanded

    def start(self) -> dict:
        with _radar_ops_lock() as ops_ok:
            if not ops_ok:
                return {"ok": False, "error": "ops_lock_busy"}
            with self._lock:
                if self._starting:
                    return {"ok": False, "error": "already_starting"}
                if not _PYTHON.is_file():
                    return {
                        "ok": False,
                        "error": "no_venv",
                        "detail": f"Нет Python: {_PYTHON}",
                    }
                self.children = self._spawn_children()
                exp_main, exp_tg = self._expected_workers()
                mc, tc = count_radar_workers(_RADAR_PROFILE)
                popens_ok = all(
                    s.popen is not None and s.popen.poll() is None
                    for s in self.children
                )
                if popens_ok and mc >= exp_main and tc >= exp_tg:
                    return {"ok": False, "error": "already_running"}
                self._starting = True
                self._ever_started = True
                errors: list[str] = []
                try:
                    if self._tg_enabled():
                        try:
                            from config import load_config, telethon_monitor_accounts
                            from radar_status import reset_tg_session_stats
                            from storage import storage_from_config

                            reset_tg_session_stats(
                                storage_from_config(load_config()),
                                telethon_monitor_accounts(),
                            )
                        except Exception:
                            pass
                    _release_stale_neon_consumer_lock()
                    self._stop_unlocked(sweep_orphans=True)
                    kill_duplicate_radar_workers(
                        role="main",
                        log_source="radar_control:pre_spawn",
                        profile=_RADAR_PROFILE,
                    )
                    kill_duplicate_radar_workers(
                        role="tg_main",
                        log_source="radar_control:pre_spawn",
                        profile=_RADAR_PROFILE,
                    )
                    for spec in self.children:
                        script = spec.script_path()
                        if not script.is_file():
                            errors.append(f"Нет файла: {script}")
                            continue
                        try:
                            spec.popen = _hidden_popen(
                                [
                                    str(_PYTHON),
                                    "-u",
                                    str(script),
                                    "--profile",
                                    _RADAR_PROFILE,
                                ],
                                _ROOT,
                                log_key=spec.key,
                            )
                        except OSError as exc:
                            errors.append(f"{spec.label}: {exc}")
                            spec.popen = None
                    mc, tc = 0, 0
                    deadline = time.monotonic() + 15.0
                    spawn_failed = False
                    while time.monotonic() < deadline:
                        for spec in self.children:
                            if spec.popen is None:
                                continue
                            rc = spec.popen.poll()
                            if rc is not None:
                                errors.append(
                                    f"{spec.label}: процесс завершился (код {rc})"
                                )
                                spawn_failed = True
                        if spawn_failed:
                            break
                        mc, tc = count_radar_workers(_RADAR_PROFILE)
                        if mc == exp_main and tc == exp_tg:
                            break
                        time.sleep(0.25)
                    else:
                        if not spawn_failed:
                            errors.append(
                                f"воркеры main={mc} tg={tc} "
                                f"(ожидалось {exp_main}/{exp_tg})"
                            )
                            spawn_failed = True
                    workers_ok = mc == exp_main and tc == exp_tg
                    if not spawn_failed and not workers_ok:
                        popen_ok = all(
                            s.popen is not None and s.popen.poll() is None
                            for s in self.children
                        )
                        # Windows: neon_legacy_consumer жив, но psutil не успел в count
                        if popen_ok and exp_main >= 1 and mc == 0 and tc == exp_tg:
                            time.sleep(1.0)
                            mc, tc = count_radar_workers(_RADAR_PROFILE)
                            workers_ok = mc == exp_main and tc == exp_tg
                        if not workers_ok and popen_ok and exp_main == 1 and mc == 0:
                            workers_ok = True
                    if not spawn_failed and not workers_ok:
                        spawn_failed = True
                    # post_spawn kill убран: убивал только что поднятые venv-воркеры (регресс 2026-05-26)
                    if spawn_failed or not workers_ok:
                        self._stop_unlocked(sweep_orphans=True)
                    self._ui_expanded = False
                    return {"ok": len(errors) == 0, "errors": errors}
                except Exception as exc:
                    _log_start_failure(exc)
                    self._stop_unlocked(sweep_orphans=True)
                    return {
                        "ok": False,
                        "errors": [str(exc)],
                        "error": "start_exception",
                    }
                finally:
                    self._starting = False

    def _stop_unlocked(self, *, sweep_orphans: bool = True) -> dict:
        """Остановка без захвата lock (вызывать только из start/stop под lock)."""
        for spec in self.children:
            if spec.popen is not None and spec.popen.poll() is None:
                try:
                    spec.popen.terminate()
                except OSError:
                    pass
            spec.popen = None
        if sweep_orphans:
            keep = {-1}
            kill_duplicate_radar_workers(
                log_source="radar_control:stop",
                profile=_RADAR_PROFILE,
                keep_pids=keep,
            )
            kill_non_venv_radar_workers(
                log_source="radar_control:stop:non_venv",
                profile=_RADAR_PROFILE,
                keep_pids=keep,
            )
            if _RADAR_PROFILE == "legacy" or self._neon_consumer_enabled():
                kill_neon_legacy_consumers(
                    profile=_RADAR_PROFILE,
                    keep_pids=keep,
                    log_source="radar_control:stop:neon_consumer",
                )
            wait_radar_workers_stopped()
            _release_stale_tg_lock()
            _release_stale_neon_consumer_lock()
        self._ui_expanded = False
        return {"ok": True}

    def _notify_goodbye(self) -> None:
        try:
            from config import load_config
            from health_check import send_owner_text

            cfg = load_config()
            send_owner_text(cfg, "до связи")
        except Exception:
            pass

    def stop(self, silent: bool = False) -> dict:
        with _radar_ops_lock() as ops_ok:
            if not ops_ok:
                return {"ok": False, "error": "ops_lock_busy"}
            with self._lock:
                was_running = self.workers_running()
                result = self._stop_unlocked(sweep_orphans=True)
                if was_running and not silent:
                    self._notify_goodbye()
                return result

    def shutdown(self) -> dict:
        """Стоп воркеров + завершить API этого профиля (закрытие пульта ✕)."""
        result = self.stop(silent=True)
        profile = _RADAR_PROFILE

        def _kill_api() -> None:
            time.sleep(0.35)
            kill_all_radar_control(profile=profile)

        threading.Thread(target=_kill_api, daemon=True).start()
        return {**result, "shutting_down": True, "profile": profile}

    def lamp_state(self, spec: ChildSpec, workers_active: bool) -> str:
        if self._is_alive(spec):
            return "ok"
        if self._ever_started and (self._ui_expanded or workers_active):
            return "error"
        return "idle"

    def status_payload(self) -> dict:
        with self._lock:
            for spec in self.children:
                if spec.popen is not None and spec.popen.poll() is not None:
                    spec.popen = None
            workers = self.workers_running()
            if self._ui_expanded and not workers:
                self._ui_expanded = False
            lamps = []
            storage = None
            tg_enabled = self._tg_enabled()
            exchanges_enabled = self._exchanges_enabled()
            for spec in self._lamp_specs():
                if spec.key == "exchanges" and not exchanges_enabled and not self._neon_consumer_enabled():
                    lamps.append(
                        {
                            "key": "exchanges",
                            "label": spec.label,
                            "state": "idle",
                            "caption": "выкл",
                            "disabled": True,
                        }
                    )
                    continue
                if spec.key == "tg" and not tg_enabled:
                    lamps.append(
                        {
                            "key": "tg",
                            "label": "TG",
                            "state": "idle",
                            "caption": "выкл",
                            "disabled": True,
                        }
                    )
                    continue
                alive = self._is_alive(spec)
                if spec.key == "tg":
                    if alive:
                        try:
                            from config import load_config
                            from radar_status import tg_pult_lamp_state
                            from storage import storage_from_config

                            if storage is None:
                                storage = storage_from_config(load_config())
                            state, caption = tg_pult_lamp_state(
                                storage, process_alive=True
                            )
                        except Exception:
                            state, caption = "warn", "статус…"
                    elif self._ever_started and (self._ui_expanded or workers):
                        state, caption = "error", "нет"
                    else:
                        state, caption = "idle", ""
                else:
                    state = self.lamp_state(spec, workers)
                    caption = (
                        "работает"
                        if state == "ok"
                        else ("нет" if state == "error" else "")
                    )
                lamps.append(
                    {
                        "key": spec.key,
                        "label": spec.label,
                        "state": state,
                        "caption": caption,
                    }
                )
            payload: dict = {
                "running": workers,
                "ever_started": self._ever_started,
                "ui_expanded": self._ui_expanded,
                "tg_enabled": tg_enabled,
                "exchanges_enabled": exchanges_enabled,
                "profile": _RADAR_PROFILE,
                "lamps": lamps,
            }
            try:
                from config import load_config
                from radar_cycle_log import load_cycle_summary, load_site_rollup_line
                from radar_status import build_status_detail
                from storage import storage_from_config

                cfg = load_config()
                if storage is None:
                    storage = storage_from_config(cfg)
                detail = build_status_detail(cfg, storage)
                payload.update(detail)
                summary = load_cycle_summary(storage)
                if summary is not None and "last_cycle" not in payload:
                    payload["last_cycle"] = summary.to_storage_dict()
                rollup = load_site_rollup_line(storage)
                if rollup and not payload.get("site_rollup_10m"):
                    payload["site_rollup_10m"] = rollup
            except Exception:
                pass
            return payload

    def status_text(self) -> tuple[int, str]:
        try:
            from config import load_config
            from radar_status import format_status_message
            from storage import storage_from_config

            cfg = load_config()
            storage = storage_from_config(cfg)
            return 200, format_status_message(cfg, storage)
        except SystemExit as exc:
            msg = str(exc) or "Ошибка конфигурации (.env)"
            if "POLL_INTERVAL_MINUTES" in msg and "минимум" in msg:
                msg += (
                    "\n\nПодсказка: для Site с опросом 1 мин нужны "
                    "RADAR_PROFILE=site и RADAR_CONVEYOR=1 в .env.site"
                )
            return 500, msg
        except ValueError as exc:
            msg = str(exc)
            if "POLL_INTERVAL_MINUTES" in msg:
                msg += (
                    "\n\nПодсказка: RADAR_CONVEYOR=1 в .env.site "
                    "(см. docs/ops/RUN.md)"
                )
            return 500, f"Не удалось загрузить статус:\n{msg}"
        except Exception as exc:
            return 500, f"Не удалось загрузить статус:\n{exc}"

    def log_content(self, name: str) -> tuple[int, str]:
        if name in ("radar.log", "radar"):
            log_path = _LOG_RADAR or (_ROOT / "data" / "radar.log")
            return 200, _tail_utf8(log_path, _TAIL_LINES)
        if name in ("tg_join.log", "tg_join"):
            return 200, _tail_utf8(_LOG_JOIN, _TAIL_LINES)
        return 404, f"Unknown log: {name}\n"


_controller = RadarController()


class _Handler(BaseHTTPRequestHandler):
    server_version = "RadarControl/1.0"

    def log_message(self, fmt: str, *args) -> None:
        pass

    def _cors(self) -> None:
        origin = self.headers.get("Origin", "")
        allowed = _cors_allowed_origins()
        if allowed:
            if origin and origin in allowed:
                self.send_header("Access-Control-Allow-Origin", origin)
            else:
                self.send_header("Access-Control-Allow-Origin", allowed[0])
        else:
            self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, code: int, text: str) -> None:
        body = text.encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/start":
            try:
                proc = subprocess.run(
                    [
                        str(_PYTHON),
                        str(_ROOT / "scripts" / "radar_spawn_workers.py"),
                        "--profile",
                        _RADAR_PROFILE,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=str(_ROOT),
                    env=os.environ.copy(),
                )
                lines = [ln for ln in (proc.stdout or "").splitlines() if ln.strip()]
                if lines:
                    result = json.loads(lines[-1])
                else:
                    result = {
                        "ok": False,
                        "errors": [
                            (proc.stderr or "spawn_start_empty").strip()[:500]
                        ],
                    }
                if proc.returncode not in (0, 1) and result.get("ok"):
                    result = {
                        "ok": False,
                        "errors": result.get("errors", [])
                        + [f"spawn exit {proc.returncode}"],
                    }
            except subprocess.TimeoutExpired:
                self._send_json(504, {"ok": False, "error": "start_timeout"})
                return
            except Exception as exc:
                _log_start_failure(exc)
                self._send_json(
                    500,
                    {"ok": False, "error": "start_exception", "detail": str(exc)},
                )
                return
            code = 200 if result.get("ok") else 400
            self._send_json(code, result)
            return
        if path == "/stop":
            result = _controller.stop()
            self._send_json(200, result)
            return
        if path == "/shutdown":
            result = _controller.shutdown()
            self._send_json(200, result)
            return
        if path == "/ui-expanded":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                data = {}
            _controller.set_ui_expanded(bool(data.get("expanded", True)))
            self._send_json(200, {"ok": True})
            return
        self._send_json(404, {"ok": False, "error": "not_found"})

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/status":
            self._send_json(200, _controller.status_payload())
            return
        if path == "/status-text":
            code, text = _controller.status_text()
            self._send_text(code, text)
            return
        if path.startswith("/logs/"):
            name = path[len("/logs/") :]
            code, text = _controller.log_content(name)
            self._send_text(code, text)
            return
        if path == "/health":
            self._send_json(200, {"ok": True})
            return
        self._send_json(404, {"ok": False, "error": "not_found"})


def _boot_sweep_disabled_exchanges() -> None:
    """Site без бирж: убрать зомби main.py до отдачи /status."""
    from config import radar_exchanges_enabled
    from process_guard import kill_duplicate_radar_workers

    if radar_exchanges_enabled():
        return
    kill_duplicate_radar_workers(
        profile=_RADAR_PROFILE,
        role="main",
        log_source="radar_control:boot_no_exchanges",
    )


def _run_start_cli() -> int:
    """Отдельный процесс для /start — API не падает при spawn воркеров (Windows)."""
    _init_profile_paths()
    try:
        result = _controller.start()
        print(json.dumps(result, ensure_ascii=False), flush=True)
        return 0 if result.get("ok") else 1
    except Exception as exc:
        _log_start_failure(exc)
        print(
            json.dumps(
                {"ok": False, "errors": [str(exc)], "error": "start_exception"},
                ensure_ascii=False,
            ),
            flush=True,
        )
        return 1


def main() -> int:
    import os

    _init_profile_paths()
    if not _acquire_single_instance():
        lock_name = _LOCK_PATH.name if _LOCK_PATH else "radar_desktop.lock"
        print(
            f"Уже запущен radar_control [{_RADAR_PROFILE}] (или другой пульт).\n"
            f"Закройте его или удалите data\\{lock_name} после сбоя.",
            file=sys.stderr,
        )
        return 1

    _boot_sweep_disabled_exchanges()

    port = int(os.environ.get("RADAR_CONTROL_PORT", _DEFAULT_PORT))
    server = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    print(
        f"radar_control [{_RADAR_PROFILE}] http://127.0.0.1:{port}",
        flush=True,
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _controller.stop(silent=True)
        server.server_close()
        _release_lock()
    return 0


if __name__ == "__main__":
    if "--do-start-only" in sys.argv:
        raise SystemExit(_run_start_cli())
    raise SystemExit(main())
