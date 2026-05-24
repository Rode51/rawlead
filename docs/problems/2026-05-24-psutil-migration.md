# Миграция process_guard с PowerShell на psutil

**Дата:** 2026-05-24  
**Статус:** решено — Mechanic (2026-05-24)  
**Связь:** [`2026-05-24-duplicate-python-processes.md`](2026-05-24-duplicate-python-processes.md) (корневая причина регрессий)

---

## Симптом / Корневая причина

Все регрессии в тикете дублей имеют один корень:  
`process_guard.py` определяет и убивает процессы через **PowerShell** (`Get-CimInstance`, `Stop-Process`).

Проблемы PowerShell-подхода:
- `pythonw.exe` с **системным Python** (`C:\Users\hramo\AppData\...\Python311\pythonw.exe`) не матчится regex `uisness.*radar_control` — потому что `pythonw` запускает скрипт относительным путём без `uisness` в CommandLine.
- `Get-CimInstance` + `Where-Object` возвращают **непредсказуемый stdout** (пустые строки, BOM, кодировка) — парсинг ломается.
- Таймаут 12 с → `subprocess.TimeoutExpired` → guard молча возвращает `[]` → дубли живут.
- `CREATE_NO_WINDOW` / `subprocess.run` — лишняя зависимость, Windows-only.
- Каждый вызов `count_radar_workers()` = 2 отдельных PowerShell-запроса (~1 с суммарно).

**Решение:** заменить весь PowerShell-слой на [`psutil`](https://pypi.org/project/psutil/) — чистый Python, кросс-платформ, итерирует процессы через WinAPI напрямую.

---

## Ожидание (Mechanic)

| # | Готово когда |
|---|--------------|
| P1 | `psutil>=5.9.0` добавлен в `requirements.txt` и установлен в `.venv` |
| P2 | `src/process_guard.py` не содержит `subprocess.run(["powershell"` — только `psutil` |
| P3 | `count_radar_workers()` возвращает правильные цифры для **любого** Python (venv + system + pythonw) |
| P4 | `kill_duplicate_radar_workers()` убивает дубли по regex на `' '.join(proc.cmdline())` — независимо от пути Python |
| P5 | `kill_all_radar_control()` / `kill_other_radar_control()` — аналогично psutil, матч по `radar_control\.py` в cmdline (любой путь Python) |
| P6 | `wait_radar_workers_stopped()` работает через psutil-loop, без PowerShell |
| P7 | Все публичные сигнатуры функций **не изменились** (обратная совместимость с `radar_control.py`, `main.py`, `tg_main.py`) |
| P8 | `radar.log`: строка `радар:дубль:убиты PID … (radar_control:all)` появляется при дублях |
| P9 | `start-radar-desktop.vbs` → ровно 2 worker (main + tg_main) — проверка в PowerShell вручную |

---

## Файлы

**Можно трогать:**
- `src/process_guard.py` — полная замена PowerShell на psutil
- `requirements.txt` — добавить `psutil>=5.9.0`

**Не трогать:**
- `scripts/radar_control.py` — вызывает guard, сигнатуры не меняются
- `src/main.py` — вызывает guard
- `scripts/tg_main.py` — вызывает guard
- `desktop/`, `docs/`, `.env`, `data/`

---

## Архитектура замены

### Было (PowerShell)

```python
def _kill_ps(match: str, pid: int) -> str:
    return (
        "Get-CimInstance Win32_Process | "
        "Where-Object { ($_.Name -eq 'python.exe' ...) "
        f"-and $_.CommandLine -match '{match}' "
        ...
    )

r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], ...)
```

### Стало (psutil)

```python
import psutil
import re

def _iter_python_procs():
    """Все python/pythonw процессы на Windows."""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            name = (proc.info['name'] or '').lower()
            if name in ('python.exe', 'pythonw.exe'):
                yield proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

def _cmd_str(proc) -> str:
    """Cmdline как строка для regex-матча."""
    try:
        return ' '.join(proc.cmdline())
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return ''

def _kill_matching(pattern: str, except_pid: int) -> list[int]:
    killed = []
    rx = re.compile(pattern, re.IGNORECASE)
    for proc in _iter_python_procs():
        if proc.pid == except_pid:
            continue
        if rx.search(_cmd_str(proc)):
            try:
                proc.kill()
                killed.append(proc.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    return killed
```

### count_radar_workers — psutil

```python
def count_radar_workers() -> tuple[int, int]:
    main_rx = re.compile(_ROLE_MATCH["main"], re.IGNORECASE)
    tg_rx   = re.compile(_ROLE_MATCH["tg_main"], re.IGNORECASE)
    mc = tc = 0
    for proc in _iter_python_procs():
        cmd = _cmd_str(proc)
        if main_rx.search(cmd): mc += 1
        if tg_rx.search(cmd):   tc += 1
    return mc, tc
```

---

## Проверка (владелец, после сдачи Mechanic)

1. `.venv\Scripts\pip install psutil` — убедиться что установлен.
2. Закрыть пульт → подождать 5 с.
3. `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'radar_control' }` — **0** строк.
4. Только `start-radar-desktop.vbs` → ▶ **один раз**.
5. Через 10 с: `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'uisness' }` — **ровно 2** (main + tg_main).
6. Повторный ▶ без ■ → `already_running`, третьего процесса нет.
7. `data/radar.log` — нет `TimeoutExpired`, нет ошибок PowerShell.

---

## Решение

PowerShell-слой (`Get-CimInstance`, `Stop-Process`, `subprocess.run`) полностью заменён на `psutil`:

- `_iter_python_procs()` — итерация по `python.exe` / `pythonw.exe` через `psutil.process_iter`
- `_cmd_str()` — `' '.join(proc.cmdline())` для regex-матча (работает с относительными путями system pythonw)
- `_kill_matching()` — единая функция kill по regex с опциональным `except_pid`
- `_ROLE_MATCH` / `_ALL_MATCH` — `(?:uisness[\\/].*)?` перед путём скрипта: матч и `C:\...\uisness\src\main.py`, и `pythonw.exe src\main.py`
- `_RADAR_CONTROL_MATCH` — только `radar_control\.py` (без требования `uisness` в cmdline)

Публичные функции — сигнатуры без изменений:

| Функция | Сигнатура |
|---------|-----------|
| `count_radar_workers` | `() -> tuple[int, int]` |
| `log_duplicate_kills` | `(killed, *, log_path=None, source='guard') -> None` |
| `kill_all_radar_control` | `() -> list[int]` |
| `kill_other_radar_control` | `(*, except_pid=None) -> list[int]` |
| `kill_duplicate_radar_workers` | `(*, role=None, except_pid=None, log_path=None, log_source='guard') -> list[int]` |
| `wait_radar_workers_stopped` | `(*, timeout_sec=8.0) -> bool` |

## Изменённые файлы

- `src/process_guard.py` — psutil вместо PowerShell
- `requirements.txt` — `psutil>=5.9.0`

## Как проверить

1. `.venv\Scripts\pip install psutil` — уже установлен (7.2.2).
2. Smoke: `.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'src'); from process_guard import count_radar_workers; print(count_radar_workers())"` → `(0, 0)` или актуальные цифры.
3. Владелец — сценарий § «Проверка» выше (P8–P9): VBS → 2 worker, повторный ▶ → `already_running`, `radar.log` без `TimeoutExpired`.
