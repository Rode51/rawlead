"""HTTP API пульта FL Radar: subprocess, lock, логи, статус.

Запуск: .venv\\Scripts\\python.exe scripts\\radar_control.py
Порт: RADAR_CONTROL_PORT (по умолчанию 18765)
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

if sys.platform == "win32":
    import msvcrt

    CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
else:
    msvcrt = None  # type: ignore
    CREATE_NO_WINDOW = 0

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

_LOCK_PATH = _ROOT / "data" / ".radar_desktop.lock"
_PYTHON = _ROOT / ".venv" / "Scripts" / "python.exe"
_LOG_RADAR = _ROOT / "data" / "radar.log"
_LOG_JOIN = _ROOT / "data" / "tg_join.log"
_TAIL_LINES = 200
_DEFAULT_PORT = 18765

_STOP_PS = (
    "Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | "
    "Where-Object { $_.CommandLine -match "
    "'uisness\\\\(src\\\\main|scripts\\\\tg_main|scripts\\\\tg_join_daemon|scripts\\\\tg_join_queue)' } | "
    "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
)

_lock_fh = None


def _acquire_single_instance() -> bool:
    global _lock_fh
    _LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        fh = open(_LOCK_PATH, "a+b")
    except OSError:
        return True
    if msvcrt is not None:
        try:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            fh.close()
            return False
    _lock_fh = fh
    return True


def _release_lock() -> None:
    global _lock_fh
    if _lock_fh is not None:
        try:
            if msvcrt is not None:
                _lock_fh.seek(0)
                msvcrt.locking(_lock_fh.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
        _lock_fh.close()
        _lock_fh = None


def _hidden_popen(args: list[str], cwd: Path) -> subprocess.Popen:
    kwargs: dict = {
        "cwd": str(cwd),
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if sys.platform == "win32":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        kwargs["startupinfo"] = si
        kwargs["creationflags"] = CREATE_NO_WINDOW
    return subprocess.Popen(args, **kwargs)


def stop_radar_processes() -> None:
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", _STOP_PS],
                cwd=str(_ROOT),
                creationflags=CREATE_NO_WINDOW,
                check=False,
                timeout=12,
            )
        except subprocess.TimeoutExpired:
            pass
    try:
        from health_check import try_release_stale_tg_main_lock

        import time

        time.sleep(0.3)
        try_release_stale_tg_main_lock()
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

    def __post_init__(self) -> None:
        if not self.children:
            self.children = [
                ChildSpec("exchanges", "Биржи", "src/main.py"),
                ChildSpec("tg", "TG", "scripts/tg_main.py"),
            ]

    def _running_needles(self) -> set[str]:
        if sys.platform != "win32":
            return set()
        needles = [str(s.script_path()).replace("/", "\\") for s in self.children]
        ps = (
            "Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | "
            "ForEach-Object { $_.CommandLine }"
        )
        try:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                cwd=str(_ROOT),
                capture_output=True,
                text=True,
                creationflags=CREATE_NO_WINDOW,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            return set()
        cmdlines = r.stdout or ""
        return {n for n in needles if n in cmdlines}

    def _is_alive(self, spec: ChildSpec, running: set[str] | None = None) -> bool:
        if spec.popen is not None and spec.popen.poll() is None:
            return True
        if running is None:
            running = self._running_needles()
        needle = str(spec.script_path()).replace("/", "\\")
        return needle in running

    def workers_running(self, running: set[str] | None = None) -> bool:
        return any(self._is_alive(s, running) for s in self.children)

    def set_ui_expanded(self, expanded: bool) -> None:
        with self._lock:
            self._ui_expanded = expanded

    def start(self) -> dict:
        with self._lock:
            if self._starting:
                return {"ok": False, "error": "already_starting"}
            if not _PYTHON.is_file():
                return {
                    "ok": False,
                    "error": "no_venv",
                    "detail": f"Нет Python: {_PYTHON}",
                }
            self._starting = True
            self._ever_started = True
            errors: list[str] = []
            try:
                # Без PowerShell-sweep — иначе /start висит 30+ с
                self._stop_unlocked(sweep_orphans=False)
                for spec in self.children:
                    script = spec.script_path()
                    if not script.is_file():
                        errors.append(f"Нет файла: {script}")
                        continue
                    try:
                        spec.popen = _hidden_popen(
                            [str(_PYTHON), "-u", str(script)],
                            _ROOT,
                        )
                    except OSError as exc:
                        errors.append(f"{spec.label}: {exc}")
                        spec.popen = None
                self._ui_expanded = True
                return {"ok": len(errors) == 0, "errors": errors}
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
            stop_radar_processes()
        self._ui_expanded = False
        return {"ok": True}

    def stop(self, silent: bool = False) -> dict:
        with self._lock:
            return self._stop_unlocked(sweep_orphans=True)

    def lamp_state(self, spec: ChildSpec, running: set[str], workers_active: bool) -> str:
        if self._is_alive(spec, running):
            return "ok"
        if self._ever_started and (self._ui_expanded or workers_active):
            return "error"
        return "idle"

    def status_payload(self) -> dict:
        with self._lock:
            running = self._running_needles()
            for spec in self.children:
                if spec.popen is not None and spec.popen.poll() is not None:
                    spec.popen = None
            workers = self.workers_running(running)
            if self._ui_expanded and not workers:
                self._ui_expanded = False
            lamps = []
            for spec in self.children:
                state = self.lamp_state(spec, running, workers)
                lamps.append(
                    {
                        "key": spec.key,
                        "label": spec.label,
                        "state": state,
                        "caption": (
                            "работает"
                            if state == "ok"
                            else ("нет" if state == "error" else "")
                        ),
                    }
                )
            return {
                "running": workers,
                "ever_started": self._ever_started,
                "ui_expanded": self._ui_expanded,
                "lamps": lamps,
            }

    def status_text(self) -> tuple[int, str]:
        try:
            from config import load_config
            from radar_status import format_status_message
            from storage import storage_from_config

            cfg = load_config()
            storage = storage_from_config(cfg)
            return 200, format_status_message(cfg, storage)
        except SystemExit as exc:
            return 500, str(exc) or "Ошибка конфигурации (.env)"
        except Exception as exc:
            return 500, f"Не удалось загрузить статус:\n{exc}"

    def log_content(self, name: str) -> tuple[int, str]:
        if name in ("radar.log", "radar"):
            return 200, _tail_utf8(_LOG_RADAR, _TAIL_LINES)
        if name in ("tg_join.log", "tg_join"):
            return 200, _tail_utf8(_LOG_JOIN, _TAIL_LINES)
        return 404, f"Unknown log: {name}\n"


_controller = RadarController()


class _Handler(BaseHTTPRequestHandler):
    server_version = "RadarControl/1.0"

    def log_message(self, fmt: str, *args) -> None:
        pass

    def _cors(self) -> None:
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
            result = _controller.start()
            code = 200 if result.get("ok") else 400
            self._send_json(code, result)
            return
        if path == "/stop":
            result = _controller.stop()
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


def main() -> int:
    import os

    if not _acquire_single_instance():
        print(
            "Уже запущен radar_control (или другой пульт).\n"
            "Закройте его или удалите data\\.radar_desktop.lock после сбоя.",
            file=sys.stderr,
        )
        return 1

    port = int(os.environ.get("RADAR_CONTROL_PORT", _DEFAULT_PORT))
    server = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    print(f"radar_control http://127.0.0.1:{port}", flush=True)

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
    raise SystemExit(main())
