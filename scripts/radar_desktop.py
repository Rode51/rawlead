"""Пульт FL Radar: старт/стоп трёх процессов без окон cmd (Windows)."""

from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

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
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", _STOP_PS],
            cwd=str(_ROOT),
            creationflags=CREATE_NO_WINDOW,
            check=False,
        )


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


class RadarDesktopApp:
    def __init__(self) -> None:
        self._children: list[ChildSpec] = [
            ChildSpec("exchanges", "Биржи", "src/main.py"),
            ChildSpec("tg", "TG", "scripts/tg_main.py"),
            ChildSpec("join", "Join", "scripts/tg_join_daemon.py"),
        ]
        self._indicator_labels: dict[str, tk.Label] = {}
        self._starting = False

        self.root = tk.Tk()
        self.root.title("FL Radar — пульт")
        self.root.minsize(720, 520)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        top = ttk.Frame(self.root, padding=8)
        top.pack(fill=tk.X)

        ttk.Button(top, text="▶ Старт", command=self._on_start).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(top, text="⏹ Стоп", command=self._on_stop).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Button(top, text="Обновить статус", command=self._refresh_status).pack(side=tk.LEFT)

        ind = ttk.LabelFrame(self.root, text="Процессы", padding=8)
        ind.pack(fill=tk.X, padx=8, pady=(0, 4))
        for spec in self._children:
            row = ttk.Frame(ind)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=spec.label, width=8).pack(side=tk.LEFT)
            lbl = ttk.Label(row, text="🔴 остановлен", font=("Segoe UI", 10))
            lbl.pack(side=tk.LEFT)
            self._indicator_labels[spec.key] = lbl

        ttk.Label(
            self.root,
            text="Пауза — в Telegram-боте (ℹ Статус)",
            foreground="#555",
        ).pack(anchor=tk.W, padx=12, pady=(0, 4))

        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        self._log_radar = scrolledtext.ScrolledText(nb, wrap=tk.WORD, font=("Consolas", 9))
        self._log_join = scrolledtext.ScrolledText(nb, wrap=tk.WORD, font=("Consolas", 9))
        self._status_text = scrolledtext.ScrolledText(nb, wrap=tk.WORD, font=("Segoe UI", 10))
        for w in (self._log_radar, self._log_join, self._status_text):
            w.configure(state=tk.DISABLED)

        nb.add(self._log_radar, text="radar.log")
        nb.add(self._log_join, text="tg_join.log")
        nb.add(self._status_text, text="Статус")

        self._schedule_poll()
        self._schedule_logs()

    def run(self) -> None:
        self.root.mainloop()

    def _schedule_poll(self) -> None:
        self._update_indicators()
        self.root.after(2500, self._schedule_poll)

    def _schedule_logs(self) -> None:
        self._update_log_widget(self._log_radar, _LOG_RADAR)
        self._update_log_widget(self._log_join, _LOG_JOIN)
        self.root.after(1500, self._schedule_logs)

    def _running_needles(self) -> set[str]:
        if sys.platform != "win32":
            return set()
        needles = [
            str(s.script_path()).replace("/", "\\") for s in self._children
        ]
        ps = (
            "Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | "
            "ForEach-Object { $_.CommandLine }"
        )
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            cwd=str(_ROOT),
            capture_output=True,
            text=True,
            creationflags=CREATE_NO_WINDOW,
        )
        cmdlines = r.stdout or ""
        return {n for n in needles if n in cmdlines}

    def _is_alive(self, spec: ChildSpec, running: set[str] | None = None) -> bool:
        if spec.popen is not None and spec.popen.poll() is None:
            return True
        if running is None:
            running = self._running_needles()
        needle = str(spec.script_path()).replace("/", "\\")
        return needle in running

    def _update_indicators(self) -> None:
        running = self._running_needles()
        for spec in self._children:
            alive = self._is_alive(spec, running)
            lbl = self._indicator_labels[spec.key]
            if alive:
                lbl.configure(text="🟢 работает")
            else:
                lbl.configure(text="🔴 остановлен")
                if spec.popen is not None and spec.popen.poll() is not None:
                    spec.popen = None

    def _update_log_widget(self, widget: scrolledtext.ScrolledText, path: Path) -> None:
        text = _tail_utf8(path, _TAIL_LINES)
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        widget.see(tk.END)
        widget.configure(state=tk.DISABLED)

    def _set_status_text(self, text: str) -> None:
        self._status_text.configure(state=tk.NORMAL)
        self._status_text.delete("1.0", tk.END)
        self._status_text.insert(tk.END, text)
        self._status_text.see(tk.END)
        self._status_text.configure(state=tk.DISABLED)

    def _refresh_status(self) -> None:
        try:
            from config import load_config
            from radar_status import format_status_message
            from storage import storage_from_config

            cfg = load_config()
            storage = storage_from_config(cfg)
            self._set_status_text(format_status_message(cfg, storage))
        except SystemExit as exc:
            messagebox.showerror("Статус", str(exc) or "Ошибка конфигурации (.env)")
        except Exception as exc:
            messagebox.showerror("Статус", f"Не удалось загрузить статус:\n{exc}")

    def _on_start(self) -> None:
        if self._starting:
            return
        if not _PYTHON.is_file():
            messagebox.showerror(
                "Старт",
                f"Нет Python в виртуальном окружении:\n{_PYTHON}\n\n"
                "Создайте: py -3.11 -m venv .venv\n"
                "Затем: .venv\\Scripts\\python.exe -m pip install -r requirements.txt",
            )
            return
        self._starting = True
        try:
            self._on_stop(silent=True)
            self.root.update_idletasks()
            errors: list[str] = []
            for spec in self._children:
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
            if errors:
                messagebox.showerror("Старт", "\n".join(errors))
            self._update_indicators()
        finally:
            self._starting = False

    def _on_stop(self, silent: bool = False) -> None:
        for spec in self._children:
            if spec.popen is not None and spec.popen.poll() is None:
                try:
                    spec.popen.terminate()
                except OSError:
                    pass
            spec.popen = None
        stop_radar_processes()
        self._update_indicators()
        if not silent:
            self.root.update_idletasks()

    def _on_close(self) -> None:
        running = self._running_needles()
        if any(self._is_alive(s, running) for s in self._children):
            if messagebox.askyesno(
                "Выход",
                "Остановить радар и закрыть пульт?",
                default=messagebox.YES,
            ):
                self._on_stop(silent=True)
            else:
                return
        self.root.destroy()


def main() -> int:
    if not _acquire_single_instance():
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "FL Radar — пульт",
            "Уже открыт другой экземпляр пульта.\n"
            "Закройте его или удалите data\\.radar_desktop.lock после сбоя.",
        )
        root.destroy()
        return 1
    try:
        RadarDesktopApp().run()
    finally:
        stop_radar_processes()
        _release_lock()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
