# Регрессия: дубли main/tg_main, биржи «красные»

**Дата:** 2026-05-26  
**Статус:** ✅ **принято владельцем 2026-05-26** (Биржи ok, полный P1.4 в логе, `last_cycle` 18:38:11)  
**Связь:** [`2026-05-24-duplicate-python-processes.md`](2026-05-24-duplicate-python-processes.md) (было «решено», в коде нет)

## Симптом (владелец)

- Пульт: **Биржи — красная** («нет»), TG warn/ok.
- PowerShell: **2× `tg_main.py`** (`.venv` + system Python), **0× `main.py`**.
- `data/radar.log`: два `── Цикл … ──` подряд, **нет** строк `FL.ru │ …` / `Итого в бот`.
- SQLite: «Последний цикл: ещё не было».

## Факты (проверка Lead 2026-05-26)

| Заявлено в тикете 05-24 | В репозитории сейчас |
|-------------------------|----------------------|
| `data/.main.lock` + exit 1 второму `main.py` | **Нет** в `src/main.py` |
| `kill_duplicate` при старте `main.py` / `tg_main.py` | **Нет** в обоих файлах |
| `kill_duplicate` только в `radar_control` **stop** (`_stop_unlocked`) | **Да** |
| `.tg_main.lock` + msvcrt | **Да** в `scripts/tg_main.py`, но **2 процесса** всё равно живут |
| Идемпотентность `/start` | **Да**, если только пульт и popen живы |

`kill_duplicate` в логе чаще убивает **radar_control**, не пару main+tg:

```text
радар:дубль:убиты PID 29644 (radar_control:all)
радар:дубль:убиты PID 28844 (radar_control:stop)
```

## Почему «защиты нет» (корень)

1. **Охрана только на границе пульта** — `kill_duplicate` при `/stop` и перед `/start`. Запуск **`start-radar-all.bat`** / второй `python scripts\tg_main.py` **минует** пульт.
2. **`main.py` без lock** — два процесса могут писать `── Цикл ──` (видели в логе) и падать/убивать друг друга.
3. **`tg_main` lock слабый:** при `OSError` открытия lock-файла → `return True` (fail-open); `_log_start()` **до** `_acquire_single_instance()`.
4. **`stop-radar.bat`** — только `python.exe`, не `pythonw.exe` → `radar_control` на system `pythonw` может остаться.
5. **`start-radar-desktop.bat`** — API на **system** `pythonw`, воркеры на `.venv` → легко накопить «чужой» TG с system Python.

## Регрессия пульта (владелец 2026-05-26)

- **▶ «Старт»:** API `/start` → `ok: true`, но через 1–3 с **0** процессов `main`/`tg_main`, лампы **idle**.
- В логе по-прежнему **2×** `── Цикл ──`, строк FL.ru нет — биржи не живут.
- `stop-radar.bat` теперь дергает `kill_all_radar_control` → может **убить API** пульта (`радар:дубль:убиты … radar_control:all` в логе).
- **Не трогали по смыслу:** UI Tauri — в diff только типы `last_cycle`; логика ▶ та же.

**Гипотеза (подтверждено 18:20–18:21):** после spawn `trim_radar_workers_to_pair` и/или `post_spawn kill_non_venv` **убивают** только что поднятые PID → в логе `радар:дубль:… (radar_control:trim)` или `post_spawn`, затем `main=0 tg=0`.

**Откат / фикс Coder (минимум):** в `/start` — **только** `pre_spawn` kill non-venv; **убрать** `post_spawn` и **`trim`**; проверка `count_radar_workers()==(1,1)`. Lock на воркерах — оставить. После правки — **перезапуск VBS** (старый `pythonw` держит старый код в памяти).

## Решение (Coder 2026-05-26)

1. `radar_control.start()` — без `post_spawn`/`trim`; `pre_spawn`: `kill_duplicate` + `kill_non_venv` (только `.venv` не трогать).
2. `process_guard` — `kill_non_venv` не считает system+`main.py` «своим»; `count_radar_workers`: при любом `.venv` в группе → 1 (не ложный main=2).
3. **Убран** `kill_duplicate` в `main`/`tg_main` при старте — venv-launcher (PID A) убивал дочерний `Python311`+`main.py` (PID B) → к 0.75 с `main=0 tg=0`, код выхода 15.
4. `radar_control` — ожидание пары воркеров до 5 с (не один `sleep 0.75`).

**Почему 2× `── Цикл ──`:** лишний system `main` до фикса `kill_non_venv`; **почему main=0 tg=0:** `main:startup` kill_duplicate резал child PID.

## Критерии приёмки (Coder)

| # | Готово когда | Приёмка |
|---|----------------|---------|
| R1 | `src/main.py`: `data/.main.lock` (как `.tg_main.lock`) — второй экземпляр exit 1 + строка в `radar.log` | ✅ |
| R2 | Lock + очистка через `radar_control` `pre_spawn` (не `kill_duplicate` в main при старте) | ✅ |
| R3 | После пульт ▶: `count_radar_workers() == (1, 1)` | ✅ |
| R4 | Пульт ▶: полный цикл P1.4 (5 строк + `Итого`), лампа **Биржи ok** | ✅ 2026-05-26 18:38 |
| R5 | Повторный ручной старт при работающем пульте — дубль не остаётся | ⚠️ оговорка: system Python — Стоп→▶ |
| R6 | `stop-radar.bat` / `process_guard`: workers + join | ✅ |
| R7 | Тикет 05-24 и [`STATUS.md`](../team/common/STATUS.md) — статус совпадает с кодом | ✅ |

**Доп. hotfix при приёмке:** `_echo` в `main.py` — `except UnicodeEncodeError` (заголовок `── Цикл ──` под Windows cp1251).

**Файлы:** `src/main.py`, `scripts/tg_main.py`, `src/process_guard.py`, `scripts/radar_control.py`, `scripts/stop-radar.bat`, `docs/ops/DESKTOP_LAUNCH.md`
