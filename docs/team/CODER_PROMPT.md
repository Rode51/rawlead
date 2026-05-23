# Coder — Пульт управления (десктоп, Windows)

Скопируй в **новый** чат: `@coder` + `@docs/team/CODER_PROMPT.md`

---

Ты **Coder** в `c:\Users\hramo\uisness`.

## Задача

**Одно окно** вместо 3 cmd: **Старт / Стоп** радара (full = биржи + TG + join), логи и индикаторы «жив/не жив».

Владелец: не программист, Windows 10/11.

## Не делать

- Не переносить логику FL/Kwork/TG/join в GUI — только **запуск/остановка** тех же скриптов, что bat
- Не ломать `start-radar-full.bat` / `stop-radar.bat` (можно вызывать их или общую логику)
- Не трогать WordPress
- Не обязательный `.exe` в этой задаче (достаточно `python scripts/radar_desktop.py`)

## Прочитай

| Файл | Зачем |
|------|--------|
| `scripts/start-radar-full.bat` | какие 3 процесса |
| `scripts/stop-radar.bat` | как убивать |
| `scripts/_radar-env.bat` | venv, cwd |
| `src/radar_status.py` | текст статуса (как в боте) |
| `src/telegram_control.py` | пауза уже в боте — в пульте не дублировать, опционально ссылка |
| `docs/ops/DESKTOP_LAUNCH.md` | обновить после сдачи |

## UI (вариант B — пульт)

**Окно** (tkinter встроенный **или** CustomTkinter — если добавишь в `requirements.txt`, обоснуй в STATUS):

| Элемент | Поведение |
|---------|-----------|
| **▶ Старт** | Сначала стоп (если что-то висит), затем 3 subprocess **без** видимого cmd (`CREATE_NO_WINDOW` / `startupinfo`) |
| **⏹ Стоп** | Та же логика, что `stop-radar.bat` |
| Индикаторы | 3 строки: **Биржи** · **TG** · **Join** — 🟢 процесс жив / 🔴 нет (опрос PID раз в 2–3 с) |
| Лог | Вкладки или split: хвост `data/radar.log` + `data/tg_join.log` (автоскролл, последние ~200 строк, обновление раз в 1–2 с) |
| **Статус** | Кнопка «Обновить» → `format_status_message()` из `radar_status.py` (read-only Text) |
| Подсказка | «Пауза — в Telegram-боте (ℹ Статус)» |

**Процессы при старте (cwd = корень repo, python = `.venv\Scripts\python.exe`):**

1. `src/main.py` — биржи  
2. `scripts/tg_main.py` — TG  
3. `scripts/tg_join_daemon.py` — join  

Заголовки окон subprocess не обязательны; главное — не 3 чёрных cmd.

## Техника

- Точка входа: `scripts/radar_desktop.py` (или `src/radar_desktop.py` — один файл, зафиксируй в STATUS)
- Хранить Popen/PID трёх детей; при закрытии GUI — **стоп** всех (confirm или авто-стоп)
- Один экземпляр приложения (lock-файл `data/.radar_desktop.lock` или аналог)
- Ошибки старта — messagebox с текстом, без traceback в лицо
- Кодировка логов UTF-8

## Приёмка

1. Закрыть все cmd радара → запуск `python scripts/radar_desktop.py` → **Старт** → **нет** 3 окон cmd, в диспетчере 3 python
2. `data/radar.log` — `радар:старт`, `тг:старт`, три `тг:монитор:старт account=…`
3. **Стоп** — процессы исчезают
4. Повторный **Старт** без 409 / без «database is locked»
5. Индикаторы меняются при стоп/старт
6. Кнопка статуса показывает acc1/2/3 (если `.env` с `TELETHON_MONITOR_ACCOUNTS`)

## Docs (минимум)

- `docs/ops/DESKTOP_LAUNCH.md` — главный способ запуска = пульт
- `docs/ops/RUN.md` — ссылка на пульт
- `.env.example` — не нужно

## Отчёт

`docs/team/STATUS.md` — Сделано / Файлы / Как проверить (одна команда запуска).

Lead обновит `FOR_YOU.md` и ROADMAP после ревью.
