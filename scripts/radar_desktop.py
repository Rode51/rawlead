"""Пульт FL Radar: PyQt6 ops-dashboard — DEPRECATED, см. desktop/ + radar_control.py."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

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

_SIZE_COMPACT = (480, 340)
_SIZE_EXPANDED = (880, 640)
_LOG_PANEL_HEIGHT = 300
_ICON_FONT_PX = 48
_BTN_SIZE = 112

_STOP_PS = (
    "Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | "
    "Where-Object { $_.CommandLine -match "
    "'uisness\\\\(src\\\\main|scripts\\\\tg_main|scripts\\\\tg_join_daemon|scripts\\\\tg_join_queue)' } | "
    "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
)

_lock_fh = None

# --- Palette (ops-dashboard tokens) ---
_C_BG = "#0d0f14"
_C_CARD = "#161922"
_C_BG_LOG = "#090a0d"
_C_BORDER = "#252830"
_C_PRIMARY = "#3b82f6"
_C_ACTIVE = "#f59e0b"
_C_OK = "#22c55e"
_C_ERROR = "#ef4444"
_C_IDLE = "#4b5563"
_C_TEXT = "#f3f4f6"
_C_DIM = "#9ca3af"
_C_LOG = "#a3e635"
_C_STATUS_TEXT = "#e5e7eb"


def _build_stylesheet() -> str:
    return f"""
    QWidget {{
        background-color: {_C_BG};
        color: {_C_TEXT};
        font-family: "Segoe UI", sans-serif;
    }}
    QFrame#card {{
        background-color: {_C_CARD};
        border: 1px solid {_C_BORDER};
        border-radius: 8px;
    }}
    QPushButton#btn_refresh {{
        background-color: transparent;
        color: {_C_PRIMARY};
        border: 1px solid {_C_PRIMARY};
        border-radius: 4px;
        padding: 6px 14px;
        font-size: 11px;
    }}
    QPushButton#btn_refresh:hover {{
        background-color: rgba(59, 130, 246, 0.18);
    }}
    QPushButton#btn_toggle_run {{
        border: none;
        border-radius: 12px;
        font-size: 22px;
        font-weight: bold;
        min-height: 56px;
        min-width: 200px;
    }}
    QLabel#title {{
        font-size: 12px;
        font-weight: 600;
        color: {_C_TEXT};
        letter-spacing: 0.5px;
    }}
    QLabel#hint {{
        color: {_C_DIM};
        font-size: 10px;
    }}
    QLabel#proc_label {{
        color: {_C_TEXT};
        font-size: 11px;
    }}
    QTabWidget::pane {{
        border: 1px solid {_C_BORDER};
        background-color: {_C_BG_LOG};
        border-radius: 4px;
    }}
    QTabBar::tab {{
        background: {_C_BG};
        color: {_C_DIM};
        padding: 8px 16px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    QTabBar::tab:selected {{
        background: {_C_CARD};
        color: {_C_TEXT};
    }}
    QTextEdit#log_view {{
        background-color: {_C_BG_LOG};
        color: {_C_LOG};
        border: none;
        font-family: Consolas, "Courier New", monospace;
        font-size: 11px;
        padding: 8px;
    }}
    QTextEdit#status_view {{
        background-color: {_C_BG_LOG};
        color: {_C_STATUS_TEXT};
        border: none;
        font-family: "Segoe UI", sans-serif;
        font-size: 10px;
        padding: 8px;
    }}
    QLabel#footer {{
        color: #ffffff;
        font-size: 9px;
        font-weight: 400;
        padding: 2px 0 0 0;
    }}
    QPushButton#btn_collapse_logs {{
        background: transparent;
        color: #ffffff;
        border: none;
        font-size: 10px;
        padding: 0;
    }}
    QPushButton#btn_collapse_logs:hover {{
        color: #d1d5db;
    }}
    """


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


try:
    from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
    from PyQt6.QtGui import QColor, QFont, QGraphicsDropShadowEffect
    from PyQt6.QtWidgets import (
        QApplication,
        QFrame,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QSizePolicy,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    print(
        "PyQt6 не установлен. Выполните:\n"
        "  .venv\\Scripts\\python.exe -m pip install PyQt6",
        file=sys.stderr,
    )
    raise SystemExit(1) from None


def _lamp_glow(color: str, blur: int = 14) -> QGraphicsDropShadowEffect:
    fx = QGraphicsDropShadowEffect()
    fx.setBlurRadius(blur)
    fx.setOffset(0, 0)
    fx.setColor(QColor(color))
    return fx


class _LampDot(QLabel):
    """Круглый индикатор процесса."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(14, 14)
        self._glow = _lamp_glow(_C_IDLE, blur=0)
        self.setGraphicsEffect(self._glow)
        self.set_idle()

    def _apply_glow(self, color: str, blur: int) -> None:
        self._glow.setColor(QColor(color))
        self._glow.setBlurRadius(blur)

    def set_idle(self) -> None:
        self.setStyleSheet(
            f"background-color: {_C_IDLE}; border-radius: 7px; border: 1px solid #374151;"
        )
        self._apply_glow(_C_IDLE, 0)

    def set_ok(self) -> None:
        self.setStyleSheet(
            f"background-color: {_C_OK}; border-radius: 7px; border: 1px solid #16a34a;"
        )
        self._apply_glow(_C_OK, 16)

    def set_error(self) -> None:
        self.setStyleSheet(
            f"background-color: {_C_ERROR}; border-radius: 7px; border: 1px solid #dc2626;"
        )
        self._apply_glow(_C_ERROR, 16)


