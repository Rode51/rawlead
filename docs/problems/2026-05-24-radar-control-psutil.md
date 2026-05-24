# radar_control.py — убрать PowerShell, подключить process_guard

**Дата:** 2026-05-24  
**Статус:** решено — Mechanic (2026-05-24)  
**Связь:** [`2026-05-24-psutil-migration.md`](2026-05-24-psutil-migration.md) (process_guard уже написан)

---

## Симптом

Дубли `main.py` + `tg_main.py` остаются после нажатия ▶ повторно.  
`process_guard.py` уже переписан на `psutil`, но `radar_control.py` его **не использует** —  
у него свои два куска PowerShell, которые дубли не убивают.

---

## Два куска PowerShell в radar_control.py (убрать оба)

### 1. `_STOP_PS` + `stop_radar_processes()` (строки 36–112)

```python
_STOP_PS = (
    "Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | ..."
)

def stop_radar_processes() -> None:
    if sys.platform == "win32":
        subprocess.run(["powershell", "-NoProfile", "-Command", _STOP_PS], ...)
```

Проблема: матчит только `python.exe`, пропускает `pythonw.exe`; regex требует `uisness\\` в пути — системный Python не матчится; таймаут 12 с → падает молча.

### 2. `_running_needles()` (строки 155–175)

```python
def _running_needles(self) -> set[str]:
    ps = "Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | ..."
    subprocess.run(["powershell", ...])
```

Проблема: то же — только `python.exe`, только полные пути, таймаут.

### 3. `start()` — sweep отключён (строка 207)

```python
self._stop_unlocked(sweep_orphans=False)   # ← не убивает старые процессы!
```

Из-за этого повторный ▶ порождает второй `main.py` поверх живого.

---

## Ожидание (Mechanic)

| # | Готово когда |
|---|--------------|
| R1 | `_STOP_PS` константа удалена |
| R2 | `stop_radar_processes()` удалена; вместо неё — `process_guard.kill_duplicate_radar_workers()` |
| R3 | `_running_needles()` заменена на psutil-проверку через `process_guard.count_radar_workers()` или прямой `psutil` |
| R4 | `_is_alive()` работает через psutil (не через PowerShell) |
| R5 | `start()`: перед spawn — `kill_duplicate_radar_workers()` + `wait_radar_workers_stopped()` из process_guard |
| R6 | `main()` при старте вызывает `kill_other_radar_control()` — убивает системный pythonw с radar_control |
| R7 | Повторный ▶ без ■ → `already_running` или graceful restart, **не** третий процесс |
| R8 | Пульт ▶ → ровно 2 worker (main + tg_main) в `radar.log` |

---

## Файлы

**Можно трогать:**
- `scripts/radar_control.py` — убрать PowerShell, подключить process_guard

**Не трогать:**
- `src/process_guard.py` — уже готов, только читать сигнатуры
- `src/main.py`, `scripts/tg_main.py`, `desktop/`, `docs/`

---

## Архитектура замены

### _running_needles / _is_alive → psutil через process_guard

```python
# УБРАТЬ _running_needles() полностью.
# _is_alive: сначала проверяем popen, потом psutil
from process_guard import count_radar_workers

def _is_alive(self, spec: ChildSpec) -> bool:
    if spec.popen is not None and spec.popen.poll() is None:
        return True
    # psutil fallback
    mc, tc = count_radar_workers()
    if spec.key == "exchanges":
        return mc > 0
    if spec.key == "tg":
        return tc > 0
    return False

def workers_running(self) -> bool:
    return any(self._is_alive(s) for s in self.children)
```

### stop_radar_processes → process_guard

```python
# УБРАТЬ _STOP_PS и stop_radar_processes().
# В _stop_unlocked:
from process_guard import kill_duplicate_radar_workers, wait_radar_workers_stopped

def _stop_unlocked(self, *, sweep_orphans: bool = True) -> dict:
    for spec in self.children:
        if spec.popen is not None and spec.popen.poll() is None:
            try:
                spec.popen.terminate()
            except OSError:
                pass
        spec.popen = None
    if sweep_orphans:
        kill_duplicate_radar_workers()   # psutil, не PowerShell
        wait_radar_workers_stopped()
    self._ui_expanded = False
    return {"ok": True}
```

### start() — включить sweep

```python
def start(self) -> dict:
    with self._lock:
        if self._starting:
            return {"ok": False, "error": "already_starting"}
        if not _PYTHON.is_file():
            return {"ok": False, "error": "no_venv", "detail": f"Нет Python: {_PYTHON}"}
        self._starting = True
        self._ever_started = True
        errors: list[str] = []
        try:
            self._stop_unlocked(sweep_orphans=True)  # ← sweep включён
            for spec in self.children:
                script = spec.script_path()
                if not script.is_file():
                    errors.append(f"Нет файла: {script}")
                    continue
                try:
                    spec.popen = _hidden_popen([str(_PYTHON), "-u", str(script)], _ROOT)
                except OSError as exc:
                    errors.append(f"{spec.label}: {exc}")
                    spec.popen = None
            self._ui_expanded = True
            return {"ok": len(errors) == 0, "errors": errors}
        finally:
            self._starting = False
```

### main() — kill_other_radar_control при старте

```python
def main() -> int:
    import os
    from process_guard import kill_other_radar_control

    kill_other_radar_control()   # убить системный pythonw с radar_control до захвата порта

    if not _acquire_single_instance():
        print("Уже запущен radar_control...", file=sys.stderr)
        return 1
    ...
```

---

## Как проверить

1. `.venv\Scripts\pip show psutil` — есть.
2. Закрыть пульт → 5 с → `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'radar_control' }` → **0 строк**.
3. `start-radar-desktop.vbs` → ▶ → `radar.log`: ровно 2 worker (main + tg_main).
4. Повторный ▶ без ■ → `already_running` в ответе API ИЛИ restart, но **не 3 процесса**.
5. Остановить ■ → проверка → 0 worker.

---

## Решение (Mechanic 2026-05-24)

| Критерий | Что сделано |
|----------|-------------|
| R1 | `_STOP_PS` удалена |
| R2 | `stop_radar_processes()` удалена; `_stop_unlocked` → `kill_duplicate_radar_workers` + `wait_radar_workers_stopped` |
| R3 | `_running_needles()` удалена; живость — `count_radar_workers()` в `_is_alive` |
| R4 | `_is_alive()` — popen, затем psutil через `count_radar_workers()` |
| R5 | `start()`: `sweep_orphans=True`, sweep перед spawn |
| R6 | `main()`: `kill_other_radar_control()` до `_acquire_single_instance()` |
| R7 | `start()`: при живых popen и mc≥1, tc≥1 → `{"error": "already_running"}` |
| R8 | Приёмка владельцем (VBS → ▶ → 2 worker в `radar.log`) |

Дополнительно: `_release_stale_tg_lock()` — прежний вызов `try_release_stale_tg_main_lock` после sweep (без PowerShell).

## Изменённые файлы

- `scripts/radar_control.py`

## Как проверить (Mechanic)

- `py_compile scripts/radar_control.py` — OK
- В файле нет `powershell`, `_STOP_PS`, `stop_radar_processes`, `_running_needles`
- Приёмка: § «Как проверить» выше (п. 1–5) — владелец
