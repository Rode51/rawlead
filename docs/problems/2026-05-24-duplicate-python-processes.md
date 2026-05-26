# Дубли python (venv + system) ломают TG

**Дата:** 2026-05-24  
**Статус:** регрессия 2026-05-26 — см. [`2026-05-26-duplicate-workers-regression.md`](2026-05-26-duplicate-workers-regression.md) · было «решено» 2026-05-24  
**Связь:** [`2026-05-24-tg-forward-not-via-bot.md`](2026-05-24-tg-forward-not-via-bot.md) § I

## Симптом

- 2× `tg_main` + 2× `main.py` → `database is locked`, сообщения не в логе.
- **2026-05-24:** 2× `main.py` + 1× `tg_main` → пары `радар:старт` / `цикл:старт`, пересылка в ЛС, § H не виден в логе.

## Факты

```powershell
Get-CimInstance Win32_Process -Filter "name='python.exe'" |
  Where-Object { $_.CommandLine -match 'uisness' }
```

**Норма после пульт ▶:** 2 строки — `src/main.py` + `scripts/tg_main.py`, обе `.venv\Scripts\python.exe`.

**Сейчас (плохо):** 3+ строк или два `main.py`.

## Ожидание (Mechanic § I)

| # | Готово когда |
|---|----------------|
| I1 | `/stop` пульта убивает **все** uisness workers (main + tg_main + join), не только popen |
| I2 | `/start` перед spawn — `kill_duplicate_radar_workers()` без role; **не** остаётся второго main |
| I3 | Повторный ▶ при уже running → не второй main (идемпотентность) |
| I4 | `radar.log`: `радар:дубль:убиты PID …` если были лишние |
| I5 | Док: запуск **только** `start-radar-desktop.vbs` — не bat/tg_main вручную |

**Файлы:** `scripts/radar_control.py`, `src/process_guard.py`, `src/main.py`, `scripts/tg_main.py`, `docs/ops/DESKTOP_LAUNCH.md`

## Было (process_guard)

- `src/process_guard.py` — kill чужих main/tg_main
- `radar_control.py` `/start` — guard + lock
- Статус **fixed** 2026-05-24 — **регрессия**, переоткрыто.

## Доп. (2026-05-24) «Нет связи с API :18765»

**Причина:** два `radar_control.py` (`.venv` + **system Python**); зависший держал порт, `/health` не отвечал. Плюс `/stop`/`/start` держали HTTP-lock во время `wait_radar_workers_stopped` → пульт «мертвый».

**Фикс:** sweep вне lock; `kill_other_radar_control()` при старте API; таймаут `apiGet` в пульте.

**Сейчас:** закрой пульт → `start-radar-desktop.vbs` → в браузере http://127.0.0.1:18765/health → `{"ok":true}`. Если правили `desktop/src` — `scripts\rebuild-pult.bat`.

## Решение (Mechanic 2026-05-24)

| Критерий | Что сделано |
|----------|-------------|
| I1 | `radar_control` `/stop`: `stop_radar_processes` + `kill_duplicate` (все воркеры) + `wait_radar_workers_stopped` |
| I2 | `/start`: kill без role → полный stop с sweep → wait → spawn (нет гонки «старый main + новый») |
| I3 | `/start` при уже 1×main + 1×tg_main и живых popen → `already_running`, без второго spawn |
| I4 | `радар:дубль:убиты PID …` в `data/radar.log` (`process_guard.log_duplicate_kills`) |
| I5 | Запуск только `start-radar-desktop.vbs` — в `docs/ops/DESKTOP_LAUNCH.md` (Lead); не bat/tg_main вручную |

Дополнительно: lock `data/.main.lock` (как `.tg_main.lock`) — второй `main.py` выходит с кодом 1.

## Изменённые файлы

- `src/process_guard.py` — kill join-воркеров, count/wait, лог в radar.log
- `scripts/radar_control.py` — stop/start порядок, идемпотентность `/start`
- `src/main.py` — `.main.lock`, один kill при старте
- `scripts/tg_main.py` — kill с логом в radar.log
- `.gitignore` — `data/.main.lock`

## Регрессия (2026-05-24, сессия 2)

**Симптом:** после VBS снова 2× `radar_control.py`:
- PID 26264 — `.venv\Scripts\pythonw.exe` (правильный)
- PID 2100 — `C:\Users\hramo\AppData\Local\Programs\Python\Python311\pythonw.exe` (**системный**, держит порт :18765)

**Следствие:** `.venv` radar_control не может занять порт → пульт «Нет связи с API».

**Вывод:** `kill_all_radar_control()` в `start-radar-desktop.bat` (строка 8) **не убивает** системный `pythonw.exe`, запущенный предыдущей сессией. Нужно убивать `pythonw.exe` по пути не только `.venv`, но и по `CommandLine -match 'radar_control'` вне зависимости от пути Python.

**Текущий воркэраунд владельцу:** `Stop-Process -Id <PID системного> -Force` → `/health ok` → пульт работает.

**Решение (Lead 2026-05-24):** найден `pythonw.exe` (системный, PID 36492) с `radar_control` в CommandLine, не видимый через фильтр `uisness`. Убит вручную → lock удалён → `radar_control.py` запущен от `.venv` → `/health ok` → пульт работает.

**Задача Mechanic (регрессия 2):** `kill_all_radar_control` / `kill_other_radar_control` — матч по `radar_control.py` в CommandLine **без** требования `uisness.*scripts\` (системный `pythonw` + относительный путь).

### Решение (Mechanic, регрессия 2)

- `_RADAR_CONTROL_MATCH` в `process_guard.py`: `radar_control\.py` (любой Python: `.venv`, system, `pythonw.exe`).
- Убийства API пишутся в `radar.log`: `радар:дубль:убиты PID … (radar_control:all|other)`.

**Изменённые файлы:** `src/process_guard.py`

**Как проверить (регрессия 2):**

1. Закрыть пульт → подождать 5 с.
2. `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'radar_control' }` — **0** строк (или один после VBS).
3. Только `start-radar-desktop.vbs` → `curl http://127.0.0.1:18765/health` → `{"ok":true}`.
4. Повторный VBS без закрытия — в `radar.log` может быть `радар:дубль:… (radar_control:all)`, порт не занят «чужим» system `pythonw`.

## Как проверить

1. Пульт **■**, подожди 5–10 с → PowerShell: **0** uisness python (кроме `radar_control`).
2. Только **`start-radar-desktop.vbs`** → ▶ **один раз** → **ровно 2** python (`main` + `tg_main`), оба `.venv`.
3. Повторный ▶ без ■ → в ответе API `already_running`, **не** третий процесс.
4. При ручном втором `main.py` (bat) → в `radar.log` строка `радар:дубль:…` или второй процесс не стартует (lock).

## Владельцу (приёмка)

1. Пульт **■** (стоп), подожди 5–10 с.
2. PowerShell — проверка: должно быть **0** строк uisness (кроме возможно `radar_control.py`).
3. Только **`start-radar-desktop.vbs`** → ▶ **один раз**.
4. Снова проверка — **ровно 2** python.