class _RunToggleButton(QPushButton):
    """Круглая кнопка ▶ / ⏹ с подсветкой и вдавливанием."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(_BTN_SIZE, _BTN_SIZE)
        self._glow = _lamp_glow(_C_PRIMARY, blur=22)
        self.setGraphicsEffect(self._glow)
        self._running = False
        self.set_idle()

    def _base_style(self, bg: str, border: str, color: str) -> str:
        return (
            f"QPushButton {{ background-color: {bg}; color: {color}; "
            f"border: 2px solid {border}; border-radius: {_BTN_SIZE // 2}px; "
            f"font-size: {_ICON_FONT_PX}px; font-weight: bold; padding: 0; "
            f"padding-top: 2px; }}"
            f"QPushButton:hover {{ background-color: {bg}; }}"
            f"QPushButton:pressed {{ background-color: {bg}; color: {color}; "
            f"border: 2px solid {border}; padding-top: 8px; padding-left: 4px; }}"
        )

    def set_idle(self) -> None:
        self._running = False
        self.setText("▶")
        self.setStyleSheet(
            self._base_style(
                "rgba(59, 130, 246, 0.14)",
                _C_PRIMARY,
                _C_PRIMARY,
            )
        )
        self._glow.setColor(QColor(_C_PRIMARY))
        self._glow.setBlurRadius(28)

    def set_running(self) -> None:
        self._running = True
        self.setText("⏹")
        self.setStyleSheet(
            self._base_style(
                "rgba(34, 197, 94, 0.14)",
                _C_OK,
                _C_OK,
            )
        )
        self._glow.setColor(QColor(_C_OK))
        self._glow.setBlurRadius(28)


class LogTailWorker(QThread):
    """Чтение хвостов логов в фоне — UI не блокируется."""

    radar_text = pyqtSignal(str)
    join_text = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._active = True

    def stop(self) -> None:
        self._active = False

    def run(self) -> None:
        while self._active:
            self.radar_text.emit(_tail_utf8(_LOG_RADAR, _TAIL_LINES))
            self.join_text.emit(_tail_utf8(_LOG_JOIN, _TAIL_LINES))
            self.msleep(1500)


class RadarDesktopWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FL Radar — пульт")
        self.setStyleSheet(_build_stylesheet())
        self.resize(*_SIZE_COMPACT)
        self.setMinimumSize(440, 280)

        self._children: list[ChildSpec] = [
            ChildSpec("exchanges", "Биржи", "src/main.py"),
            ChildSpec("tg", "TG", "scripts/tg_main.py"),
        ]
        self._lamps: dict[str, _LampDot] = {}
        self._starting = False
        self._ui_expanded = False
        self._logs_visible = False
        self._ever_started = False

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 10)
        root.setSpacing(10)

        # --- Верх: FL RADAR слева, обновить статус справа ---
        top = QHBoxLayout()
        title = QLabel("FL RADAR")
        title.setObjectName("title")
        top.addWidget(title, alignment=Qt.AlignmentFlag.AlignLeft)
        top.addStretch()
        self._btn_refresh = QPushButton("Обновить статус")
        self._btn_refresh.setObjectName("btn_refresh")
        self._btn_refresh.clicked.connect(self._refresh_status)
        top.addWidget(self._btn_refresh, alignment=Qt.AlignmentFlag.AlignRight)
        root.addLayout(top)

        # --- Карточка: кнопка + индикаторы (фиксированная высота) ---
        self._card = QFrame()
        self._card.setObjectName("card")
        self._card.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
        )
        card_layout = QVBoxLayout(self._card)
        card_layout.setSpacing(14)

        self._btn_toggle = _RunToggleButton()
        self._btn_toggle.clicked.connect(self._on_toggle)
        card_layout.addWidget(self._btn_toggle, alignment=Qt.AlignmentFlag.AlignCenter)

        lamps_row = QHBoxLayout()
        lamps_row.setSpacing(24)
        for spec in self._children:
            col = QVBoxLayout()
            col.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lamp = _LampDot()
            self._lamps[spec.key] = lamp
            col.addWidget(lamp, alignment=Qt.AlignmentFlag.AlignCenter)
            lbl = QLabel(spec.label)
            lbl.setObjectName("proc_label")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            col.addWidget(lbl)
            lamps_row.addLayout(col)
        card_layout.addLayout(lamps_row)

        hint = QLabel("Пауза FL/Kwork — в Telegram-боте (ℹ Статус)")
        hint.setObjectName("hint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(hint)

        root.addWidget(self._card, 0, Qt.AlignmentFlag.AlignTop)

        # --- Логи (ниже карточки, окно растёт вниз) ---
        self._log_section = QWidget()
        log_section_layout = QVBoxLayout(self._log_section)
        log_section_layout.setContentsMargins(0, 0, 0, 0)
        log_section_layout.setSpacing(4)

        log_header = QHBoxLayout()
        log_header.setContentsMargins(0, 0, 0, 0)
        self._btn_collapse_logs = QPushButton("▼")
        self._btn_collapse_logs.setObjectName("btn_collapse_logs")
        self._btn_collapse_logs.setFixedSize(22, 18)
        self._btn_collapse_logs.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_collapse_logs.setToolTip("Свернуть логи")
        self._btn_collapse_logs.clicked.connect(self._toggle_logs_panel)
        log_header.addWidget(self._btn_collapse_logs, alignment=Qt.AlignmentFlag.AlignLeft)
        log_header.addStretch()
        log_section_layout.addLayout(log_header)

        self._log_body = QWidget()
        self._log_body.setMinimumHeight(_LOG_PANEL_HEIGHT)
        self._log_body.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        log_outer = QVBoxLayout(self._log_body)
        log_outer.setContentsMargins(0, 0, 0, 0)

        self._tabs = QTabWidget()
        self._log_radar = QTextEdit()
        self._log_radar.setObjectName("log_view")
        self._log_radar.setReadOnly(True)
        self._log_radar.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._log_join = QTextEdit()
        self._log_join.setObjectName("log_view")
        self._log_join.setReadOnly(True)
        self._log_join.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._status_view = QTextEdit()
        self._status_view.setObjectName("status_view")
        self._status_view.setReadOnly(True)

        mono = QFont("Consolas", 10)
        if not mono.exactMatch():
            mono = QFont("Courier New", 10)
        self._log_radar.setFont(mono)
        self._log_join.setFont(mono)
        self._status_view.setFont(QFont("Segoe UI", 10))

        self._tabs.addTab(self._log_radar, "radar.log")
        self._tabs.addTab(self._log_join, "tg_join.log")
        self._tabs.addTab(self._status_view, "Статус")
        self._tabs.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        log_outer.addWidget(self._tabs, 1)
        log_section_layout.addWidget(self._log_body, 1)
        root.addWidget(self._log_section, 1)
        self._log_section.hide()

        self._footer = QLabel("by Rode 51")
        self._footer.setObjectName("footer")
        self._footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._footer, 0, Qt.AlignmentFlag.AlignBottom)

        self._log_worker = LogTailWorker(self)
        self._log_worker.radar_text.connect(self._on_radar_log)
        self._log_worker.join_text.connect(self._on_join_log)
        self._log_worker.start()

        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._update_indicators)
        self._poll_timer.start(2500)

    def _workers_running(self) -> bool:
        return any(self._is_alive(s) for s in self._children)

    def _sync_toggle_button(self) -> None:
        if self._workers_running():
            self._btn_toggle.set_running()
        else:
            self._btn_toggle.set_idle()

    def _window_height(self, with_logs: bool) -> int:
        base_h = _SIZE_COMPACT[1]
        if with_logs:
            return _SIZE_EXPANDED[1]
        if self._ui_expanded and not self._logs_visible:
            return base_h + 28
        return base_h

    def _apply_window_size(self, with_logs: bool) -> None:
        w = self.width() if self.width() > 200 else _SIZE_COMPACT[0]
        if with_logs and w < _SIZE_EXPANDED[0]:
            w = _SIZE_EXPANDED[0]
        if not with_logs and w > _SIZE_COMPACT[0]:
            w = _SIZE_COMPACT[0]
        self.resize(w, self._window_height(with_logs))

    def _show_logs_panel(self) -> None:
        self._logs_visible = True
        self._log_section.show()
        self._log_body.show()
        self._btn_collapse_logs.setText("▼")
        self._btn_collapse_logs.setToolTip("Свернуть логи")
        self._apply_window_size(with_logs=True)

    def _collapse_logs_panel(self) -> None:
        self._logs_visible = False
        self._log_body.hide()
        if self._ui_expanded or self._workers_running():
            self._log_section.show()
        else:
            self._log_section.hide()
        self._btn_collapse_logs.setText("▲")
        self._btn_collapse_logs.setToolTip("Развернуть логи")
        self._apply_window_size(with_logs=False)

    def _toggle_logs_panel(self) -> None:
        if self._logs_visible:
            self._collapse_logs_panel()
        elif self._workers_running() or self._ui_expanded:
            self._show_logs_panel()

    def _collapse_ui(self) -> None:
        self._ui_expanded = False
        self._logs_visible = False
        self._log_section.hide()
        self._log_body.hide()
        self._apply_window_size(with_logs=False)
        self._sync_toggle_button()

    def _expand_ui(self) -> None:
        self._ui_expanded = True
        self._sync_toggle_button()
        self._show_logs_panel()
        self._refresh_status()

    def _on_toggle(self) -> None:
        if self._workers_running():
            self._on_stop(silent=True)
            self._collapse_ui()
        else:
            self._on_start()
            if self._workers_running():
                self._expand_ui()

    def _on_radar_log(self, text: str) -> None:
        if not self._logs_visible:
            return
        sb = self._log_radar.verticalScrollBar()
        at_bottom = sb.value() >= sb.maximum() - 8
        self._log_radar.setPlainText(text)
        if at_bottom:
            sb.setValue(sb.maximum())

    def _on_join_log(self, text: str) -> None:
        if not self._logs_visible:
            return
        sb = self._log_join.verticalScrollBar()
        at_bottom = sb.value() >= sb.maximum() - 8
        self._log_join.setPlainText(text)
        if at_bottom:
            sb.setValue(sb.maximum())

    def _running_needles(self) -> set[str]:
        if sys.platform != "win32":
            return set()
        needles = [str(s.script_path()).replace("/", "\\") for s in self._children]
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
        session_active = self._ui_expanded or self._workers_running()
        for spec in self._children:
            lamp = self._lamps[spec.key]
            if self._is_alive(spec, running):
                lamp.set_ok()
            elif self._ever_started and session_active:
                lamp.set_error()
            else:
                lamp.set_idle()
            if spec.popen is not None and spec.popen.poll() is not None:
                spec.popen = None
        self._sync_toggle_button()
        if self._ui_expanded and not self._workers_running():
            self._ui_expanded = False
            self._collapse_logs_panel()
        elif self._workers_running() and self._ui_expanded and not self._logs_visible:
            self._show_logs_panel()

    def _refresh_status(self) -> None:
        try:
            from config import load_config
            from radar_status import format_status_message
            from storage import storage_from_config

            cfg = load_config()
            storage = storage_from_config(cfg)
            self._status_view.setPlainText(format_status_message(cfg, storage))
            sb = self._status_view.verticalScrollBar()
            sb.setValue(0)
        except SystemExit as exc:
            QMessageBox.critical(self, "Статус", str(exc) or "Ошибка конфигурации (.env)")
        except Exception as exc:
            QMessageBox.critical(self, "Статус", f"Не удалось загрузить статус:\n{exc}")

    def _on_start(self) -> None:
        if self._starting:
            return
        if not _PYTHON.is_file():
            QMessageBox.critical(
                self,
                "Старт",
                f"Нет Python в виртуальном окружении:\n{_PYTHON}\n\n"
                "Создайте: py -3.11 -m venv .venv\n"
                "Затем: .venv\\Scripts\\python.exe -m pip install -r requirements.txt",
            )
            return
        self._starting = True
        self._ever_started = True
        try:
            self._on_stop(silent=True)
            QApplication.processEvents()
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
                QMessageBox.warning(self, "Старт", "\n".join(errors))
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
            QApplication.processEvents()

    def closeEvent(self, event) -> None:  # noqa: N802
        running = self._running_needles()
        if any(self._is_alive(s, running) for s in self._children):
            reply = QMessageBox.question(
                self,
                "Выход",
                "Остановить радар и закрыть пульт?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self._on_stop(silent=True)
        self._log_worker.stop()
        self._log_worker.wait(2000)
        event.accept()

    def run(self) -> None:
        self.show()


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    if not _acquire_single_instance():
        QMessageBox.critical(
            None,
            "FL Radar — пульт",
            "Уже открыт другой экземпляр пульта.\n"
            "Закройте его или удалите data\\.radar_desktop.lock после сбоя.",
        )
        return 1

    win: RadarDesktopWindow | None = None
    try:
        win = RadarDesktopWindow()
        win.run()
        return app.exec()
    finally:
        if win is not None:
            win._log_worker.stop()
            win._log_worker.wait(1500)
        stop_radar_processes()
        _release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
