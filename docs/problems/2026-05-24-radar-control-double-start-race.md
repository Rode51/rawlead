# radar_control: race condition при двойном запуске VBS

**Дата:** 2026-05-24  
**Статус:** решено — Mechanic  
**Связь:** [`2026-05-24-radar-control-psutil.md`](2026-05-24-radar-control-psutil.md)

---

## Симптом

«Нет связи с API» — при двойном клике на ярлык (или повторном клике до закрытия Desktop).

## Корневая причина

В `main()` добавлен `kill_other_radar_control()` **до** захвата lock-файла.

Сценарий двойного клика:
1. VBS → cmd.exe #1 → `pythonw.exe radar_control.py` → **Процесс A**
2. VBS → cmd.exe #2 → `pythonw.exe radar_control.py` → **Процесс B** (стартует ~одновременно)
3. Процесс A: `kill_other_radar_control()` → находит Процесс B → убивает
4. Процесс B: `kill_other_radar_control()` → находит Процесс A → убивает
5. **Оба мертвы.** Пульт открывается — API не отвечает.

Дополнительно: `start-radar-desktop.bat` убивает порт `:18765` через `netstat | findstr LISTENING`, но не убивает предыдущий `radar_control.py` по имени → zombie с system pythonw.exe не умирает.

---

## Ожидание (Mechanic)

| # | Готово когда |
|---|--------------|
| D1 | В `main()` — `kill_other_radar_control()` **удалён** (вызывает race при двойном старте) |
| D2 | Вместо него: в `start-radar-desktop.bat` — явный kill всех radar_control перед `start /B pythonw.exe` через `.venv\Scripts\python.exe -c "from process_guard import kill_all_radar_control; kill_all_radar_control()"` |
| D3 | В bat: пауза 1 с после kill перед стартом nового pythonw.exe (уже есть `timeout /t 1`) |
| D4 | Повторный клик на ярлык при живом radar_control → НЕ убивает его (bat делает kill → но видит что port уже слушает → не запускает второй) |
| D5 | Одиночный клик на ярлык → пульт открывается, API отвечает `{"ok": true}` |

---

## Файлы

**Можно трогать:**
- `scripts/start-radar-desktop.bat` — добавить kill_all_radar_control перед стартом
- `scripts/radar_control.py` — убрать `kill_other_radar_control()` из `main()`

**Не трогать:**
- `src/process_guard.py` — уже готов, только читать сигнатуры
- `desktop/`, `docs/`, `src/main.py`, `scripts/tg_main.py`

---

## Архитектура замены

### start-radar-desktop.bat — добавить в начало (после kill netstat):

```bat
REM Убить все radar_control (любой Python — venv или system)
"%RADAR_ROOT%\.venv\Scripts\python.exe" -c "import sys; sys.path.insert(0,'%RADAR_ROOT%\src'); from process_guard import kill_all_radar_control; kill_all_radar_control()"
timeout /t 1 /nobreak >nul
```

### radar_control.py main() — убрать строку:

```python
# УБРАТЬ:
kill_other_radar_control()

# Оставить только:
if not _acquire_single_instance():
    print("Уже запущен...", file=sys.stderr)
    return 1
```

---

## Как проверить

1. Закрыть пульт → `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'radar_control' }` → **0 строк**.
2. Кликнуть ярлык **дважды быстро** → подождать 5 с → **ровно один** radar_control.py в процессах.
3. `curl http://127.0.0.1:18765/health` → `{"ok":true}`.
4. Закрыть пульт → снова одиночный клик → снова работает.

---

## Решение (Mechanic, 2026-05-24)

| Критерий | Статус |
|----------|--------|
| D1 `kill_other_radar_control()` убран из `main()` | уже было (только lock) |
| D2 `kill_all_radar_control` в bat перед стартом | было |
| D3 `timeout /t 1` после kill | было |
| D4/D5 launcher → один system `pythonw` | **сделано** |

**Корень дубля:** `.venv\Scripts\pythonw.exe` на Windows — shim/launcher; поднимает второй `Python311\pythonw.exe` без venv-пакетов → два `radar_control`, гонка kill в bat.

**Правка в `start-radar-desktop.bat`:**
- `pythonw` берётся из `executable` в `.venv\pyvenv.cfg` (`python.exe` → `pythonw.exe`) — фактически `…\Python311\pythonw.exe`.
- `PYTHONPATH=%RADAR_ROOT%\.venv\Lib\site-packages` перед `start /B` (psutil и deps; `src` radar_control добавляет сам).

**Изменённые файлы:** `scripts/start-radar-desktop.bat`

**Проверка (Mechanic):**
1. После старта с `PYTHONPATH` + system `pythonw` → **1** процесс `pythonw.exe` с `radar_control` в CommandLine (не пара `.venv` + system).
2. `curl http://127.0.0.1:18765/health` → `{"ok": true}`.

**Владельцу:** закрыть пульт → VBS/ярлык → PowerShell: один `radar_control`; двойной быстрый клик → по-прежнему один API (kill в bat + lock в `main()`).
